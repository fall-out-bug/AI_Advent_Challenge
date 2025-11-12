# Model Recommendations for Agent Roles
> Style: EN only, concise. Use this quick guide; treat the rest as appendix if present.

## Summary (1‑screen)
- Primary (cloud): Sonnet 4.5, GPT‑5; Alt: GPT‑5 Codex High; Avoid draft/experimental for prod.
- Use cloud for architecture, security, final reviews; use local for drafts and batch tasks.
- Cost control: prefer local for formatting, boilerplate tests, refactors; cloud for critical decisions.
- Decision records: any model choice impacting delivery must be logged as MADR.

**Cloud Models in Cursor (2025)**

> **Актуальные модели:** **Sonnet 4.5**, **GPT‑5**, **GPT‑5 Codex High**, **Haiku 4.5**, **Composer‑1** (экспериментальная), **Grok Code** (экспериментальная).

> **💡 Hybrid Strategy 2025:** Для максимальной эффективности рассмотрите использование локальных моделей для рутинных задач. См. [LOCAL_MODELS.md](LOCAL_MODELS.md) для детального гайда по гибридному подходу (экономия до 78% на API costs).

---

## ⚡ Quick Decision Guide

**Используйте Cloud (Sonnet 4.5, GPT-5), когда:**
- ✅ Критические архитектурные решения
- ✅ Security analysis и vulnerability assessment
- ✅ Final production review перед deployment
- ✅ Сложный business context и stakeholder communication
- ✅ Нужна максимальная надежность и качество

**Используйте Local Models ([см. LOCAL_MODELS.md](LOCAL_MODELS.md)), когда:**
- ✅ Рутинные задачи (formatting, linting, tests)
- ✅ First drafts (код, документация, планирование)
- ✅ Batch processing множества похожих задач
- ✅ Privacy-sensitive код (не хотите отправлять в облако)
- ✅ Нужна высокая скорость без задержек API

---

## 📊 Маппинг моделей по ролям

| Role        | Primary                     | Alternative             | Use with Caution                      |
|-------------|-----------------------------|-------------------------|---------------------------------------|
| Developer   | Sonnet 4.5                  | GPT‑5 Codex High        | Composer‑1, Grok Code *(draft only)*  |
| Tech Lead   | Sonnet 4.5                  | GPT‑5                   | Haiku 4.5 *(короткие заметки)*        |
| Architect   | Sonnet 4.5                  | GPT‑5                   | Composer‑1, Grok Code                 |
| Analyst     | GPT‑5                       | Haiku 4.5               | Composer‑1 *(first draft)*            |

---

## 🤖 Характеристики модели

### Sonnet 4.5 (Claude 3.5 Sonnet)
- Лучший выбор для сложной разработки, архитектуры, техлид-задач.
- Глубокое понимание паттернов, безопасность, тесты.
- Использовать для: масштабных рефакторингов, системного дизайна, risk review.

### GPT‑5
- Сильна в аналитике, документации, планировании.
- Хорошее объяснение решений и структурирование текстов.
- Использовать для: требований, спецификаций, ретроспектив, отчётов.

### GPT‑5 Codex High
- Кодовая версия GPT‑5, оптимальна для шаблонов и быстрых фиксов.
- Отлично удерживает паттерны проекта.
- Использовать для: boilerplate, генерации тестов, небольших изменений.

### Haiku 4.5 (Claude 3.5 Haiku)
- Быстрая и экономичная, но с ограниченным reasoning.
- Подходит для коротких апдейтов, черновых заметок, чеклистов.

### Composer‑1 *(experimental)*
- Модель нестабильного качества; использовать только для rough draft, который в любом случае переписывается.
- Избегать для кода, архитектуры, критичных документов.

### Grok Code *(experimental)*
- Может подсказать простые сниппеты, но плохо держит контекст и правила.
- Применять только для черновых набросков под строгий ревью.

---

## 🎯 Decision Matrix

- **Sonnet 4.5**: архитектура, сложный код, безопасностные ревью, системные решения.
- **GPT‑5**: требования, планирование, отчётность, коммуникации.
- **GPT‑5 Codex High**: генерация паттернов, boilerplate, быстрые фиксы.
- **Haiku 4.5**: простые тексты, быстрые заметки.
- **Composer‑1 / Grok Code**: только для черновиков/песочницы и под обязательный ручной контроль.

---

## 📋 Ролевые рекомендации (шпаргалка)

### Developer
```
Primary: Sonnet 4.5 — сложный код, пайплайны, тесты, безопасность.
Alt:     GPT-5 Codex High — шаблонные изменения, генерация тестов.
Local:   Qwen2.5-Coder 32B, DeepSeek Coder V2 — first drafts, refactoring.
Fallback: Composer-1 / Grok Code — только для чернового кода.
```

