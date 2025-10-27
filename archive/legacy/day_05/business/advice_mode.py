"""
Advice mode for structured dialogue.

Following Python Zen: "Simple is better than complex"
and "Explicit is better than implicit".
"""

from typing import Optional


class AdviceModeV5:
    """Handles structured advice dialogue with the AI."""
    
    def __init__(self):
        """Initialize advice mode."""
        self.is_active = True
        self.question_count = 0
        self.max_questions = 5
    
    def get_system_prompt(self) -> str:
        """Get system prompt for advice mode."""
        return """Ты мудрый дедушка, который дает советы. 
        Задавай уточняющие вопросы (до 5), чтобы лучше понять ситуацию.
        В конце дай конкретный совет с заботой и мудростью.
        ОСТАНОВИСЬ после совета - не задавай больше вопросов."""
    
    def can_ask_more(self) -> bool:
        """Check if can ask more questions."""
        return self.question_count < self.max_questions
    
    def increment_question_count(self) -> None:
        """Increment question counter."""
        self.question_count += 1
