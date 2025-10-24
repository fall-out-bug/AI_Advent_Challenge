# AI Agents Quick Reference

## 🎯 Agent Selection Guide

| Task Type | Primary Agent | Secondary Agent | Use Case |
|-----------|---------------|-----------------|----------|
| **Documentation** | @technical-writer.mdc | @ai-reviewer.mdc | API docs, user guides, README |
| **Code Review** | @ai-reviewer.mdc | @py-reviewer.mdc | Quality, readability, optimization |
| **Architecture** | @chief-architect.mdc | @devops-engineer.mdc | System design, patterns, scalability |
| **Security** | @security-reviewer.mdc | @docker-reviewer.mdc | Security audit, hardening |
| **Testing** | @qa-tdd-reviewer.mdc | @py-reviewer.mdc | Test strategy, TDD, coverage |
| **Infrastructure** | @devops-engineer.mdc | @docker-reviewer.mdc | CI/CD, deployment, monitoring |
| **Python Code** | @py-reviewer.mdc | @python-zen-writer.mdc | Python best practices, PEP 8 |
| **JavaScript** | @js-reviewer.mdc | @ai-reviewer.mdc | JS/TS patterns, types |
| **Shell Scripts** | @sh-reviewer.mdc | @security-reviewer.mdc | Script security, readability |
| **Data Engineering** | @data-engineer.mdc | @ml-engineer.mdc | ETL, schemas, pipelines |
| **ML/AI** | @ml-engineer.mdc | @data-engineer.mdc | ML pipelines, models |
| **Project Management** | @tl-vasiliy.mdc | @chief-architect.mdc | Planning, coordination |

## 🚀 Quick Commands

### Documentation
```bash
@technical-writer.mdc Create API documentation for the new endpoint
@technical-writer.mdc Write user guide for authentication system
@technical-writer.mdc Generate changelog for v2.0 release
```

### Code Quality
```bash
@ai-reviewer.mdc Review orchestrator.py for readability improvements
@py-reviewer.mdc Check Python code for PEP 8 compliance
@security-reviewer.mdc Audit authentication module for vulnerabilities
```

### Architecture & Design
```bash
@chief-architect.mdc Design microservices architecture for e-commerce
@devops-engineer.mdc Set up CI/CD pipeline for the application
@docker-reviewer.mdc Optimize Dockerfile for security and size
```

### Testing & Quality
```bash
@qa-tdd-reviewer.mdc Implement TDD approach for new feature
@qa-tdd-reviewer.mdc Set up comprehensive test strategy
@py-reviewer.mdc Review test coverage and suggest improvements
```

### Security & Infrastructure
```bash
@security-reviewer.mdc Audit Docker configuration for security
@docker-reviewer.mdc Implement Docker best practices
@devops-engineer.mdc Set up monitoring and alerting
```

## 🔧 Multi-Agent Workflows

### Comprehensive Code Review
```bash
@ai-reviewer.mdc @security-reviewer.mdc @py-reviewer.mdc Review the authentication module
```

### Full Stack Architecture
```bash
@chief-architect.mdc @devops-engineer.mdc @security-reviewer.mdc Design scalable system architecture
```

### Complete Feature Development
```bash
@chief-architect.mdc Design the feature architecture
@py-reviewer.mdc Implement the Python code
@qa-tdd-reviewer.mdc Create comprehensive tests
@technical-writer.mdc Write documentation
@security-reviewer.mdc Security review
```

## 📋 Agent Capabilities Matrix

| Agent | Code Review | Architecture | Security | Testing | Documentation | DevOps | Performance |
|-------|-------------|--------------|----------|---------|---------------|--------|-------------|
| @technical-writer.mdc | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐ |
| @ai-reviewer.mdc | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐ |
| @chief-architect.mdc | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ |
| @py-reviewer.mdc | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐ |
| @security-reviewer.mdc | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐ |
| @docker-reviewer.mdc | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ |
| @qa-tdd-reviewer.mdc | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐ |
| @devops-engineer.mdc | ⭐ | ⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ |
| @js-reviewer.mdc | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐ |
| @python-zen-writer.mdc | ⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ |
| @sh-reviewer.mdc | ⭐⭐ | ⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐ |
| @data-engineer.mdc | ⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐⭐ |
| @ml-engineer.mdc | ⭐ | ⭐⭐ | ⭐ | ⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐ |
| @tl-vasiliy.mdc | ⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐⭐ | ⭐ |

**Legend**: ⭐ = Basic, ⭐⭐ = Good, ⭐⭐⭐ = Expert

## 🎨 Usage Patterns

### 1. Single Agent Focus
```bash
# Focus on specific expertise
@py-reviewer.mdc Review this Python code for best practices
@security-reviewer.mdc Audit this code for security vulnerabilities
```

### 2. Complementary Agents
```bash
# Use complementary skills
@ai-reviewer.mdc @py-reviewer.mdc Review code for readability and Python best practices
@chief-architect.mdc @devops-engineer.mdc Design architecture with deployment considerations
```

### 3. Sequential Workflow
```bash
# Step-by-step approach
@chief-architect.mdc Design the system architecture
@py-reviewer.mdc Implement the Python components
@qa-tdd-reviewer.mdc Create comprehensive tests
@technical-writer.mdc Write documentation
```

### 4. Comprehensive Analysis
```bash
# Full analysis with multiple agents
@ai-reviewer.mdc @security-reviewer.mdc @py-reviewer.mdc @docker-reviewer.mdc 
Comprehensive review of the authentication system
```

## 💡 Pro Tips

### 1. Context is Key
```bash
# Always provide context
@technical-writer.mdc @context.md Create API documentation for StarCoder Multi-Agent System
```

### 2. Be Specific
```bash
# Specific requirements
@ai-reviewer.mdc Optimize this function for better readability and performance
```

### 3. Use Examples
```bash
# Reference examples
@py-reviewer.mdc Implement Python best practices following the patterns in examples.md
```

### 4. Iterative Approach
```bash
# Start broad, then refine
@chief-architect.mdc Design high-level architecture
@py-reviewer.mdc Implement specific components
@ai-reviewer.mdc Optimize for readability
```

### 5. Combine Expertise
```bash
# Leverage multiple agents
@security-reviewer.mdc @docker-reviewer.mdc Secure the containerized application
```

## 🔍 Troubleshooting

### Agent Not Responding Well?
- Provide more specific context
- Use relevant examples
- Check agent capabilities
- Try complementary agents

### Conflicting Recommendations?
- Prioritize based on project goals
- Consider trade-offs
- Make informed decisions
- Document reasoning

### Missing Expertise?
- Combine multiple agents
- Provide additional context
- Use examples and patterns
- Reference project documentation

## 📚 Additional Resources

- **Full Documentation**: See `AGENTS.md` for detailed agent descriptions
- **Project Context**: Use `@context.md` for project-specific information
- **Code Examples**: Reference `@examples.md` for implementation patterns
- **Best Practices**: Follow `@rules.md` for consistent standards
- **Prompts**: Use `@prompts.md` for common task templates

---

**Remember**: Choose the right agent for your task, provide clear context, and use iterative approaches for best results! 🚀