### Tech Lead
```
Primary: Sonnet 4.5 — планирование, риск-менеджмент, контроль архитектуры.
Alt:     GPT-5 — дорожные карты, hand-off пакеты, review notes.
Local:   Llama 3.3 70B, Qwen2.5 72B — task breakdown, checklists.
Quick:   Haiku 4.5 — короткие апдейты/чеклисты.
```

### Architect
```
Primary: Sonnet 4.5 — system design, security review.
Alt:     GPT-5 — документация, протоколы, сравнение вариантов.
Local:   DeepSeek V3, Llama 3.3 — preliminary analysis, diagrams.
Drafts:  Composer-1 / Grok Code — только если нужен rough draft диаграмм/списков.
```

### Analyst
```
Primary: GPT-5 — требования, сводки, вопросы стейкхолдерам.
Alt:     Haiku 4.5 — быстрые обновления и заметки.
Local:   Llama 3.3 70B, Qwen2.5 72B — first drafts, simple analysis.
Drafts:  Composer-1 — шаблонные черновики, затем переписать в GPT-5.
```

---

## 💡 Best Practices

1. **Соотносите задачу со сложностью модели**: чем выше риск/сложность, тем выше класс модели (Sonnet 4.5, GPT‑5).
2. **Экономьте на рутинах**: Haiku 4.5, локальные модели или экспериментальные варианты — для простых шаблонных задач.
3. **Экспериментальные модели всегда под ревью**: Composer‑1 и Grok Code = только черновики.
4. **Переключайте модели в рамках одного флоу**: черновик в Local/Haiku → уточнение в GPT‑5 → проверка в Sonnet.
5. **Используйте сильные стороны каждой модели**: не заставляйте Haiku решать архитектурные задачи.
6. **Валидируйте важные решения**: критичные изменения проверяйте в Sonnet 4.5 независимо от начальной модели.

---

## ⚠️ Limited-Roster Playbook

При доступе только к Sonnet 4.5, GPT‑5, GPT‑5 Codex High, Haiku 4.5, Composer‑1, Grok Code:

- **Tech Lead** → Sonnet 4.5, резерв GPT‑5 (Haiku только для быстрых заметок).
- **Architect** → Sonnet 4.5, GPT‑5; Composer‑1/Grok Code использовать только как черновик.
- **Analyst** → GPT‑5, Haiku 4.5 для скорости; Composer‑1 лишь для rough draft.
- **Developer** → Sonnet 4.5 для сложных задач, GPT‑5 Codex High для шаблонов; Grok Code допустим только под строгий контроль.

Для критичных решений всегда переключайтесь на Sonnet 4.5 или GPT‑5, даже если черновик подготовлен экспериментальной моделью.

---

## 📈 Performance Comparison (относительно друг друга)

| Model            | Code Quality | Reasoning | Speed | Documentation |
|------------------|--------------|-----------|-------|---------------|
| **Sonnet 4.5**   | ⭐⭐⭐⭐⭐        | ⭐⭐⭐⭐⭐     | ⭐⭐⭐   | ⭐⭐⭐⭐          |
| **GPT-5**        | ⭐⭐⭐⭐         | ⭐⭐⭐⭐      | ⭐⭐⭐⭐  | ⭐⭐⭐⭐⭐         |
| **GPT-5 Codex**  | ⭐⭐⭐⭐         | ⭐⭐⭐       | ⭐⭐⭐⭐  | ⭐⭐⭐           |
| **Haiku 4.5**    | ⭐⭐           | ⭐⭐        | ⭐⭐⭐⭐⭐ | ⭐⭐⭐           |
| **Composer-1**   | ⭐            | ⭐         | ⭐⭐⭐⭐  | ⭐             |
| **Grok Code**    | ⭐⭐           | ⭐         | ⭐⭐⭐   | ⭐             |

---

## 🔄 Model Switching Workflow

**Standard Development Flow:**
1. **Local Model (Qwen2.5)** → Quick draft/first implementation
2. **GPT-5 or Haiku 4.5** → Refine and structure content
3. **Sonnet 4.5** → Final review and validation

**Code Development Flow:**
1. **Local (DeepSeek Coder) or GPT-5 Codex High** → Generate initial implementation
2. **Sonnet 4.5** → Code review and optimization
3. **GPT-5** → Documentation and testing

**Architecture Decisions:**
1. **Sonnet 4.5** → Primary analysis and design
2. **GPT-5** → Documentation and stakeholder communication
3. **Local (DeepSeek V3) optional** → Preliminary analysis for complex scenarios

---

