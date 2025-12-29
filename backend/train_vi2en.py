import os
from finetuning import run_finetuning

# --- CẤU HÌNH ---
MODEL_NAME = "vinai/vinai-translate-vi2en"
OUTPUT_DIR = "/kaggle/working/lora-vinai-vi2en" if os.path.exists("/kaggle/working") else "./lora-vinai-vi2en"

if __name__ == "__main__":
    run_finetuning(
        model_name=MODEL_NAME,
        output_dir=OUTPUT_DIR,
        source_lang="vi",
        target_lang="en",
        dataset_name="Helsinki-NLP/opus-100",
        dataset_config="vi-en"
    )
