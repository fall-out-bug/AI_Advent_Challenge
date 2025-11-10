from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch, os
import re
import logging
import time
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
MODEL_NAME = os.environ.get("MODEL_NAME", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
HF_TOKEN = os.environ.get("HF_TOKEN")

logger.info(f"Starting model loading for: {MODEL_NAME}")
logger.info(f"HF_TOKEN available: {'Yes' if HF_TOKEN else 'No'}")

# Prometheus metrics initialization
_prometheus_metrics_initialized = False
_request_counter = None
_request_duration = None
_tokens_total = None
_model_loaded = None

# Use 4-bit quantization for all models
quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype="float16",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

try:
    logger.info(f"Loading tokenizer for model: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, token=HF_TOKEN)
    logger.info("Tokenizer loaded successfully")
    
    logger.info(f"Loading model: {MODEL_NAME} with quantization...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=quant_config,
        device_map="auto",
        token=HF_TOKEN
    )
    logger.info("Model loaded successfully!")
    
except Exception as e:
    logger.error(f"Failed to load model {MODEL_NAME}: {str(e)}")
    raise


def build_prompt(messages, model_name):
    model_lower = model_name.lower()
    # ======= TechxGenus/starcoder2-7b-instruct format =======
    if "techxgenus" in model_lower or "starcoder2-7b-instruct" in model_lower:
        system_msg = ""
        user_msg = ""
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            elif msg["role"] == "user":
                user_msg = msg["content"]
        
        if system_msg and user_msg:
            return f"### Instruction\n{system_msg}\n\n{user_msg}\n### Response\n"
        elif user_msg:
            return f"### Instruction\n{user_msg}\n### Response\n"
        else:
            return f"### Instruction\n{messages[-1]['content'] if messages else ''}\n### Response\n"
    # ======= Mistral-format (INSTRUCT) =======
    elif "mistral" in model_lower or "openhermes" in model_lower or "mixtral" in model_lower:
        system_msg = ""
        user_msgs = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            elif msg["role"] == "user":
                user_msgs.append(msg["content"])
        user_prompt = "\n".join(user_msgs)
        return f"<s>[INST] <<SYS>>\n{system_msg}\n<</SYS>>\n\n{user_prompt} [/INST]"
    # ======= Qwen-Chat format ===========
    elif "qwen" in model_lower:
        prompt = ""
        sys = None
        for msg in messages:
            if msg["role"] == "system":
                sys = msg["content"]
        if sys:
            prompt += f"<|im_start|>system\n{sys}<|im_end|>\n"
        for msg in messages:
            if msg["role"] == "user":
                prompt += f"<|im_start|>user\n{msg['content']}<|im_end|>\n"
            elif msg["role"] == "assistant":
                prompt += f"<|im_start|>assistant\n{msg['content']}<|im_end|>\n"
        prompt += "<|im_start|>assistant\n"
        return prompt
    # ======= TinyLlama ChatML ===========
    elif "tinyllama" in model_lower or "phi" in model_lower:
        prompt = ""
        for msg in messages:
            role = msg.get("role", "")
            if role in ["system", "user", "assistant"]:
                prompt += f"<|{role}|>\n{msg['content']}\n"
        prompt += "<|assistant|>\n"
        return prompt
    # ======= default (ChatML) ===========
    else:
        prompt = ""
        for msg in messages:
            role = msg.get("role", "")
            if role in ["system", "user", "assistant"]:
                prompt += f"<|{role}|>\n{msg['content']}\n"
        prompt += "<|assistant|>\n"
        return prompt



def clean_response(response, model_name):
    model_lower = model_name.lower()
    # Для TechxGenus/starcoder2-7b-instruct — ищем ### Response
    if "techxgenus" in model_lower or "starcoder2-7b-instruct" in model_lower:
        match = re.search(r"### Response\s*\n(.*)", response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()
    # Для Qwen и ChatML — ищем <|im_start|>assistant\n или "assistant "
    elif "qwen" in model_lower:
        # Ищем строго блок от <|im_start|>assistant
        match = re.search(r"<\|im_start\|>assistant\n(.*?)(?:<\|im_end\|>|\Z)", response, re.DOTALL)
        if match:
            return match.group(1).strip()
        # Если не нашли, fallback: ищем "assistant " в сыром тексте
        match2 = re.search(r"assistant\s*(.*)", response, re.DOTALL)
        if match2:
            return match2.group(1).strip()
        # Если ничего не получилось — просто всё без служебных маркеров
        return re.sub(r"(system|user|assistant)\s*", "", response).strip()
    # Для Mistral
    elif "mistral" in model_lower:
        match = re.search(r"\[/INST\](.*)", response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()
    # Для TinyLlama/ChatML
    elif "tinyllama" in model_lower or "phi" in model_lower:
        match = re.search(r"<\|assistant\|>\n(.*)", response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()
    # Default — всё после последнего "assistant"
    else:
        match = re.search(r"assistant\s*(.*)", response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()

@app.get("/health")
async def health():
    return {"status": "healthy", "model": MODEL_NAME}

@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    messages = body.get("messages", [])
    
    # Get limits from environment variables
    MAX_INPUT_TOKENS = int(os.environ.get("MAX_INPUT_TOKENS", "4096"))
    MAX_OUTPUT_TOKENS = int(os.environ.get("MAX_OUTPUT_TOKENS", "1024"))
    
    # Optimized defaults for better performance
    max_tokens = body.get("max_tokens", 512)
    temperature = body.get("temperature", 0.2)
    top_k = body.get("top_k", 40)
    top_p = body.get("top_p", 0.9)

    prompt = build_prompt(messages, MODEL_NAME)
    
    # Validate and truncate input if needed
    input_tokens = tokenizer.encode(prompt, add_special_tokens=False)
    if len(input_tokens) > MAX_INPUT_TOKENS:
        logger.warning(f"Input {len(input_tokens)} tokens exceeds {MAX_INPUT_TOKENS}, truncating")
        truncated_tokens = input_tokens[:MAX_INPUT_TOKENS]
        prompt = tokenizer.decode(truncated_tokens, skip_special_tokens=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    else:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    # Clamp max_new_tokens to server limit
    max_tokens = min(max_tokens, MAX_OUTPUT_TOKENS)
    
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_tokens,
        do_sample=True,
        temperature=temperature,
        top_k=top_k,
        top_p=top_p,
        pad_token_id=tokenizer.eos_token_id,
        return_dict_in_generate=True,
        output_scores=True,
        use_cache=True,
        num_beams=1,
        early_stopping=True
    )
    raw_response = tokenizer.decode(outputs.sequences[0], skip_special_tokens=True)
    answer = clean_response(raw_response, MODEL_NAME)

    response_tokens = outputs.sequences[0].shape[0] - inputs["input_ids"].shape[1]
    input_tokens = inputs["input_ids"].shape[1]

    return {
        "response": answer,
        "response_tokens": response_tokens,
        "input_tokens": input_tokens,
        "total_tokens": response_tokens + input_tokens
    }


@app.get("/limits")
async def get_limits():
    """Return model token limits and configuration."""
    MAX_INPUT_TOKENS = int(os.environ.get("MAX_INPUT_TOKENS", "4096"))
    MAX_OUTPUT_TOKENS = int(os.environ.get("MAX_OUTPUT_TOKENS", "1024"))
    FLASH_ATTN = os.environ.get("FLASH_ATTN", "false").lower() == "true"
    
    return {
        "model": MODEL_NAME,
        "max_input_tokens": MAX_INPUT_TOKENS,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "context_window": 16384,  # Theoretical limit
        "sliding_window": 4096,   # Attention window
        "flash_attn_enabled": FLASH_ATTN,
        "practical_limit": MAX_INPUT_TOKENS,
        "recommended_input": int(MAX_INPUT_TOKENS * 0.8)  # 80% of limit
    }


# OpenAI-compatible API endpoints

class ChatMessage(BaseModel):
    """OpenAI-compatible chat message."""
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""
    model: Optional[str] = Field(None, description="Model name (optional, uses configured model)")
    messages: List[ChatMessage] = Field(..., min_items=1, description="List of chat messages")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Top-p sampling parameter")
    top_k: Optional[int] = Field(None, ge=1, description="Top-k sampling parameter")
    stream: Optional[bool] = Field(False, description="Stream responses (not yet supported)")
    stop: Optional[List[str]] = Field(None, description="Stop sequences")
    presence_penalty: Optional[float] = Field(None, description="Presence penalty (not supported)")
    frequency_penalty: Optional[float] = Field(None, description="Frequency penalty (not supported)")


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completions endpoint.
    
    Purpose:
        Provides OpenAI-compatible API for chat completions.
        Converts OpenAI request format to internal format and back.
        
    Args:
        request: ChatCompletionRequest with OpenAI-compatible format
        
    Returns:
        OpenAI-compatible response with choices, usage, etc.
    """
    # Get limits from environment variables
    MAX_INPUT_TOKENS = int(os.environ.get("MAX_INPUT_TOKENS", "4096"))
    MAX_OUTPUT_TOKENS = int(os.environ.get("MAX_OUTPUT_TOKENS", "1024"))
    
    # Convert messages to internal format
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    
    # Use request parameters or defaults
    max_tokens = request.max_tokens or 512
    temperature = request.temperature if request.temperature is not None else 0.2
    top_k = request.top_k or 40
    top_p = request.top_p or 0.9
    
    # Validate max_tokens
    max_tokens = min(max_tokens, MAX_OUTPUT_TOKENS)
    
    # Build prompt using existing logic
    prompt = build_prompt(messages, MODEL_NAME)
    
    # Validate and truncate input if needed
    input_tokens = tokenizer.encode(prompt, add_special_tokens=False)
    if len(input_tokens) > MAX_INPUT_TOKENS:
        logger.warning(f"Input {len(input_tokens)} tokens exceeds {MAX_INPUT_TOKENS}, truncating")
        truncated_tokens = input_tokens[:MAX_INPUT_TOKENS]
        prompt = tokenizer.decode(truncated_tokens, skip_special_tokens=True)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    else:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    # Generate response using existing logic
    try:
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=True,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            pad_token_id=tokenizer.eos_token_id,
            return_dict_in_generate=True,
            output_scores=True,
            use_cache=True,
            num_beams=1,
            early_stopping=True
        )
        raw_response = tokenizer.decode(outputs.sequences[0], skip_special_tokens=True)
        answer = clean_response(raw_response, MODEL_NAME)
        
        response_tokens = outputs.sequences[0].shape[0] - inputs["input_ids"].shape[1]
        input_tokens_count = inputs["input_ids"].shape[1]
        total_tokens = response_tokens + input_tokens_count
        
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
    
    # Format response in OpenAI-compatible format
    response_id = f"chatcmpl-{uuid.uuid4().hex[:10]}"
    created = int(time.time())
    
    return {
        "id": response_id,
        "object": "chat.completion",
        "created": created,
        "model": MODEL_NAME,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": answer
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": input_tokens_count,
            "completion_tokens": response_tokens,
            "total_tokens": total_tokens
        }
    }


@app.get("/v1/models")
async def list_models():
    """
    OpenAI-compatible models listing endpoint.
    
    Purpose:
        Returns list of available models in OpenAI-compatible format.
        
    Returns:
        OpenAI-compatible models list response
    """
    MAX_INPUT_TOKENS = int(os.environ.get("MAX_INPUT_TOKENS", "4096"))
    MAX_OUTPUT_TOKENS = int(os.environ.get("MAX_OUTPUT_TOKENS", "1024"))
    
    # Extract model name without organization prefix for display
    model_id = MODEL_NAME.split("/")[-1] if "/" in MODEL_NAME else MODEL_NAME
    
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_NAME,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "local",
                "permission": [],
                "root": MODEL_NAME,
                "parent": None
            }
        ]
    }


@app.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    """
    OpenAI-compatible model info endpoint.
    
    Purpose:
        Returns information about a specific model.
        
    Args:
        model_id: Model identifier
        
    Returns:
        OpenAI-compatible model info response
    """
    MAX_INPUT_TOKENS = int(os.environ.get("MAX_INPUT_TOKENS", "4096"))
    MAX_OUTPUT_TOKENS = int(os.environ.get("MAX_OUTPUT_TOKENS", "1024"))
    
    # For now, return info about the current model
    # In future, could support multiple models per container
    if model_id != MODEL_NAME and model_id not in MODEL_NAME:
        raise HTTPException(
            status_code=404,
            detail=f"Model {model_id} not found. Available model: {MODEL_NAME}"
        )
    
    return {
        "id": MODEL_NAME,
        "object": "model",
        "created": int(time.time()),
        "owned_by": "local",
        "permission": [],
        "root": MODEL_NAME,
        "parent": None
    }


def _init_prometheus_metrics():
    """Initialize Prometheus metrics."""
    global _prometheus_metrics_initialized, _request_counter, _request_duration, _tokens_total, _model_loaded
    
    if _prometheus_metrics_initialized:
        return
    
    try:
        from prometheus_client import Counter, Histogram, Gauge
        
        _request_counter = Counter(
            'llm_requests_total',
            'Total number of LLM requests',
            ['model', 'endpoint']
        )
        _request_duration = Histogram(
            'llm_request_duration_seconds',
            'Request duration in seconds',
            ['model', 'endpoint'],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
        )
        _tokens_total = Counter(
            'llm_tokens_total',
            'Total tokens processed',
            ['model', 'type']  # type: input, output, total
        )
        _model_loaded = Gauge(
            'llm_model_loaded',
            'Whether model is loaded (1) or not (0)',
            ['model']
        )
        _model_loaded.labels(model=MODEL_NAME).set(1)
        _prometheus_metrics_initialized = True
    except ImportError:
        logger.warning("prometheus_client not available, metrics will be disabled")
        _prometheus_metrics_initialized = True  # Set to True to avoid repeated attempts


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Purpose:
        Exposes Prometheus metrics in standard format.
        Returns basic metrics about the model service.
        
    Returns:
        Prometheus metrics in text format
    """
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY
        
        _init_prometheus_metrics()
        
        return Response(
            content=generate_latest(REGISTRY),
            media_type=CONTENT_TYPE_LATEST
        )
    except ImportError:
        # Fallback if prometheus-client not available
        return Response(
            content="# Prometheus client not installed\n",
            media_type="text/plain"
        )
    except Exception as e:
        logger.error(f"Failed to generate metrics: {str(e)}")
        return Response(
            content=f"# Error generating metrics: {str(e)}\n",
            media_type="text/plain",
            status_code=500
        )