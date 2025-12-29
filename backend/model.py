import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import get_peft_model, LoraConfig, TaskType


def print_trainable_parameters(model):
    """
    In ra số lượng tham số có thể được tinh chỉnh (trainable) của model
    """
    trainable_params = 0
    all_param = 0
    for _, param in model.named_parameters():
        all_param += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()
    print(
        f"Trainable params: {trainable_params} || All params: {all_param}\nTrainable%: {100 * trainable_params / all_param}"
    )


def get_model_and_tokenizer(model_name):
    """
    Load tokenizer và model (với cấu hình LoRA)
    """
    print(f"Loading model: {model_name}")
    
    # 1. Load Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # 2. Load Model
    # Load model với fp16 (cho P100)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_name, 
        device_map="auto",
        dtype=torch.float16
    )
    
    # peft = Parameter Efficient Fine-Tuning
    peft_config = LoraConfig(
        task_type=TaskType.SEQ_2_SEQ_LM, 
        inference_mode=False, 
        r=32,           # Tăng Rank lên 32 để học sâu hơn
        lora_alpha=64,  # Alpha = 2 * r
        lora_dropout=0.1,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj"] # Finetune toàn bộ Attention
    )

    model = get_peft_model(model, peft_config)
    print_trainable_parameters(model)
    
    return model, tokenizer
