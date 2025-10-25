"""
Performance baseline tests - не должны деградировать после рефакторинга.
"""

import pytest
import time
from core.token_analyzer import SimpleTokenCounter, LimitProfile
from core.text_compressor import SimpleTextCompressor


# Test data of different sizes
SHORT_TEXT = "This is a short text for testing."
MEDIUM_TEXT = "This is a medium length text that contains multiple sentences and should be used for performance testing of token counting and compression operations." * 10
LONG_TEXT = """
This is a very long text that contains multiple paragraphs and sentences.
It is designed to test the performance of token counting and compression operations
with realistic data sizes that might be encountered in production.
The text includes various types of content including technical terms,
natural language, and mixed content to provide a comprehensive test case.
""" * 100


@pytest.mark.benchmark
class TestPerformanceBaseline:
    """Performance benchmarks - не должны деградировать."""
    
    def test_token_counting_performance_short(self):
        """Benchmark token counting speed for short text."""
        counter = SimpleTokenCounter(limit_profile=LimitProfile.PRACTICAL)
        
        start_time = time.time()
        for _ in range(1000):
            result = counter.count_tokens(SHORT_TEXT, "starcoder")
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 1000
        assert avg_time < 0.001  # Should be < 1ms per operation
        assert result.count > 0
        
    def test_token_counting_performance_medium(self):
        """Benchmark token counting speed for medium text."""
        counter = SimpleTokenCounter(limit_profile=LimitProfile.PRACTICAL)
        
        start_time = time.time()
        for _ in range(100):
            result = counter.count_tokens(MEDIUM_TEXT, "starcoder")
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 100
        assert avg_time < 0.01  # Should be < 10ms per operation
        assert result.count > 0
        
    def test_token_counting_performance_long(self):
        """Benchmark token counting speed for long text."""
        counter = SimpleTokenCounter(limit_profile=LimitProfile.PRACTICAL)
        
        start_time = time.time()
        for _ in range(10):
            result = counter.count_tokens(LONG_TEXT, "starcoder")
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 10
        assert avg_time < 0.1  # Should be < 100ms per operation
        assert result.count > 0
        
    def test_compression_performance_truncation(self):
        """Benchmark compression speed for truncation strategy."""
        counter = SimpleTokenCounter(limit_profile=LimitProfile.PRACTICAL)
        compressor = SimpleTextCompressor(counter)
        
        start_time = time.time()
        for _ in range(10):
            result = compressor.compress_by_truncation(LONG_TEXT, 1000, "starcoder")
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 10
        assert avg_time < 0.1  # Should be < 100ms per operation
        assert result.compression_ratio < 1.0
        
    def test_compression_performance_keywords(self):
        """Benchmark compression speed for keywords strategy."""
        counter = SimpleTokenCounter(limit_profile=LimitProfile.PRACTICAL)
        compressor = SimpleTextCompressor(counter)
        
        start_time = time.time()
        for _ in range(10):
            result = compressor.compress_by_keywords(LONG_TEXT, 1000, "starcoder")
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 10
        assert avg_time < 0.1  # Should be < 100ms per operation
        assert result.compression_ratio < 1.0
        
    def test_limit_check_performance(self):
        """Benchmark limit checking performance."""
        counter = SimpleTokenCounter(limit_profile=LimitProfile.PRACTICAL)
        
        start_time = time.time()
        for _ in range(1000):
            exceeds = counter.check_limit_exceeded(MEDIUM_TEXT, "starcoder")
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 1000
        assert avg_time < 0.001  # Should be < 1ms per operation
        assert isinstance(exceeds, bool)
        
    def test_model_limits_lookup_performance(self):
        """Benchmark model limits lookup performance."""
        counter = SimpleTokenCounter(limit_profile=LimitProfile.PRACTICAL)
        
        start_time = time.time()
        for _ in range(1000):
            limits = counter.get_model_limits("starcoder")
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 1000
        assert avg_time < 0.0001  # Should be < 0.1ms per operation
        assert limits.max_input_tokens == 4096
        
    def test_memory_usage_baseline(self):
        """Test memory usage doesn't grow excessively."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create many objects
        counters = []
        compressors = []
        
        for _ in range(100):
            counter = SimpleTokenCounter(limit_profile=LimitProfile.PRACTICAL)
            compressor = SimpleTextCompressor(counter)
            counters.append(counter)
            compressors.append(compressor)
            
            # Use them
            result = counter.count_tokens(MEDIUM_TEXT, "starcoder")
            compression = compressor.compress_by_truncation(MEDIUM_TEXT, 1000, "starcoder")
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 50MB for 100 objects)
        assert memory_growth < 50 * 1024 * 1024  # 50MB
        
    def test_concurrent_operations_baseline(self):
        """Test concurrent operations don't cause issues."""
        import threading
        import queue
        
        counter = SimpleTokenCounter(limit_profile=LimitProfile.PRACTICAL)
        results = queue.Queue()
        errors = queue.Queue()
        
        def worker():
            try:
                for _ in range(10):
                    result = counter.count_tokens(MEDIUM_TEXT, "starcoder")
                    results.put(result.count)
            except Exception as e:
                errors.put(e)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check no errors occurred
        assert errors.empty(), f"Errors occurred: {list(errors.queue)}"
        
        # Check all results are valid
        result_counts = []
        while not results.empty():
            result_counts.append(results.get())
        
        assert len(result_counts) == 50  # 5 threads * 10 operations
        assert all(count > 0 for count in result_counts)
        assert all(count == result_counts[0] for count in result_counts)  # All should be same
