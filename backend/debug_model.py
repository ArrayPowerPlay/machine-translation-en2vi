from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

model_name = "vinai/vinai-translate-en2vi"
device = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading model {model_name} on {device}...")
tokenizer = AutoTokenizer.from_pretrained(model_name, src_lang="en_XX", use_fast=False)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)

text = "I love you"
print(f"Translating: {text}")

input_ids = tokenizer(text, return_tensors="pt").input_ids.to(device)
print(f"Input IDs: {input_ids}")

# Cách 1: Standard generate
print("--- Standard Generate ---")
outputs = model.generate(input_ids, decoder_start_token_id=tokenizer.lang_code_to_id["vi_VN"], num_beams=5, max_length=128)
print(f"Raw Output: {outputs}")
print(f"Decoded: {tokenizer.decode(outputs[0], skip_special_tokens=True)}")

# Cách 2: With attention mask
print("--- With Attention Mask ---")
inputs = tokenizer(text, return_tensors="pt", max_length=128, truncation=True).to(device)
outputs2 = model.generate(
    input_ids=inputs.input_ids, 
    attention_mask=inputs.attention_mask,
    decoder_start_token_id=tokenizer.lang_code_to_id["vi_VN"], 
    num_beams=5, 
    max_length=128
)
print(f"Decoded 2: {tokenizer.decode(outputs2[0], skip_special_tokens=True)}")
