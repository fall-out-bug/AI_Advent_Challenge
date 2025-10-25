from fastapi import FastAPI, Request
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch, os
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
MODEL_NAME = os.environ.get("MODEL_NAME", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
HF_TOKEN = os.environ.get("HF_TOKEN")

logger.info(f"Starting model loading for: {MODEL_NAME}")
logger.info(f"HF_TOKEN available: {'Yes' if HF_TOKEN else 'No'}")

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