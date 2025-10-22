from transformers import AutoModelForCausalLM, AutoTokenizer
import os

model_name = os.environ.get("MODEL_NAME", "meta-llama/Llama-2-7b-chat-hf")
hf_token = os.environ.get("HF_TOKEN")

tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=hf_token)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    load_in_4bit=True,
    device_map="cpu",
    use_auth_token=hf_token
)
print(f"Model {model_name} downloaded and cached.")