## 📊 Cost-Benefit Analysis

| Model | Cost Efficiency | Quality | Speed | Best For |
|-------|----------------|---------|-------|----------|
| **Sonnet 4.5** | Medium | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Critical technical work |
| **GPT-5** | High | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Documentation, planning |
| **GPT-5 Codex** | High | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Code generation |
| **Haiku 4.5** | Very High | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Quick tasks, drafts |
| **Local Models** | **Highest** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **Routine work (see LOCAL_MODELS.md)** |
| **Composer-1** | Very High | ⭐⭐ | ⭐⭐⭐⭐ | Rough drafts only |
| **Grok Code** | High | ⭐⭐⭐ | ⭐⭐⭐ | Code experiments |

---

## 💰 2025 Cost Optimization Strategy

### **Cloud Only** vs **Hybrid (Cloud + Local)**

**Cloud Only (10 epics/month):**
- Cost: ~$24/month
- Quality: ⭐⭐⭐⭐⭐
- Speed: ⭐⭐⭐

**Hybrid with 70B Local Models:**
- Cloud cost: ~$8.40/month (65% savings)
- Hardware: RTX 4090 (~$1,500 one-time)
- Quality: ⭐⭐⭐⭐⭐ (when combined properly)
- Speed: ⭐⭐⭐⭐⭐
- Break-even: ~50 epics

**Hybrid with 236B+ Local Models:**
- Cloud cost: ~$5.25/month (78% savings)
- Hardware: 2x RTX 4090 (~$5,000 one-time)
- Quality: ⭐⭐⭐⭐⭐
- Speed: ⭐⭐⭐⭐
- Break-even: ~130 epics

**Recommendation:** См. [LOCAL_MODELS.md](LOCAL_MODELS.md) для детального cost analysis и setup guide.

---

## 🎯 Final Recommendations (2025 Edition)

### **Cloud Models Strategy**

**For Critical Work:**
- Always use **Sonnet 4.5** or **GPT-5** for final validation
- Architecture decisions → Sonnet 4.5
- Security analysis → Sonnet 4.5
- Production reviews → Sonnet 4.5

**For Speed:**
- Haiku 4.5 for quick iterations
- GPT-5 Codex High for code generation
- GPT-5 for documentation

**For Experiments:**
- Composer-1/Grok Code only with mandatory review
- Use for rough drafts that will be rewritten

**For Cost Optimization:**
- Consider local models for 60-80% of routine work
- Keep cloud models for critical decisions and validation
- See [LOCAL_MODELS.md](LOCAL_MODELS.md) for hybrid setup

---

### **🔄 2025 Recommended Workflow**

**Daily Development:**
1. **Morning planning** → GPT-5 or Local (Llama 3.3 70B)
2. **Implementation** → Local models (DeepSeek Coder V2, Qwen2.5-Coder)
3. **Code review** → Sonnet 4.5 (critical validation)
4. **Documentation** → Local models (Llama 3.3, Qwen2.5)
5. **Final review** → Sonnet 4.5 (before commit/deploy)

**Epic Planning:**
1. **Requirements draft** → GPT-5 or Local (Llama 3.3)
2. **Architecture design** → Sonnet 4.5 (critical reasoning)
3. **Implementation plan** → Sonnet 4.5 or Local (DeepSeek V3)
4. **Task breakdown** → Local models (Llama 3.3, Qwen2.5)
5. **Final review** → Sonnet 4.5 + GPT-5 (stakeholder review)

---

## 🔗 Related Resources

- **[LOCAL_MODELS.md](LOCAL_MODELS.md)** - Complete guide to local models setup and hybrid workflows
- **[README.md](README.md)** - Agent roles overview
- **[architect.md](architect.md)**, **[tech_lead.md](tech_lead.md)**, **[developer.md](developer.md)**, **[analyst.md](analyst.md)** - Role-specific guidelines

---

**Итог 2025:** Sonnet 4.5 и GPT‑5 остаются лучшими для **критичных решений**, но современные локальные модели (Llama 3.3 70B, DeepSeek V3, Qwen2.5) могут заменить облачные в **60-80% рутинных задач**, экономя до 78% на API costs.

**Рекомендуемая стратегия:** Используйте **гибридный подход** — локальные модели для daily work, облачные для validation и критических решений. См. [LOCAL_MODELS.md](LOCAL_MODELS.md) для детального setup guide и cost analysis.

**Quick Start:**
1. Установите Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
2. Загрузите модели: `ollama pull qwen2.5-coder:32b && ollama pull llama3.3:70b-instruct`
3. Используйте local для first drafts, Sonnet 4.5 для final review
4. Экономьте 60-78% на API costs 💰
