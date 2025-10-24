# Быстрая справка по AI Агентам

[English](AGENTS_QUICK_REFERENCE.md) | [Русский](AGENTS_QUICK_REFERENCE.ru.md)

## 🎯 Руководство по выбору агента

| Тип задачи | Основной агент | Вторичный агент | Случай использования |
|-----------|---------------|-----------------|---------------------|
| **Документация** | @technical-writer.mdc | @ai-reviewer.mdc | API docs, руководства пользователя, README |
| **Ревью кода** | @ai-reviewer.mdc | @py-reviewer.mdc | Качество, читаемость, оптимизация |
| **Архитектура** | @chief-architect.mdc | @devops-engineer.mdc | Дизайн системы, паттерны, масштабируемость |
| **Безопасность** | @security-reviewer.mdc | @docker-reviewer.mdc | Аудит безопасности, усиление |
| **Тестирование** | @qa-tdd-reviewer.mdc | @py-reviewer.mdc | Стратегия тестирования, TDD, покрытие |
| **Инфраструктура** | @devops-engineer.mdc | @docker-reviewer.mdc | CI/CD, развертывание, мониторинг |
| **Python код** | @py-reviewer.mdc | @python-zen-writer.mdc | Лучшие практики Python, PEP 8 |
| **JavaScript** | @js-reviewer.mdc | @ai-reviewer.mdc | JS/TS паттерны, типы |
| **Shell скрипты** | @sh-reviewer.mdc | @security-reviewer.mdc | Безопасность скриптов, читаемость |
| **Инженерия данных** | @data-engineer.mdc | @ml-engineer.mdc | ETL, схемы, пайплайны |
| **ML/AI** | @ml-engineer.mdc | @data-engineer.mdc | ML пайплайны, модели |
| **Управление проектами** | @tl-vasiliy.mdc | @chief-architect.mdc | Планирование, координация |

## 🚀 Быстрые команды

### Документация
```bash
@technical-writer.mdc Create API documentation for the new endpoint
@technical-writer.mdc Write user guide for authentication system
@technical-writer.mdc Generate changelog for v2.0 release
```

### Качество кода
```bash
@ai-reviewer.mdc Review orchestrator.py for readability improvements
@py-reviewer.mdc Check Python code for PEP 8 compliance
@security-reviewer.mdc Audit authentication module for vulnerabilities
```

### Архитектура и дизайн
```bash
@chief-architect.mdc Design microservices architecture for e-commerce
@devops-engineer.mdc Set up CI/CD pipeline for the application
@docker-reviewer.mdc Optimize Dockerfile for security and size
```

### Тестирование и качество
```bash
@qa-tdd-reviewer.mdc Implement TDD approach for new feature
@qa-tdd-reviewer.mdc Set up comprehensive test strategy
@py-reviewer.mdc Review test coverage and suggest improvements
```

### Безопасность и инфраструктура
```bash
@security-reviewer.mdc Audit Docker configuration for security issues
@docker-reviewer.mdc Implement Docker best practices
@devops-engineer.mdc Design infrastructure for high availability
```

### Python разработка
```bash
@py-reviewer.mdc Review agent implementation for Python best practices
@python-zen-writer.mdc Rewrite code following Zen of Python
@py-reviewer.mdc Analyze project structure for architectural patterns
```

### JavaScript/TypeScript
```bash
@js-reviewer.mdc Review React components for best practices
@js-reviewer.mdc Implement TypeScript for better type safety
@js-reviewer.mdc Design component architecture for frontend
```

### Shell скрипты
```bash
@sh-reviewer.mdc Review deployment script for security and readability
@sh-reviewer.mdc Implement shell script best practices
@sh-reviewer.mdc Harden shell script for security
```

### Инженерия данных
```bash
@data-engineer.mdc Design ETL pipeline for processing user data
@data-engineer.mdc Design data schema for analytics system
@data-engineer.mdc Set up data quality monitoring and alerting
```

### Машинное обучение
```bash
@ml-engineer.mdc Design ML pipeline for recommendation system
@ml-engineer.mdc Implement machine learning model for classification
@ml-engineer.mdc Set up MLOps pipeline for model deployment
```

### Управление проектами
```bash
@tl-vasiliy.mdc Plan development timeline for new feature
@tl-vasiliy.mdc Coordinate team for sprint planning
@tl-vasiliy.mdc Assess risks for upcoming release
```

## 🔧 Комбинирование агентов

### Комплексный ревью
```bash
@ai-reviewer.mdc @security-reviewer.mdc @py-reviewer.mdc Review authentication module
@chief-architect.mdc @devops-engineer.mdc @security-reviewer.mdc Design system architecture
```

### Полный анализ стека
```bash
@technical-writer.mdc @ai-reviewer.mdc @py-reviewer.mdc Document and review new feature
@qa-tdd-reviewer.mdc @py-reviewer.mdc @security-reviewer.mdc Implement testing strategy
```

### DevOps и безопасность
```bash
@devops-engineer.mdc @docker-reviewer.mdc @security-reviewer.mdc Set up production deployment
@docker-reviewer.mdc @security-reviewer.mdc @devops-engineer.mdc Optimize container security
```

## 📋 Шаблоны запросов

### Документация
```bash
@technical-writer.mdc Create comprehensive [TYPE] documentation for [COMPONENT]
@technical-writer.mdc Write [AUDIENCE] guide for [SYSTEM]
@technical-writer.mdc Generate [DOCUMENT_TYPE] for [PROJECT]
```

