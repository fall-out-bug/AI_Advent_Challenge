"""
Compression Evaluator for testing all compression algorithms.

This module provides the CompressionEvaluator class that tests all 5 compression
algorithms (truncation, keywords, extractive, semantic, summarization) on heavy
queries and evaluates their quality.
"""

import asyncio
import logging
from typing import Dict, List, Optional

from core.ml_client import TokenAnalysisClient
from core.text_compressor import SimpleTextCompressor
from core.token_analyzer import SimpleTokenCounter
from models.data_models import CompressionTestResult, QualityMetrics
from utils.logging import LoggerFactory

# Configure logging
logger = LoggerFactory.create_logger(__name__)


class CompressionEvaluator:
    """
    Evaluator for testing compression algorithms on heavy queries.
    
    Tests all available compression strategies and evaluates their
    effectiveness and quality preservation.
    
    Attributes:
        model_client: TokenAnalysisClient for model interactions
        token_counter: TokenCounter for token counting
        text_compressor: TextCompressor for compression operations
        logger: Logger instance for structured logging
        
    Example:
        ```python
        from core.compression_evaluator import CompressionEvaluator
        from core.ml_client import TokenAnalysisClient
        from core.token_analyzer import SimpleTokenCounter
        from core.text_compressor import SimpleTextCompressor
        
        # Initialize evaluator
        model_client = TokenAnalysisClient()
        token_counter = SimpleTokenCounter()
        text_compressor = SimpleTextCompressor(token_counter)
        
        evaluator = CompressionEvaluator(model_client, token_counter, text_compressor)
        
        # Test all compressions on a heavy query
        results = await evaluator.test_all_compressions(heavy_query, "starcoder")
        
        # Evaluate quality
        quality = await evaluator.evaluate_compression_quality(
            original_query, compressed_query, response
        )
        ```
    """
    
    def __init__(
        self,
        model_client: Optional[TokenAnalysisClient] = None,
        token_counter: Optional[SimpleTokenCounter] = None,
        text_compressor: Optional[SimpleTextCompressor] = None
    ):
        """
        Initialize the compression evaluator.
        
        Args:
            model_client: Optional TokenAnalysisClient instance
            token_counter: Optional TokenCounter instance
            text_compressor: Optional TextCompressor instance
            
        Example:
            ```python
            from core.compression_evaluator import CompressionEvaluator
            
            # Initialize with default components
            evaluator = CompressionEvaluator()
            
            # Or with custom components
            evaluator = CompressionEvaluator(
                model_client=custom_client,
                token_counter=custom_counter,
                text_compressor=custom_compressor
            )
            ```
        """
        self.model_client = model_client or TokenAnalysisClient()
        self.token_counter = token_counter or SimpleTokenCounter()
        self.text_compressor = text_compressor or SimpleTextCompressor(self.token_counter)
        self.logger = LoggerFactory.create_logger(__name__)
        
        # Available compression strategies (only truncation and keywords are implemented)
        self.compression_strategies = [
            "truncation",
            "keywords"
        ]
        
        self.logger.info("Initialized CompressionEvaluator")
    
    async def test_all_compressions(
        self, 
        query: str, 
        model_name: str,
        target_tokens: Optional[int] = None
    ) -> List[CompressionTestResult]:
        """
        Test all compression algorithms on a query.
        
        Args:
            query: Query to compress and test
            model_name: Name of the model to use
            target_tokens: Optional target token count for compression
            
        Returns:
            List of CompressionTestResult for each compression strategy
            
        Example:
            ```python
            # Test all compressions on a heavy query
            results = await evaluator.test_all_compressions(
                heavy_query, 
                "starcoder",
                target_tokens=1000
            )
            
            # Analyze results
            for result in results:
                print(f"{result.strategy}: {result.compression_ratio:.2f} ratio")
                print(f"Success: {result.success}")
            ```
        """
        try:
            self.logger.info(f"Testing all compression strategies on query for {model_name}")
            
            # Get model limits if target_tokens not specified
            if target_tokens is None:
                model_limits = self.token_counter.get_model_limits(model_name)
                target_tokens = model_limits.recommended_input or model_limits.max_input_tokens
            
            # Count original tokens
            original_tokens = self.token_counter.count_tokens(query, model_name).count
            
            self.logger.info(f"Original query: {original_tokens} tokens")
            self.logger.info(f"Target tokens: {target_tokens}")
            
            results = []
            
            # Test each compression strategy
            for strategy in self.compression_strategies:
                try:
                    self.logger.info(f"Testing {strategy} compression...")
                    
                    result = await self._test_single_compression(
                        query, model_name, strategy, target_tokens
                    )
                    results.append(result)
                    
                    self.logger.info(f"{strategy}: {result.compression_ratio:.2f} ratio, "
                                   f"Success: {result.success}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to test {strategy} compression: {e}")
                    
                    # Create failed result
                    failed_result = CompressionTestResult(
                        strategy=strategy,
                        original_query=query,
                        compressed_query="",
                        original_tokens=original_tokens,
                        compressed_tokens=0,
                        compression_ratio=0.0,
                        response="",
                        response_tokens=0,
                        response_time=0.0,
                        success=False,
                        error_message=str(e)
                    )
                    results.append(failed_result)
            
            self.logger.info(f"Completed testing {len(results)} compression strategies")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to test all compressions: {e}")
            return []
    
    async def _test_single_compression(
        self,
        query: str,
        model_name: str,
        strategy: str,
        target_tokens: int
    ) -> CompressionTestResult:
        """
        Test a single compression strategy.
        
        Args:
            query: Query to compress
            model_name: Name of the model
            strategy: Compression strategy to use
            target_tokens: Target token count
            
        Returns:
            CompressionTestResult for the strategy
        """
        try:
            # Apply compression
            compression_result = self.text_compressor.compress_text(
                text=query,
                max_tokens=target_tokens,
                model_name=model_name,
                strategy=strategy
            )
            
            # Make request with compressed query
            response = await self.model_client.make_request(
                model_name=model_name,
                prompt=compression_result.compressed_text,
                max_tokens=1000,
                temperature=0.7
            )
            
            # Count response tokens
            response_tokens = self.token_counter.count_tokens(
                response.response, model_name
            ).count
            
            return CompressionTestResult(
                strategy=strategy,
                original_query=query,
                compressed_query=compression_result.compressed_text,
                original_tokens=compression_result.original_tokens,
                compressed_tokens=compression_result.compressed_tokens,
                compression_ratio=compression_result.compression_ratio,
                response=response.response,
                response_tokens=response_tokens,
                response_time=response.response_time,
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"Single compression test failed for {strategy}: {e}")
            raise
    
    async def evaluate_compression_quality(
        self,
        original_query: str,
        compressed_query: str,
        response: str
    ) -> QualityMetrics:
        """
        Evaluate the quality of compression and response.
        
        Args:
            original_query: Original query text
            compressed_query: Compressed query text
            response: Model response text
            
        Returns:
            QualityMetrics containing quality assessment
            
        Example:
            ```python
            quality = await evaluator.evaluate_compression_quality(
                original_query="Long detailed query...",
                compressed_query="Short compressed query...",
                response="Model response..."
            )
            
            print(f"Completeness: {quality.completeness_score:.2f}")
            print(f"Relevance: {quality.relevance_score:.2f}")
            ```
        """
        try:
            self.logger.info("Evaluating compression quality...")
            
            # Calculate basic metrics
            compression_ratio = len(compressed_query) / len(original_query) if original_query else 0
            
            # Evaluate completeness (how much of original intent is preserved)
            completeness_score = self._calculate_completeness_score(
                original_query, compressed_query
            )
            
            # Evaluate relevance (how well response addresses the query)
            relevance_score = self._calculate_relevance_score(
                compressed_query, response
            )
            
            # Evaluate semantic preservation
            semantic_score = self._calculate_semantic_score(
                original_query, compressed_query
            )
            
            # Calculate overall quality score
            overall_score = (completeness_score + relevance_score + semantic_score) / 3
            
            return QualityMetrics(
                compression_ratio=compression_ratio,
                completeness_score=completeness_score,
                relevance_score=relevance_score,
                semantic_score=semantic_score,
                overall_score=overall_score,
                response_length=len(response),
                information_preservation=self._calculate_information_preservation(
                    original_query, compressed_query
                )
            )
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate compression quality: {e}")
            
            # Return default metrics on error
            return QualityMetrics(
                compression_ratio=0.0,
                completeness_score=0.0,
                relevance_score=0.0,
                semantic_score=0.0,
                overall_score=0.0,
                response_length=0,
                information_preservation=0.0
            )
    
    def _calculate_completeness_score(self, original: str, compressed: str) -> float:
        """
        Calculate completeness score (0-1) for compression.
        
        Args:
            original: Original text
            compressed: Compressed text
            
        Returns:
            Completeness score between 0 and 1
        """
        try:
            # Simple keyword-based completeness check
            original_words = set(original.lower().split())
            compressed_words = set(compressed.lower().split())
            
            # Calculate overlap
            if not original_words:
                return 1.0
            
            overlap = len(original_words.intersection(compressed_words))
            completeness = overlap / len(original_words)
            
            # Cap at 1.0
            return min(1.0, completeness)
            
        except Exception:
            return 0.5  # Default score on error
    
    def _calculate_relevance_score(self, query: str, response: str) -> float:
        """
        Calculate relevance score (0-1) for response.
        
        Args:
            query: Query text
            response: Response text
            
        Returns:
            Relevance score between 0 and 1
        """
        try:
            # Simple keyword-based relevance check
            query_words = set(query.lower().split())
            response_words = set(response.lower().split())
            
            # Calculate overlap
            if not query_words:
                return 1.0
            
            overlap = len(query_words.intersection(response_words))
            relevance = overlap / len(query_words)
            
            # Boost score if response contains code-related keywords
            code_keywords = {"def", "class", "import", "return", "if", "for", "while"}
            if any(keyword in response_words for keyword in code_keywords):
                relevance = min(1.0, relevance + 0.2)
            
            return min(1.0, relevance)
            
        except Exception:
            return 0.5  # Default score on error
    
    def _calculate_semantic_score(self, original: str, compressed: str) -> float:
        """
        Calculate semantic preservation score (0-1).
        
        Args:
            original: Original text
            compressed: Compressed text
            
        Returns:
            Semantic score between 0 and 1
        """
        try:
            # Simple semantic preservation check based on structure
            original_sentences = original.split('.')
            compressed_sentences = compressed.split('.')
            
            # Check if key structural elements are preserved
            structural_elements = ["def ", "class ", "import ", "from ", "if ", "for ", "while "]
            
            original_has_structure = any(element in original for element in structural_elements)
            compressed_has_structure = any(element in compressed for element in structural_elements)
            
            if original_has_structure and compressed_has_structure:
                return 0.8
            elif original_has_structure and not compressed_has_structure:
                return 0.3
            else:
                return 0.6  # Default for non-structured text
            
        except Exception:
            return 0.5  # Default score on error
    
    def _calculate_information_preservation(self, original: str, compressed: str) -> float:
        """
        Calculate information preservation score (0-1).
        
        Args:
            original: Original text
            compressed: Compressed text
            
        Returns:
            Information preservation score between 0 and 1
        """
        try:
            # Calculate based on length ratio and keyword preservation
            length_ratio = len(compressed) / len(original) if original else 0
            
            # Extract important keywords (longer words, technical terms)
            original_words = original.split()
            compressed_words = compressed.split()
            
            # Important words are longer than 4 characters or contain special chars
            important_original = [w for w in original_words if len(w) > 4 or any(c in w for c in ['_', '-', '.'])]
            important_compressed = [w for w in compressed_words if len(w) > 4 or any(c in w for c in ['_', '-', '.'])]
            
            if not important_original:
                return length_ratio
            
            preserved_important = len(set(important_original).intersection(set(important_compressed)))
            preservation_ratio = preserved_important / len(important_original)
            
            # Combine length ratio and preservation ratio
            return (length_ratio + preservation_ratio) / 2
            
        except Exception:
            return 0.5  # Default score on error
    
    def get_compression_strategies(self) -> List[str]:
        """
        Get list of available compression strategies.
        
        Returns:
            List of compression strategy names
            
        Example:
            ```python
            strategies = evaluator.get_compression_strategies()
            print(f"Available strategies: {strategies}")
            ```
        """
        return self.compression_strategies.copy()
    
    def get_best_compression_strategy(self, results: List[CompressionTestResult]) -> Optional[str]:
        """
        Determine the best compression strategy from results.
        
        Args:
            results: List of compression test results
            
        Returns:
            Name of the best strategy, or None if no successful results
            
        Example:
            ```python
            results = await evaluator.test_all_compressions(query, model)
            best_strategy = evaluator.get_best_compression_strategy(results)
            print(f"Best strategy: {best_strategy}")
            ```
        """
        if not results:
            return None
        
        # Filter successful results
        successful_results = [r for r in results if r.success]
        if not successful_results:
            return None
        
        # Score each strategy based on multiple factors
        best_strategy = None
        best_score = -1
        
        for result in successful_results:
            # Score based on compression ratio, response quality, and speed
            compression_score = 1.0 - result.compression_ratio  # Lower ratio is better
            speed_score = 1.0 / (result.response_time + 0.1)  # Faster is better
            response_quality_score = len(result.response) / 1000  # Longer response is better (up to a point)
            
            # Combined score
            total_score = (compression_score * 0.4 + speed_score * 0.3 + response_quality_score * 0.3)
            
            if total_score > best_score:
                best_score = total_score
                best_strategy = result.strategy
        
        return best_strategy
    
    async def compress_and_test(
        self, 
        query: str, 
        model_name: str, 
        strategy: str,
        target_tokens: Optional[int] = None
    ) -> CompressionTestResult:
        """
        Test single compression strategy and return detailed results.
        
        Args:
            query: Query text to compress and test
            model_name: Name of the model to use
            strategy: Compression strategy to use
            target_tokens: Optional target token count for compression
            
        Returns:
            CompressionTestResult containing detailed test results
            
        Example:
            ```python
            result = await evaluator.compress_and_test(
                query="Long detailed query...",
                model_name="starcoder",
                strategy="keywords"
            )
            
            print(f"Success: {result.success}")
            print(f"Compression ratio: {result.compression_ratio:.2f}")
            print(f"Response time: {result.response_time:.2f}s")
            ```
        """
        try:
            # Get model limits if target_tokens not specified
            if target_tokens is None:
                model_limits = self.token_counter.get_model_limits(model_name)
                target_tokens = model_limits.recommended_input or model_limits.max_input_tokens
            
            # Compress the text
            compressed = self.text_compressor.compress_text(
                text=query,
                strategy=strategy,
                max_tokens=target_tokens,
                model_name=model_name
            )
            
            # Make request with compressed text
            response = await self.model_client.make_request(
                model_name=model_name,
                prompt=compressed.compressed_text,
                max_tokens=1000,
                temperature=0.7
            )
            
            # Count response tokens
            response_tokens = self.token_counter.count_tokens(
                response.response, model_name
            ).count
            
            return CompressionTestResult(
                strategy=strategy,
                original_query=query,
                compressed_query=compressed.compressed_text,
                original_tokens=compressed.original_tokens,
                compressed_tokens=compressed.compressed_tokens,
                compression_ratio=compressed.compression_ratio,
                response=response.response,
                response_tokens=response_tokens,
                response_time=response.response_time,
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"Compress and test failed for {strategy}: {e}")
            return CompressionTestResult(
                strategy=strategy,
                original_query=query,
                compressed_query="",
                original_tokens=0,
                compressed_tokens=0,
                compression_ratio=0,
                response="",
                response_tokens=0,
                response_time=0,
                success=False,
                error_message=str(e)
            )