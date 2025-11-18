# Persona Template Configuration Guide

**Epic**: EP25 - Personalised Butler
**Purpose**: Edit Alfred-style дворецкий persona prompt without code changes

---

## Overview

Persona templates are now stored in **`config/persona_templates.yaml`** instead of hardcoded in Python. This allows easy editing without modifying code.

---

## File Location

**Template File**: `config/persona_templates.yaml`

This file contains all prompt templates for personalization:
- `persona_template` - Main Alfred-style дворецкий persona instructions
- `memory_context_template` - Memory context formatting
- `full_prompt_template` - Complete prompt assembly
- `summary_section_template` - Summary section formatting
- `events_section_template` - Events section formatting

---

## Editing Persona Template

### Current Template

The default template creates an "Alfred-style дворецкий" persona:

```yaml
persona_template: |
  Ты — {persona}. Твой тон: {tone}. Язык ответа: {language}.

  Instructions:
  - Отвечай как Alfred из Batman (вежливый, ироничный, заботливый).
  - Используй английский юмор, но говори на русском языке.
  - Будь полезным и информативным, но добавляй лёгкую иронию где уместно.
  - Preferred topics: {preferred_topics}.
  - Обращайся к пользователю на "вы" или "сэр" для поддержания стиля Alfred.

  Примеры стиля:
  - "Добрый день, сэр. Надеюсь, день проходит без излишней драмы?"
  - "Ах, вечный вопрос. Позвольте проверить свои архивы..."
  - "Конечно, сэр. Хотя я бы рекомендовал немного больше внимания к деталям в будущем."
```

### How to Edit

1. **Open the file**:
   ```bash
   nano config/persona_templates.yaml
   # or
   vim config/persona_templates.yaml
   ```

2. **Edit the template**:
   - Modify `persona_template` section
   - Keep placeholders: `{persona}`, `{tone}`, `{language}`, `{preferred_topics}`
   - Use YAML multiline string syntax (`|`)

3. **Restart Butler bot**:
   ```bash
   make butler-restart
   ```

4. **Test**:
   - Send a message to Butler bot
   - Check if new persona style is applied

---

## Template Variables

Available placeholders in templates:

| Variable | Description | Example |
|----------|-------------|---------|
| `{persona}` | Persona name | "Alfred-style дворецкий" |
| `{tone}` | Conversation tone | "witty" |
| `{language}` | Response language | "ru" |
| `{preferred_topics}` | User's preferred topics | "Python, AI, coding" |
| `{summary_section}` | Memory summary (if exists) | "User likes Python..." |
| `{events_section}` | Recent conversation events | "- User: Hello\n- Butler: Good day..." |
| `{persona_section}` | Formatted persona instructions | Full persona prompt |
| `{memory_context}` | Formatted memory context | Summary + events |
| `{new_message}` | Current user message | "Привет!" |

---

## Example: Custom Persona

To create a different persona style:

```yaml
persona_template: |
  Ты — {persona}. Твой тон: {tone}. Язык ответа: {language}.

  Instructions:
  - Отвечай как дружелюбный помощник.
  - Будь вежливым и профессиональным.
  - Preferred topics: {preferred_topics}.
  - Используй простой и понятный язык.

  Примеры стиля:
  - "Здравствуйте! Чем могу помочь?"
  - "Конечно, давайте разберемся..."
```

---

## Reloading Templates

### Automatic Reload

Templates are **cached in memory** after first load. To reload:

1. **Restart Butler bot**:
   ```bash
   make butler-restart
   ```

2. **Or restart specific service**:
   ```bash
   docker-compose -f docker-compose.butler.yml restart butler-bot
   ```

### Development Mode

For development with hot-reload, you can:
- Mount `config/` directory as volume in docker-compose
- Use file watcher to detect changes
- Implement template reload endpoint (future enhancement)

---

## Fallback Behavior

If `config/persona_templates.yaml` is missing:
- System uses **default templates** from code
- No errors, graceful fallback
- Logs warning about missing file

---

## File Structure

```
config/
└── persona_templates.yaml    # Edit this file to customize persona
```

**Note**: File is loaded at module import time and cached. Restart required for changes.

---

## Validation

After editing, validate YAML syntax:

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('config/persona_templates.yaml'))"
```

---

## Best Practices

1. **Backup before editing**: Copy original template
2. **Test changes**: Restart bot and test with real messages
3. **Keep placeholders**: Don't remove `{persona}`, `{tone}`, etc.
4. **Use YAML multiline**: Use `|` for multi-line strings
5. **Version control**: Commit template changes to git

---

## Troubleshooting

### Template not loading

```bash
# Check file exists
ls -la config/persona_templates.yaml

# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('config/persona_templates.yaml'))"
```

### Changes not applied

- Restart Butler bot after editing
- Check logs for template loading errors
- Verify YAML syntax is correct

---

**Status**: ✅ Implemented
**File**: `config/persona_templates.yaml`
**Reload**: Restart Butler bot after editing
