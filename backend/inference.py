import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel
import os
import re

# Global model placeholders
models = {}
tokenizers = {}

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EN2VI_LORA_PATH = os.path.join(BASE_DIR, "lora-vinai-en2vi")
VI2EN_LORA_PATH = os.path.join(BASE_DIR, "lora-vinai-vi2en")

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

    # Device Management
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    try:
        # Load Base Model
        # device_map="auto" can be unstable on some Windows setups, using explicit device
        model = AutoModelForSeq2SeqLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        ).to(device)
        
        # Load Tokenizer
        tokenizer = AutoTokenizer.from_pretrained(base_model_name, use_fast=False)

        # ... (LoRA skipped)

        models[direction] = model
        tokenizers[direction] = tokenizer
        return model, tokenizer

    except Exception as e:
        print(f"Error loading model {direction}: {e}")
        return None, None


def perform_translation(text: str, source_lang: str, target_lang: str):
    # ... (Direction logic same)
    if source_lang == "en" and target_lang == "vi":
        direction = "en2vi"
    elif source_lang == "vi" and target_lang == "en":
        direction = "vi2en"
    else:
        return None, "[Unsupported Language Pair]"

    model, tokenizer = load_model(direction)
    
    if model is None or tokenizer is None:
        return None, "Model could not be loaded"
    
    LANG_CODE_MAP = {"en": "en_XX", "vi": "vi_VN"}
    src_code = LANG_CODE_MAP.get(source_lang)
    tgt_code = LANG_CODE_MAP.get(target_lang)
    
    if not src_code or not tgt_code:
        return None, "Unsupported language code"

    try:
        tokenizer.src_lang = src_code
        inputs = tokenizer(text, return_tensors="pt", max_length=256, truncation=True).to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                input_ids=inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_length=256,
                decoder_start_token_id=tokenizer.lang_code_to_id[tgt_code],
                num_beams=1, # Reduced for stability
                early_stopping=False
            )
            
        translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        translated_text = re.sub(r"^[-.\s]+", "", translated_text).strip()
        
        return translated_text, None
    except Exception as e:
        print(f"Inference Error: {e}")
        return None, str(e)
