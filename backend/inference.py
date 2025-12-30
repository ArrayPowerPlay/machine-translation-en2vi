import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel
import os

# Global model placeholders
models = {}
tokenizers = {}

# Configuration
EN2VI_LORA_PATH = "./lora-vinai-en2vi"
VI2EN_LORA_PATH = "./lora-vinai-vi2en"

EN2VI_BASE = "vinai/vinai-translate-en2vi"
VI2EN_BASE = "vinai/vinai-translate-vi2en"


def load_model(direction="en2vi"):
    """
    Hàm load model + LoRA adapter (nếu có).
    Chỉ load khi cần để tiết kiệm RAM.
    """
    global models, tokenizers
    
    if direction in models:
        return models[direction], tokenizers[direction]

    print(f"Loading model for {direction}...")
    
    if direction == "en2vi":
        base_model_name = EN2VI_BASE
        adapter_path = EN2VI_LORA_PATH
    else:
        base_model_name = VI2EN_BASE
        adapter_path = VI2EN_LORA_PATH

    try:
        # Load Base Model
        # Sử dụng device_map="auto" để tự động dùng GPU nếu có
        model = AutoModelForSeq2SeqLM.from_pretrained(
            base_model_name,
            device_map="auto",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        
        # Load Tokenizer
        tokenizer = AutoTokenizer.from_pretrained(base_model_name)

        # Load LoRA Adapter nếu tồn tại folder
        if os.path.exists(adapter_path):
            print(f"Found LoRA adapter at {adapter_path}. Loading...")
            model = PeftModel.from_pretrained(model, adapter_path)
        else:
            print(f"No LoRA adapter found at {adapter_path} or PEFT missing. Using base model.")

        models[direction] = model
        tokenizers[direction] = tokenizer
        return model, tokenizer

    except Exception as e:
        print(f"Error loading model {direction}: {e}")
        return None, None


def perform_translation(text: str, source_lang: str, target_lang: str):
    # Xác định hướng dịch
    if source_lang == "en" and target_lang == "vi":
        direction = "en2vi"
    elif source_lang == "vi" and target_lang == "en":
        direction = "vi2en"
    else:
        return None, "[Unsupported Language Pair]"

    model, tokenizer = load_model(direction)
    
    if model is None or tokenizer is None:
        return None, "Model could not be loaded"
    
    # Map ngôn ngữ request (en/vi) sang mã của mBART (en_XX/vi_VN)
    LANG_CODE_MAP = {"en": "en_XX", "vi": "vi_VN"}
    src_code = LANG_CODE_MAP.get(source_lang)
    tgt_code = LANG_CODE_MAP.get(target_lang)
    
    if not src_code or not tgt_code:
        return None, "Unsupported language code"

    # 1. Set source language cho tokenizer
    tokenizer.src_lang = src_code
    
    # 2. Tokenize
    # Move inputs to device handled by model
    inputs = tokenizer(text, return_tensors="pt", max_length=128, truncation=True).to(model.device)
    
    # 3. Generate
    with torch.no_grad():
        outputs = model.generate(
            inputs.input_ids, 
            max_length=128,
            forced_bos_token_id=tokenizer.lang_code_to_id[tgt_code]
        )
        
    translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return translated_text, None
