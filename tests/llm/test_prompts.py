from src.infrastructure.llm.prompts import get_map_prompt, get_reduce_prompt


def test_map_prompt_ru_contains_controls():
    p = get_map_prompt("текст", "ru", max_sentences=3)
    assert "ЗАДАЧА" in p and "КЛЮЧЕВЫЕ ФАКТЫ" in p
    assert "3" in p


def test_reduce_prompt_en_contains_controls():
    s = get_reduce_prompt("s1\n\ns2", "en", max_sentences=7)
    assert "Combine" in s and "FINAL SUMMARY" in s
    assert "7" in s


