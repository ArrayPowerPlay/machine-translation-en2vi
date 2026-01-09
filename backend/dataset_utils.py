from datasets import load_dataset
import os


def load_and_preprocess_data(
    dataset_path, 
    dataset_name, 
    dataset_config, 
    tokenizer, 
    max_length, 
    source_lang, 
    target_lang
): 
    """Tải dataset, chia tập train/test và tiền xử lý (tokenize)"""
    if dataset_path and os.path.exists(dataset_path):
        print(f"Loading dataset from {dataset_path}...")
        if dataset_path.endswith('.json'):
            dataset_dict = load_dataset("json", data_files=dataset_path)
        else:
            dataset_dict = load_dataset("csv", data_files=dataset_path)
        dataset = dataset_dict[list(dataset_dict.keys())[0]]
    else:
        print(f"Using dataset {dataset_name} config {dataset_config}...")
        dataset = load_dataset(dataset_name, dataset_config, split="train") 
        if len(dataset) > 400000:
            dataset = dataset.select(range(400000))   
            
    print(f"Dataset size: {len(dataset)}")

    # Chia train/val
    dataset_split = dataset.train_test_split(test_size=0.1)
    train_dataset = dataset_split["train"]
    eval_dataset = dataset_split["test"]

    # Mapping ngôn ngữ cho mBART
    LANG_CODE_MAP = {
        "en": "en_XX",
        "vi": "vi_VN"
    }

    def preprocess_function(examples):
        inputs = []
        targets = []
        
        # Kiểm tra cấu trúc dữ liệu
        if "translation" in examples:
            inputs = [ex[source_lang] for ex in examples["translation"]]
            targets = [ex[target_lang] for ex in examples["translation"]]
        else:
            inputs = examples[source_lang]
            targets = examples[target_lang]

        # Lấy mã ngôn ngữ
        source_code = LANG_CODE_MAP.get(source_lang, "en_XX")
        target_code = LANG_CODE_MAP.get(target_lang, "vi_VN")
        
        # Thiết lập mã ngôn ngữ nguồn và đích
        tokenizer.src_lang = source_code
        tokenizer.tgt_lang = target_code
        
        # Tokenize input và output
        model_inputs = tokenizer(inputs, text_target=targets, max_length=max_length, truncation=True)
        
        return model_inputs

    print("Preprocessing dataset...")
    tokenized_train = train_dataset.map(preprocess_function, batched=True, remove_columns=train_dataset.column_names)
    tokenized_eval = eval_dataset.map(preprocess_function, batched=True, remove_columns=eval_dataset.column_names)
    # Output sau khi tokenize
    # {
    #     'input_ids': [...],
    #     'attention_mask': [...],
    #     'labels': [...]
    # }
    
    return tokenized_train, tokenized_eval