### Ревью кода
```bash
@ai-reviewer.mdc Review [FILE] for [ASPECT] improvements
@py-reviewer.mdc Check [COMPONENT] for Python best practices
@security-reviewer.mdc Audit [MODULE] for security vulnerabilities
```

### Архитектура
```bash
@chief-architect.mdc Design [ARCHITECTURE_TYPE] for [PROJECT]
@devops-engineer.mdc Set up [INFRASTRUCTURE_COMPONENT] for [ENVIRONMENT]
@docker-reviewer.mdc Optimize [CONTAINER_COMPONENT] for [REQUIREMENT]
```

### Тестирование
```bash
@qa-tdd-reviewer.mdc Implement [TESTING_APPROACH] for [FEATURE]
@qa-tdd-reviewer.mdc Set up [TESTING_TYPE] strategy for [COMPONENT]
@py-reviewer.mdc Review test coverage for [MODULE]
```

## 🎯 Контекстные команды

### С контекстом проекта
```bash
@technical-writer.mdc @context.md Create API documentation for StarCoder Multi-Agent System
@ai-reviewer.mdc @context.md Review orchestrator.py for performance optimization
@chief-architect.mdc @context.md Design microservices architecture for day_07
```

### С конкретными требованиями
```bash
@technical-writer.mdc Create user guide for authentication system targeting developers
@ai-reviewer.mdc Optimize this function for better LLM understanding and token efficiency
@security-reviewer.mdc Audit Docker configuration for production security requirements
```

### С примерами
```bash
@technical-writer.mdc Create API documentation similar to FastAPI docs for our endpoints
@ai-reviewer.mdc Refactor this code following the patterns in orchestrator.py
@py-reviewer.mdc Review this module for PEP 8 compliance like the base_agent.py
```

## 🚨 Экстренные команды

### Критические проблемы
```bash
@security-reviewer.mdc URGENT: Audit production deployment for security vulnerabilities
@devops-engineer.mdc CRITICAL: Fix deployment pipeline failure
@docker-reviewer.mdc EMERGENCY: Optimize container for memory issues
```

### Быстрые исправления
```bash
@ai-reviewer.mdc QUICK: Fix linting errors in [FILE]
@py-reviewer.mdc FAST: Resolve import issues in [MODULE]
@sh-reviewer.mdc IMMEDIATE: Fix shell script security issues
```

## 📊 Метрики и мониторинг

### Качество кода
```bash
@ai-reviewer.mdc Analyze code complexity metrics for [PROJECT]
@py-reviewer.mdc Review test coverage and suggest improvements
@qa-tdd-reviewer.mdc Set up quality metrics and monitoring
```

### Производительность
```bash
@ai-reviewer.mdc Optimize code for better performance
@devops-engineer.mdc Monitor application performance metrics
@docker-reviewer.mdc Optimize container resource usage
```

### Безопасность
```bash
@security-reviewer.mdc Scan for security vulnerabilities
@docker-reviewer.mdc Audit container security configuration
@security-reviewer.mdc Review IAM policies and permissions
```

## 🔄 Итеративные команды

### Поэтапная разработка
```bash
@chief-architect.mdc Design high-level architecture for [PROJECT]
@technical-writer.mdc Create initial documentation for [COMPONENT]
@ai-reviewer.mdc Review implementation for [ASPECT]
@qa-tdd-reviewer.mdc Set up testing strategy for [FEATURE]
```

### Рефакторинг
```bash
@ai-reviewer.mdc Analyze current code structure
@py-reviewer.mdc Suggest refactoring improvements
@ai-reviewer.mdc Implement refactoring changes
@qa-tdd-reviewer.mdc Update tests for refactored code
```

## 💡 Советы по эффективности

### 1. Будьте конкретными
- Указывайте конкретные файлы, модули или компоненты
- Предоставляйте контекст и ограничения
- Задавайте конкретные вопросы

### 2. Используйте контекст
- Применяйте `@context.md` для информации о проекте
- Ссылайтесь на существующие примеры
- Указывайте целевую аудиторию

### 3. Комбинируйте агентов
- Используйте несколько агентов для разных аспектов
- Получайте комплексное покрытие
- Используйте дополнительные навыки

### 4. Итеративный подход
- Начните с высокоуровневого дизайна
- Уточняйте на основе обратной связи
- Реализуйте инкрементально

### 5. Документируйте решения
- Записывайте архитектурные решения
- Объясняйте компромиссы
- Ведите журнал решений

## 🆘 Получение помощи

### Частые проблемы
1. **Агент не отвечает соответствующим образом** → Предоставьте более конкретный контекст
2. **Конфликтующие рекомендации** → Приоритизируйте на основе целей проекта
3. **Отсутствующая экспертиза** → Комбинируйте несколько агентов

### Ресурсы
- **Документация агентов**: `AGENTS.md` / `AGENTS.ru.md`
- **Примеры**: `.cursor/examples.md`
- **Контекст проекта**: `@context.md`
- **Правила**: `.cursor/rules.md`

### Контакты
- **Техническая поддержка**: Используйте соответствующих агентов
- **Вопросы по архитектуре**: @chief-architect.mdc
- **Проблемы с безопасностью**: @security-reviewer.mdc
- **Управление проектами**: @tl-vasiliy.mdc
