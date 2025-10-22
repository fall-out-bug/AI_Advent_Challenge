# 👨‍💻 Developer Guide - Day 05 Zen Chat Application

*Complete guide for developers working on the modular chat application*

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.10+
- pip or poetry
- Git

### **Setup**
```bash
# Clone the repository
git clone <repository-url>
cd AI_Challenge/day_05

# Install dependencies
pip install -r requirements.txt

# Run tests
make test

# Start the application
make run-zen
```

## 🏗️ **Architecture Principles**

### **Design Philosophy**
The application follows **Python Zen principles** and **SOLID design patterns**:

1. **Single Responsibility**: Each module has one clear purpose
2. **Open/Closed**: Easy to extend with new APIs without modifying existing code
3. **Liskov Substitution**: All components are interchangeable
4. **Interface Segregation**: Clear, focused interfaces
5. **Dependency Inversion**: Depend on abstractions, not concretions

### **Module Responsibilities**

| Module | Responsibility | Dependencies |
|--------|----------------|--------------|
| `ChatLogic` | API calls, routing, business rules | `ChatState`, `TextUtils` |
| `TerminalUI` | User interface, display, input | `ChatState` |
| `ChatState` | State management, configuration | `config`, `LocalModelClient` |
| `TextUtils` | Text processing utilities | None |

## 🔧 **Development Workflow**

### **Code Style Guidelines**

#### **Python Zen Compliance**
- **Simple is better than complex**: Keep functions small and focused
- **Explicit is better than implicit**: Use clear variable names and type hints
- **Flat is better than nested**: Avoid deep nesting, use early returns
- **Readability counts**: Write self-documenting code

#### **Type Hints**
Always use type hints for function parameters and return values:

```python
def process_message(
    self, 
    message: str, 
    temperature: float
) -> Dict[str, Any]:
    """Process user message with specified temperature."""
    pass
```

#### **Docstrings**
Use comprehensive docstrings following Google style:

```python
def call_model(
    self, 
    message: str, 
    temperature: float, 
    system_prompt: Optional[str] = None
) -> Dict:
    """
    Route API call to current provider.
    
    Args:
        message: User input message to process
        temperature: Generation temperature (0.0-1.5)
        system_prompt: Optional system prompt override
        
    Returns:
        Dict with response data including tokens and timing
        
    Raises:
        httpx.RequestError: On network failures
        ValueError: On invalid parameters
    """
```

### **Testing Guidelines**

#### **Test Structure**
- One test file per module: `test_<module_name>.py`
- One test class per class: `Test<ClassName>`
- One test method per function: `test_<function_name>`

#### **Test Naming**
```python
def test_call_model_success(self):
    """Test successful API call."""
    pass

def test_call_model_invalid_temperature(self):
    """Test API call with invalid temperature."""
    pass
```

#### **Running Tests**
```bash
# All tests
make test

# Specific module
python -m pytest tests/test_chat_logic.py -v

# With coverage
make test-coverage
```

### **Adding New Features**

#### **1. New API Provider**
```python
# In ChatLogic class
async def _call_new_provider(self, message: str, temperature: float) -> str:
    """Call new API provider."""
    # Implementation
    pass

def _create_new_provider_payload(self, message: str, temperature: float) -> Dict:
    """Create payload for new provider."""
    # Implementation
    pass
```

#### **2. New UI Component**
```python
# In TerminalUI class
def print_new_feature(self, data: Any) -> None:
    """Print new feature information."""
    # Implementation
    pass
```

#### **3. New Utility Function**
```python
# In utils/text_utils.py
def new_utility_function(input_data: str) -> str:
    """
    New utility function description.
    
    Args:
        input_data: Input string to process
        
    Returns:
        Processed string
    """
    # Implementation
    pass
```

## 🐛 **Debugging**

### **Debug Mode**
Enable explain mode for detailed debugging:

```python
state = ChatState()
state.set_explain_mode(True)
```

This will show:
- Temperature used
- Model name
- API endpoint
- Response time
- Token usage

### **Common Issues**

#### **Import Errors**
```python
# ❌ Bad - sys.path manipulation
sys.path.append(os.path.join(...))

# ✅ Good - explicit imports
from business.chat_logic import ChatLogic
```

#### **Type Errors**
```python
# ❌ Bad - no type hints
def process_data(data):
    return data

# ✅ Good - explicit types
def process_data(data: Dict[str, Any]) -> str:
    return str(data)
```

#### **Async/Await Issues**
```python
# ❌ Bad - missing await
response = logic.call_model(message, temperature)

# ✅ Good - proper async handling
response = await logic.call_model(message, temperature)
```

## 📊 **Performance Guidelines**

### **Function Size**
- **Target**: 8-15 lines per function
- **Maximum**: 25 lines
- **Refactor if**: Function does multiple things

### **Class Size**
- **Target**: 100-200 lines per class
- **Maximum**: 300 lines
- **Refactor if**: Class has multiple responsibilities

### **Module Size**
- **Target**: 200-400 lines per module
- **Maximum**: 500 lines
- **Split if**: Module becomes too complex

## 🔍 **Code Review Checklist**

### **Before Submitting**
- [ ] All tests pass
- [ ] Type hints added
- [ ] Docstrings complete
- [ ] No `sys.path` manipulation
- [ ] Functions are small and focused
- [ ] Error handling implemented
- [ ] No hardcoded values

### **Review Criteria**
- [ ] Follows Python Zen principles
- [ ] Maintains separation of concerns
- [ ] Includes appropriate tests
- [ ] Handles edge cases
- [ ] Performance considerations

## 🚀 **Deployment**

### **Production Checklist**
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Configuration externalized
- [ ] Error logging implemented
- [ ] Performance monitoring added
- [ ] Security review completed

### **Environment Setup**
```bash
# Production environment
export PERPLEXITY_API_KEY="your_key"
export CHAD_API_KEY="your_key"

# Run application
python terminal_chat_v5_zen.py
```

## 📚 **Resources**

### **Documentation**
- [API Documentation](API_DOCUMENTATION.md)
- [Python Zen Principles](https://peps.python.org/pep-0020/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

### **Tools**
- **Linting**: `flake8`, `black`
- **Testing**: `pytest`, `pytest-cov`
- **Type Checking**: `mypy`
- **Documentation**: `sphinx`

### **Commands**
```bash
# Code formatting
black .

# Linting
flake8 .

# Type checking
mypy .

# Test coverage
pytest --cov=. --cov-report=html
```

## 🤝 **Contributing**

### **Pull Request Process**
1. Create feature branch
2. Implement changes with tests
3. Update documentation
4. Run full test suite
5. Submit pull request

### **Commit Messages**
Use conventional commit format:
```
feat: add new API provider support
fix: resolve temperature parsing issue
docs: update API documentation
test: add tests for new utility functions
```

---

*This developer guide is maintained as part of the Zen refactoring project. Please keep it updated as the codebase evolves.*
