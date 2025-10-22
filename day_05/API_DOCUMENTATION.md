# 📚 API Documentation - Day 05 Zen Chat Application

*Comprehensive API reference for the modular chat application*

## 🏗️ **Architecture Overview**

The application follows a clean modular architecture with separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   TerminalUI    │    │   ChatLogic     │    │   ChatState     │
│   (Presentation)│◄──►│   (Business)    │◄──►│   (Data)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   TextUtils     │
                    │   (Utilities)   │
                    └─────────────────┘
```

## 📦 **Module Reference**

### **ChatLogic** (`business/chat_logic.py`)

Main business logic handler for API calls and model routing.

#### **Class: ChatLogic**

```python
class ChatLogic:
    """Handles chat business logic and API calls."""
```

#### **Methods**

##### **`__init__(self, chat_state)`**
Initialize chat logic with state reference.

**Parameters:**
- `chat_state` (ChatState): Reference to application state

---

##### **`async call_model(self, message: str, temperature: float, system_prompt: Optional[str] = None, use_history: bool = False) -> Dict`**

Route API call to current provider (local/external).

**Parameters:**
- `message` (str): User input message to process
- `temperature` (float): Generation temperature (0.0-1.5)
- `system_prompt` (Optional[str]): Optional system prompt override
- `use_history` (bool): Whether to include conversation history

**Returns:**
- `Dict`: Response dictionary with keys:
  - `response` (str): Generated text response
  - `input_tokens` (int): Number of input tokens used
  - `response_tokens` (int): Number of response tokens generated
  - `total_tokens` (int): Total tokens consumed

**Raises:**
- `httpx.RequestError`: On network failures
- `ValueError`: On invalid temperature values

**Example:**
```python
logic = ChatLogic(state)
response = await logic.call_model(
    message="Hello world",
    temperature=0.7,
    system_prompt="You are a helpful assistant"
)
print(response["response"])
```

---

##### **`parse_temp_override(self, user_message: str) -> Tuple[Optional[float], str]`**

Parse one-off temperature override in 'temp=<v> <text>' format.

**Parameters:**
- `user_message` (str): User input that may contain temperature override

**Returns:**
- `Tuple[Optional[float], str]`: Tuple of (temperature_value, clean_message)

**Example:**
```python
temp, message = logic.parse_temp_override("temp=0.8 Hello world")
# temp = 0.8, message = "Hello world"
```

---

##### **`apply_interactive_temperature(self, reply_text: str) -> None`**

Apply interactive temperature based on reply content.

**Parameters:**
- `reply_text` (str): AI response text to analyze for temperature triggers

**Temperature Triggers:**
- "не душни" → T=0.0 (calm)
- "потише" → T=0.7 (normal)
- "разгоняй" → T=1.2 (aggressive)

---

##### **`switch_model(self, model_name: str) -> bool`**

Switch to specified model.

**Parameters:**
- `model_name` (str): Model identifier (e.g., "local-qwen", "chadgpt")

**Returns:**
- `bool`: True if switch successful, False if invalid model

---

### **TerminalUI** (`ui/terminal_ui.py`)

Handles all terminal UI operations and user interaction.

#### **Class: TerminalUI**

```python
class TerminalUI:
    """Handles all terminal UI operations for chat application."""
```

#### **Methods**

##### **`__init__(self, chat_state)`**
Initialize UI with chat state reference.

**Parameters:**
- `chat_state` (ChatState): Reference to application state

---

##### **`print_welcome(self) -> None`**
Print welcome message and help information.

**Displays:**
- Application title and version
- Available commands
- Temperature triggers
- Available models

---

##### **`print_ded_message(self, message: str, eff_temp: Optional[float] = None) -> None`**

Pretty-print model message with optional temperature indicator.

**Parameters:**
- `message` (str): The response message from the AI model
- `eff_temp` (Optional[float]): Effective temperature used for generation

**Note:** Temperature indicator is only shown when explain_mode is enabled

---

##### **`print_debug_info(self, user_message: str, reply_data: Dict[str, Any], eff_temp: float, sys_prompt: Optional[str], duration_ms: int) -> None`**

Print extended debug information in explain mode.

**Parameters:**
- `user_message` (str): Original user input
- `reply_data` (Dict[str, Any]): Response data from API
- `eff_temp` (float): Effective temperature used
- `sys_prompt` (Optional[str]): System prompt used
- `duration_ms` (int): Response time in milliseconds

---

##### **`get_user_input(self) -> str`**
Read user input with temperature indicator.

**Returns:**
- `str`: User input string

---

##### **`print_error(self, message: str) -> None`**
Print error message with error icon.

**Parameters:**
- `message` (str): Error message to display

---

##### **`print_success(self, message: str) -> None`**
Print success message with success icon.

**Parameters:**
- `message` (str): Success message to display

---

### **ChatState** (`state/chat_state.py`)

Manages chat application state and configuration.

#### **Class: ChatState**

```python
class ChatState:
    """Manages chat application state and configuration."""
