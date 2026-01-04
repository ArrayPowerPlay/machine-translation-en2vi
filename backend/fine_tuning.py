# pyright: reportOptionalMemberAccess=false
from transformers import (
    Seq2SeqTrainingArguments, 
    Seq2SeqTrainer,
    DataCollatorForSeq2Seq
)
import matplotlib.pyplot as plt
from model import get_model_and_tokenizer
from dataset_utils import load_and_preprocess_data


def run_finetuning(
    model_name, 
    output_dir, 
    source_lang, 
    target_lang,
    dataset_path=None,
    dataset_name="Helsinki-NLP/opus-100", 
    dataset_config="en-vi",
    max_length=128,
    batch_size=16,
    grad_accumulation=2,
    num_epochs=3,
    learning_rate=2e-4
):
    
    # 1 & 2 & 3. Load Model & Tokenizer & LoRA Config
    model, tokenizer = get_model_and_tokenizer(model_name)

    # Set forced_bos_token_id for mBART evaluation
    # mBART needs this to know which language to generate during evaluation
    lang_code_map = {
        "en": "en_XX",
        "vi": "vi_VN"
    }
    # target_lang (en or vi) -> mapped code -> token id
    target_code = lang_code_map.get(target_lang, "vi_VN")
    model.config.forced_bos_token_id = tokenizer.lang_code_to_id[target_code]  # type: ignore
    print(f"Forced BOS token ID for evaluation set to: {model.config.forced_bos_token_id} ({target_code})")

    # 4. Chuẩn bị dữ liệu
    tokenized_train, tokenized_eval = load_and_preprocess_data(  # type: ignore
        dataset_path, 
        dataset_name, 
        dataset_config, 
        tokenizer, 
        max_length, 
        source_lang, 
        target_lang
    )

    # 5. Training Arguments
    args = Seq2SeqTrainingArguments(
        output_dir=output_dir,
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        weight_decay=0.01,
        save_total_limit=1,
        num_train_epochs=num_epochs,
        predict_with_generate=True,
        fp16=True,       # Dùng 16-bit để lưu và tính toán số thập phân
        gradient_accumulation_steps=grad_accumulation,
        logging_dir=f"{output_dir}/logs",
        logging_steps=100,
        eval_strategy="steps",
        eval_steps=500,
        save_strategy="steps",
        save_steps=500,
        load_best_model_at_end=True,
        report_to="none", # Tắt WandB
    )

    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

    # 6. Initialize Trainer
    trainer = Seq2SeqTrainer(
        model=model,
        args=args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_eval,
        data_collator=data_collator,
    )

    # 7. Train
    print("Starting training...")
    trainer.train()

    # 7.5 Plot Loss
    log_history = trainer.state.log_history
    train_steps = []
    train_loss = []
    eval_steps = []
    eval_loss = []

    for log in log_history:
        if "loss" in log:
            train_steps.append(log["step"])
            train_loss.append(log["loss"])
        if "eval_loss" in log:
            eval_steps.append(log["step"])
            eval_loss.append(log["eval_loss"])

    plt.figure(figsize=(10, 6))
    if train_loss:
        plt.plot(train_steps, train_loss, label="Training Loss")
    if eval_loss:
        plt.plot(eval_steps, eval_loss, label="Validation Loss")
    
    plt.xlabel("Steps")
    plt.ylabel("Loss")
    plt.title("Training & Validation Loss")
    plt.legend()
    plt.grid()
    plt.savefig(f"{output_dir}/loss_chart.png")
    print(f"Loss chart saved to {output_dir}/loss_chart.png")

    # 8. Save Model & Tokenizer
    print(f"Saving LoRA adapter and tokenizer to {output_dir}")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
