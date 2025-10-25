"""
План рефакторинга по Дзену Python для системы анализа токенов.

Принципы Дзена Python, которые нужно применить:
1. Beautiful is better than ugly
2. Explicit is better than implicit  
3. Simple is better than complex
4. Complex is better than complicated
5. Flat is better than nested
6. Sparse is better than dense
7. Readability counts
8. Special cases aren't special enough to break the rules
9. Although practicality beats purity
10. Errors should never pass silently
11. In the face of ambiguity, refuse the temptation to guess
12. There should be one obvious way to do it
13. Although that way may not be obvious at first unless you're Dutch
14. Now is better than never
15. Although never is often better than right now
16. If the implementation is hard to explain, it's a bad idea
17. If the implementation is easy to explain, it's a good idea
18. Namespaces are one honking great idea -- let's do more of those!
"""

# TODO: Рефакторинг по принципам Дзена Python

# 1. "Beautiful is better than ugly" - Улучшить структуру данных
TODO_BEAUTIFUL = [
    "Упростить MODEL_LIMITS структуру - убрать глубокую вложенность",
    "Создать более элегантные dataclass с валидацией",
    "Улучшить именование переменных и методов",
    "Добавить type hints везде где возможно"
]

# 2. "Explicit is better than implicit" - Сделать код более явным
TODO_EXPLICIT = [
    "Добавить явные проверки типов в runtime",
    "Создать явные константы вместо магических чисел",
    "Добавить явную обработку ошибок везде",
    "Сделать зависимости явными через dependency injection"
]

# 3. "Simple is better than complex" - Упростить сложные классы
TODO_SIMPLE = [
    "Разбить TokenLimitExperiments на более мелкие классы",
    "Упростить HybridTokenCounter логику",
    "Создать простые функции вместо сложных методов",
    "Убрать избыточную абстракцию"
]

# 4. "Flat is better than nested" - Убрать глубокую вложенность
TODO_FLAT = [
    "Переписать MODEL_LIMITS как плоскую структуру",
    "Убрать глубокую вложенность в экспериментах",
    "Создать плоскую структуру конфигурации",
    "Упростить иерархию классов"
]

# 5. "Readability counts" - Улучшить читаемость
TODO_READABLE = [
    "Добавить больше docstring с примерами",
    "Улучшить именование методов и переменных",
    "Создать более понятные сообщения об ошибках",
    "Добавить комментарии к сложной логике"
]

# 6. "Errors should never pass silently" - Улучшить обработку ошибок
TODO_ERRORS = [
    "Добавить явную обработку всех исключений",
    "Создать кастомные исключения для домена",
    "Логировать все ошибки с контекстом",
    "Не использовать bare except"
]

# 7. "There should be one obvious way to do it" - Унифицировать подходы
TODO_OBVIOUS = [
    "Создать единый интерфейс для всех счетчиков токенов",
    "Унифицировать обработку экспериментов",
    "Стандартизировать формат ответов",
    "Создать единый стиль обработки ошибок"
]

# 8. "If the implementation is hard to explain, it's a bad idea" - Упростить сложную логику
TODO_EXPLAINABLE = [
    "Упростить логику выбора стратегии сжатия",
    "Создать более понятную логику fallback",
    "Упростить Docker управление",
    "Сделать ML клиент более понятным"
]

# Приоритетные задачи для немедленного исправления:
PRIORITY_FIXES = [
    "Упростить MODEL_LIMITS структуру",
    "Разбить TokenLimitExperiments на более мелкие классы", 
    "Добавить явную обработку ошибок",
    "Улучшить именование и документацию",
    "Создать плоскую структуру конфигурации"
]
