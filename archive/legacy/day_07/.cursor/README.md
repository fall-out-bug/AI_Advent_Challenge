# Cursor IDE Configuration

This directory contains Cursor IDE configuration files for optimal AI-assisted development with the StarCoder Multi-Agent System.

## Files Overview

- `rules.md` - Cursor rules for AI context and behavior
- `prompts.md` - Common prompts and examples for AI assistance
- `context.md` - Project context and architecture information
- `examples.md` - Code examples and patterns for AI reference

## Quick Start

1. **Open project in Cursor IDE**
2. **Load context**: Use `@context.md` to provide project overview
3. **Apply rules**: Use `@rules.md` for consistent AI behavior
4. **Use prompts**: Reference `@prompts.md` for common tasks

## AI Assistant Usage

### Basic Commands

```bash
# Generate code with specific requirements
@rules.md Generate a REST API endpoint for user authentication with JWT tokens

# Review existing code
@ai-reviewer.mdc Review the orchestrator.py file for improvements

# Create documentation
@technical-writer.mdc Create API documentation for the new endpoint

# Debug issues
@context.md Help debug the connection error in agent communication
```

### Advanced Usage

```bash
# Multi-agent workflow
@rules.md @context.md Implement a new agent type for data validation

# Code refactoring
@ai-reviewer.mdc Refactor the base_agent.py to improve readability

# Performance optimization
@context.md Optimize the batch processing in orchestrator.py
```

## Best Practices

1. **Always provide context** - Use `@context.md` for project overview
2. **Be specific** - Include detailed requirements and constraints
3. **Iterate** - Use AI feedback to refine and improve code
4. **Test** - Always test AI-generated code before committing
5. **Review** - Use `@ai-reviewer.mdc` for code quality checks

## Troubleshooting

### Common Issues

- **AI doesn't understand context**: Use `@context.md` to provide project information
- **Code quality issues**: Use `@ai-reviewer.mdc` for code review
- **Inconsistent behavior**: Ensure `@rules.md` is loaded
- **Missing examples**: Reference `@examples.md` for patterns

### Getting Help

- Check the examples in `examples.md`
- Review the context in `context.md`
- Use the prompts in `prompts.md`
- Refer to the main project documentation
