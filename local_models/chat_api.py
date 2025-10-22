from fastapi import FastAPI, Request
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch, os
import re

app = FastAPI()
MODEL_NAME = os.environ.get("MODEL_NAME", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")

quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype="float16",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

print(f"Loading model: {MODEL_NAME} ...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=quant_config,
    device_map="auto"
)
print("Model loaded!")


def build_prompt(messages, model_name):
    model_lower = model_name.lower()
    # ======= Mistral-format (INSTRUCT) =======
    if "mistral" in model_lower or "openhermes" in model_lower or "mixtral" in model_lower:
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
    # Для Qwen и ChatML — ищем <|im_start|>assistant\n или "assistant "
    if "qwen" in model_lower:
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

@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    messages = body.get("messages", [])
    max_tokens = body.get("max_tokens", 800)
    temperature = body.get("temperature", 0.7)

    prompt = build_prompt(messages, MODEL_NAME)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=max_tokens,
        do_sample=True,
        temperature=temperature,
        pad_token_id=tokenizer.eos_token_id,
        return_dict_in_generate=True,
        output_scores=True
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