```

#### **Properties**

- `api_key` (Optional[str]): Current API key
- `client` (Optional[httpx.AsyncClient]): HTTP client instance
- `default_temperature` (float): Default generation temperature
- `explain_mode` (bool): Whether debug mode is enabled
- `current_api` (Optional[str]): Current API provider
- `advice_mode` (Optional[AdviceModeV5]): Advice mode instance
- `use_history` (bool): Whether to use conversation history

#### **Methods**

##### **`async __aenter__(self)`**
Async context manager entry.

**Returns:**
- `ChatState`: Self instance

---

##### **`async __aexit__(self, exc_type, exc_val, exc_tb)`**
Async context manager exit.

**Parameters:**
- `exc_type`: Exception type
- `exc_val`: Exception value
- `exc_tb`: Exception traceback

---

##### **`setup(self) -> bool`**
Ensure at least one API is configured.

**Returns:**
- `bool`: True if setup successful, False otherwise

**Behavior:**
1. Check for local models first
2. Fall back to external APIs
3. Set default model if available

---

##### **`set_temperature(self, temperature: float) -> None`**
Set default temperature.

**Parameters:**
- `temperature` (float): Temperature value (0.0-1.5)

---

##### **`toggle_explain_mode(self) -> None`**
Toggle explain mode on/off.

---

##### **`switch_model(self, model_name: str) -> bool`**
Switch to specified model.

**Parameters:**
- `model_name` (str): Model identifier

**Returns:**
- `bool`: True if switch successful

---

### **TextUtils** (`utils/text_utils.py`)

Utility functions for text processing.

#### **Functions**

##### **`contains_any(haystack: str, needles: List[str]) -> bool`**

Check if haystack contains any of the needles.

**Parameters:**
- `haystack` (str): String to search in
- `needles` (List[str]): List of strings to search for

**Returns:**
- `bool`: True if any needle is found in haystack

**Example:**
```python
result = contains_any("Hello world", ["world", "universe"])
# result = True
```

---

##### **`normalize_for_trigger(text: str) -> str`**

Normalize unicode and punctuation to improve trigger matching.

**Parameters:**
- `text` (str): Input text to normalize

**Returns:**
- `str`: Normalized text with collapsed spaces

**Normalization:**
- Unicode normalization (NFKC)
- Lowercase conversion
- Punctuation replacement with spaces
- Multiple space collapse

**Example:**
```python
normalized = normalize_for_trigger("Hello—world!")
# normalized = "hello world"
```

## 🔧 **Configuration**

### **API Configuration**

The application supports multiple API providers:

#### **External APIs**
- **Perplexity**: `https://api.perplexity.ai/chat/completions`
- **ChadGPT**: `https://ask.chadgpt.ru/api/public/gpt-5-mini`

#### **Local Models**
- **Qwen**: `http://localhost:8000`
- **Mistral**: `http://localhost:8001`
- **TinyLlama**: `http://localhost:8002`

### **Environment Variables**

- `PERPLEXITY_API_KEY`: Perplexity API key
- `CHAD_API_KEY`: ChadGPT API key

### **Configuration File**

API keys can be stored in `api_key.txt`:
```
perplexity:your_perplexity_key_here
chadgpt:your_chadgpt_key_here
```

## 🚀 **Usage Examples**

### **Basic Usage**

```python
from terminal_chat_v5_zen import DedChatV5Zen

async def main():
    async with DedChatV5Zen() as chat:
        if not chat.setup():
            return
        
        # Process user input
        await chat._process_message("Hello, how are you?")
```

### **Custom Configuration**

```python
from state.chat_state import ChatState
from business.chat_logic import ChatLogic

# Create custom state
state = ChatState()
state.set_temperature(0.8)
state.set_explain_mode(True)

# Create logic handler
logic = ChatLogic(state)

# Make API call
response = await logic.call_model(
    message="Tell me a joke",
    temperature=0.9
)
```

### **Text Processing**

```python
from utils.text_utils import contains_any, normalize_for_trigger

# Check for triggers
if contains_any(user_input, ["help", "assistance"]):
    show_help()

# Normalize for processing
normalized = normalize_for_trigger("Hello—world!")
```

## ⚠️ **Error Handling**

### **Common Exceptions**

- `httpx.RequestError`: Network connectivity issues
- `ValueError`: Invalid parameter values
- `ImportError`: Missing dependencies

### **Error Recovery**

The application includes graceful error handling:
- Automatic fallback between API providers
- Input validation and sanitization
- User-friendly error messages

## 📝 **Changelog**

### **v5.0 (Zen Version)**
- Complete modular refactoring
- Separation of concerns
- Enhanced type safety
- Comprehensive test coverage
- Improved documentation

---

*This API documentation is automatically generated and maintained as part of the Zen refactoring project.*
