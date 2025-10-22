"""
Unit тесты для модуля riddles.

Тестирует функциональность коллекции загадок и анализатора ответов.
"""

import pytest

from src.riddles import RiddleCollection, RiddleAnalyzer, Riddle


class TestRiddleCollection:
    """Тесты для класса RiddleCollection."""
    
    @pytest.fixture
    def collection(self):
        """Фикстура для создания коллекции загадок."""
        return RiddleCollection()
    
    def test_collection_initialization(self, collection):
        """Тест инициализации коллекции."""
        assert collection.riddles is not None
        assert len(collection.riddles) == 5
    
    def test_get_riddles(self, collection):
        """Тест получения всех загадок."""
        riddles = collection.get_riddles()
        assert len(riddles) == 5
        assert all(isinstance(riddle, Riddle) for riddle in riddles)
    
    def test_get_riddle_texts(self, collection):
        """Тест получения текстов загадок."""
        texts = collection.get_riddle_texts()
        assert len(texts) == 5
        assert all(isinstance(text, str) for text in texts)
        assert all(len(text) > 0 for text in texts)
    
    def test_get_riddle_by_difficulty(self, collection):
        """Тест получения загадок по сложности."""
        easy_riddles = collection.get_riddle_by_difficulty(1)
        assert len(easy_riddles) == 1
        assert easy_riddles[0].difficulty == 1
        
        hard_riddles = collection.get_riddle_by_difficulty(5)
        assert len(hard_riddles) == 1
        assert hard_riddles[0].difficulty == 5
    
    def test_riddle_structure(self, collection):
        """Тест структуры загадок."""
        riddles = collection.get_riddles()
        
        for riddle in riddles:
            assert hasattr(riddle, 'title')
            assert hasattr(riddle, 'text')
            assert hasattr(riddle, 'difficulty')
            assert isinstance(riddle.title, str)
            assert isinstance(riddle.text, str)
            assert isinstance(riddle.difficulty, int)
            assert 1 <= riddle.difficulty <= 5


class TestRiddleAnalyzer:
    """Тесты для класса RiddleAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Фикстура для создания анализатора."""
        return RiddleAnalyzer()
    
    def test_analyzer_initialization(self, analyzer):
        """Тест инициализации анализатора."""
        assert analyzer.LOGICAL_KEYWORDS is not None
        assert len(analyzer.LOGICAL_KEYWORDS) > 0
    
    def test_count_words(self, analyzer):
        """Тест подсчета слов."""
        assert analyzer._count_words("") == 0
        assert analyzer._count_words("одно слово") == 2
        assert analyzer._count_words("три слова здесь") == 3
        assert analyzer._count_words("много    пробелов    между    словами") == 4
    
    def test_has_logical_keywords(self, analyzer):
        """Тест проверки наличия логических ключевых слов."""
        assert analyzer._has_logical_keywords("") is False
        assert analyzer._has_logical_keywords("обычный текст") is False
        assert analyzer._has_logical_keywords("если это так") is True
        assert analyzer._has_logical_keywords("значит правильно") is True
        assert analyzer._has_logical_keywords("поэтому вывод") is True
    
    def test_count_logical_keywords(self, analyzer):
        """Тест подсчета логических ключевых слов."""
        assert analyzer._count_logical_keywords("") == 0
        assert analyzer._count_logical_keywords("обычный текст") == 0
        assert analyzer._count_logical_keywords("если это так") == 1
        assert analyzer._count_logical_keywords("если это так, значит правильно") == 2
        assert analyzer._count_logical_keywords("если если если") == 3
    
    def test_has_step_by_step_structure(self, analyzer):
        """Тест проверки пошаговой структуры."""
        assert analyzer._has_step_by_step_structure("") is False
        assert analyzer._has_step_by_step_structure("обычный текст") is False
        assert analyzer._has_step_by_step_structure("1. Первый шаг") is True
        assert analyzer._has_step_by_step_structure("1) Первый шаг") is True
        assert analyzer._has_step_by_step_structure("шаг 1") is True
        assert analyzer._has_step_by_step_structure("этап 1") is True
        assert analyzer._has_step_by_step_structure("сначала это") is True
        assert analyzer._has_step_by_step_structure("затем это") is True
        assert analyzer._has_step_by_step_structure("далее это") is True
        assert analyzer._has_step_by_step_structure("в итоге это") is True
    
    def test_analyze_response(self, analyzer):
        """Тест полного анализа ответа."""
        response = "Сначала рассмотрим условие. Если это так, значит вывод правильный. 1. Первый шаг. 2. Второй шаг."
        
        analysis = analyzer.analyze_response(response)
        
        assert isinstance(analysis, dict)
        assert "word_count" in analysis
        assert "has_logical_keywords" in analysis
        assert "logical_keywords_count" in analysis
        assert "has_step_by_step" in analysis
        assert "response_length" in analysis
        
        assert analysis["word_count"] > 0
        assert analysis["has_logical_keywords"] is True
        assert analysis["logical_keywords_count"] > 0
        assert analysis["has_step_by_step"] is True
        assert analysis["response_length"] > 0
    
    def test_analyze_empty_response(self, analyzer):
        """Тест анализа пустого ответа."""
        analysis = analyzer.analyze_response("")
        
        assert analysis["word_count"] == 0
        assert analysis["has_logical_keywords"] is False
        assert analysis["logical_keywords_count"] == 0
        assert analysis["has_step_by_step"] is False
        assert analysis["response_length"] == 0
