# 🚀 Smart ChadGPT Demo Collection

Коллекция демонстрационных скриптов для умной системы интеграции с ChadGPT.

## 📋 Доступные демо

### 1. ⚡ Quick Demo (`quick_demo.py`)
**Быстрое демо основных возможностей**

```bash
python quick_demo.py
```

**Что показывает:**
- Умные рекомендации моделей для разных задач
- Анализ сложности и типа задач
- Автоматический выбор оптимальной модели
- Демо с реальным API (если доступен ключ)

### 2. 🎮 Interactive Demo (`interactive_demo.py`)
**Интерактивное демо с пользовательским вводом**

```bash
python interactive_demo.py
```

**Возможности:**
- Ввод собственных задач
- Выбор предпочтений (скорость/качество)
- Живая генерация кода
- Анализ задач
- Сохранение результатов

### 3. 🚀 Full Demo (`smart_chadgpt_demo.py`)
**Полноценное демо всех возможностей**

```bash
python smart_chadgpt_demo.py
```

**Включает:**
- Умный выбор модели
- Генерация кода с оптимальными моделями
- Анализ кода с лучшими моделями
- Мульти-агентная оркестрация
- Сравнение производительности

### 4. 🧠 Smart Selection Demo (`demo_smart_selection.py`)
**Демо системы умного выбора модели**

```bash
python demo_smart_selection.py
```

**Фокус на:**
- Анализе различных типов задач
- Сравнении моделей по сложности
- Предпочтениях скорости vs качества
- Подробных рекомендациях

## 🛠️ CLI инструменты

### Управление провайдерами
```bash
# Показать все модели
python manage_providers.py models

# Получить рекомендацию
python manage_providers.py recommend "Create a web API" --prefer-quality

# Показать все рекомендации
python manage_providers.py recommend "Debug this code" --show-all

# Статус провайдеров
python manage_providers.py status

# Тест провайдеров
python manage_providers.py test
```

### Примеры команд
```bash
# Простая задача - выберет gpt-5-mini
python manage_providers.py recommend "Create hello world function"

# Сложная задача - выберет gpt-5
python manage_providers.py recommend "Implement microservices architecture" --prefer-quality

# Анализ кода - выберет claude-4.1-opus
python manage_providers.py recommend "Review code for security issues"

# Быстрая задача - выберет gpt-5-nano
python manage_providers.py recommend "Create simple function" --prefer-speed
```

## 🔧 Настройка

### 1. Установка API ключа
```bash
export CHADGPT_API_KEY="your-chadgpt-api-key"
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Запуск демо
```bash
# Быстрое демо
python quick_demo.py

# Интерактивное демо
python interactive_demo.py

# Полное демо
python smart_chadgpt_demo.py
```

## 📊 Поддерживаемые модели

### GPT модели
- **GPT-5**: Самая мощная (8000 токенов, expert tasks)
- **GPT-5 Mini**: Быстрая и эффективная (4000 токенов, medium tasks)
- **GPT-5 Nano**: Легкая (2000 токенов, simple tasks)

### Claude модели
- **Claude 4.1 Opus**: Лучшая для анализа (6000 токенов, expert tasks)
- **Claude 4.5 Sonnet**: Сбалансированная (5000 токенов, medium tasks)

## 🎯 Примеры использования

### Программное использование
```python
from agents.core.code_generator import CodeGeneratorAgent

# Создание агента
generator = CodeGeneratorAgent(external_provider="chadgpt")

# Получение рекомендации
recommendation = generator.get_smart_model_recommendation(
    "Create a machine learning pipeline",
    prefer_quality=True
)

print(f"Рекомендуется: {recommendation.model}")
print(f"Обоснование: {recommendation.reasoning}")

# Автоматическое переключение
await generator.switch_to_smart_model(
    "Create a machine learning pipeline",
    prefer_quality=True
)

# Генерация кода
request = CodeGenerationRequest(
    task_description="Create a machine learning pipeline",
    language="python"
)

result = await generator.process(request)
print(result.generated_code)
```

### CLI использование
```bash
# Получить рекомендацию для задачи
python manage_providers.py recommend "Create a REST API with authentication"

# С предпочтением качества
python manage_providers.py recommend "Implement complex algorithm" --prefer-quality

# С предпочтением скорости
python manage_providers.py recommend "Create simple function" --prefer-speed

# Показать все рекомендации
python manage_providers.py recommend "Debug this code" --show-all
```

## 📈 Результаты тестирования

### Простые задачи
- **Hello World**: GPT-5 Mini (0.80 confidence) - быстрая генерация
- **Простая функция**: GPT-5 Mini (0.80 confidence) - эффективность

### Сложные задачи
- **Бинарное дерево**: GPT-5 (0.80 confidence) - качество кода
- **ML Pipeline**: GPT-5 (0.80 confidence) - экспертная сложность
- **Микросервисы**: GPT-5 (0.80 confidence) - архитектурная сложность

### Анализ кода
- **Code Review**: Claude 4.1 Opus (0.80 confidence) - лучший анализ
- **Security Review**: Claude 4.1 Opus (0.80 confidence) - экспертиза
- **Performance Analysis**: Claude 4.1 Opus (0.80 confidence) - глубокий анализ

### Тестирование
- **Unit Tests**: GPT-5 Mini (0.50 confidence) - хороший баланс
- **Integration Tests**: GPT-5 (0.50 confidence) - сложность

## 🎉 Преимущества системы

### 1. **Автоматический выбор**
- Система сама анализирует задачу
- Выбирает оптимальную модель
- Не нужно думать о том, какую модель использовать

### 2. **Экономия ресурсов**
- Использование подходящей модели для задачи
- Избежание переплаты за избыточную мощность
- Оптимальное использование токенов

### 3. **Подробная аналитика**
- Обоснование каждого выбора
- Сравнение всех доступных моделей
- Метрики уверенности

### 4. **Гибкость**
- Учет предпочтений пользователя
- Поддержка различных типов задач
- Легкое переключение между моделями

## 🚀 Следующие шаги

1. **Запустите демо**: `python quick_demo.py`
2. **Попробуйте интерактивное**: `python interactive_demo.py`
3. **Изучите CLI**: `python manage_providers.py --help`
4. **Интегрируйте в код**: используйте `switch_to_smart_model()`

## 📚 Дополнительные ресурсы

- **Документация**: `EXTERNAL_API_GUIDE.md`
- **Примеры**: `examples/external_api_example.py`
- **Конфигурация**: `external_api_config.example.json`
- **Тесты**: `tests/test_external_api.py`

---

**ChadGPT работает как единая точка доступа ко всем моделям, а наша система умно выбирает лучшую для каждой конкретной задачи!** 🧠✨
