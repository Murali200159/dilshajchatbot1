import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    pipeline,
    logging,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer
import fire

def train(
    # Model arguments
    base_model_name: str = "meta-llama/Meta-Llama-3-8B-Instruct",
    new_model_name: str = "llama-3-8b-dilshaj-finetuned",
    
    # Dataset arguments
    dataset_path: str = "dataset.json", # Path to local JSON/JSONL file
    dataset_text_field: str = "text",
    
    # Training arguments
    output_dir: str = "models/finetuned",
    num_train_epochs: int = 1,
    per_device_train_batch_size: int = 4,
    gradient_accumulation_steps: int = 1,
    learning_rate: float = 2e-4,
    weight_decay: float = 0.001,
    fp16: bool = False,
    bf16: bool = False, 
    max_grad_norm: float = 0.3,
    max_steps: int = -1,
    warmup_ratio: float = 0.03,
    group_by_length: bool = True,
    lr_scheduler_type: str = "constant",
    
    # LoRA arguments
    lora_alpha: int = 16,
    lora_dropout: float = 0.1,
    lora_r: int = 64,
    lora_bias: str = "none",
    
    # SFT arguments
    max_seq_length: int = None,
    packing: bool = False,
):
    """
    Fine-tune a LLaMA model using QLoRA and save adapters to models/finetuned/.
    """
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Determine final save path for the adapter
    final_save_path = os.path.join(output_dir, new_model_name)
    checkpoint_dir = os.path.join(output_dir, "checkpoints")

    print(f"Training Config:")
    print(f"  Base Model: {base_model_name}")
    print(f"  Dataset: {dataset_path}")
    print(f"  Output Adapter Path: {final_save_path}")

    # Detect hardware
    if torch.cuda.get_device_capability()[0] >= 8:
        print("Ampere GPU detected, enabling bf16")
        bf16 = True
        fp16 = False
    else:
        fp16 = True
        bf16 = False

    # QLoRA Configuration
    compute_dtype = getattr(torch, "float16")
    if bf16:
        compute_dtype = getattr(torch, "bfloat16")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=False,
    )

    # Load Model
    print("Loading Base Model...")
    model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        quantization_config=bnb_config,
        device_map="auto"
    )
    model.config.use_cache = False
    model.config.pretraining_tp = 1
    
    # Load Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right" 

    # Load LoRA Config
    peft_config = LoraConfig(
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        r=lora_r,
        bias=lora_bias,
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"] 
    )

    # Load Dataset
    print(f"Loading Dataset from {dataset_path}...")
    try:
        if not os.path.exists(dataset_path):
             print(f"Warning: {dataset_path} not found. Using dummy path for check...")
             # This path is just for structure, runtime will fail if file not found earlier
        
        extension = "json" if dataset_path.endswith(".json") else "json"
        dataset = load_dataset(extension, data_files=dataset_path, split="train")
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    # LLaMA 3 Prompt Formatting Function
    def formatting_prompts_func(examples):
        output_texts = []
        instructions = examples.get("instruction", [])
        inputs = examples.get("input", [])
        outputs = examples.get("output", [])
        
        # Handle case where input column might be missing or empty strings
        if not inputs: 
            inputs = [""] * len(instructions)
        
        for instruction, input_text, output in zip(instructions, inputs, outputs):
            # Combine instruction and input
            user_content = instruction
            if input_text:
                user_content += f"\nInput:\n{input_text}"
            
            # LLaMA 3 Special Tokens Format
            text = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{user_content}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n{output}<|eot_id|>"
            output_texts.append(text)
        return output_texts

    # Training Arguments
    training_arguments = TrainingArguments(
        output_dir=checkpoint_dir,
        num_train_epochs=num_train_epochs,
        per_device_train_batch_size=per_device_train_batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        optim="paged_adamw_32bit",
        save_steps=50,
        logging_steps=10,
        learning_rate=learning_rate,
        weight_decay=weight_decay,
        fp16=fp16,
        bf16=bf16,
        max_grad_norm=max_grad_norm,
        max_steps=max_steps,
        warmup_ratio=warmup_ratio,
        group_by_length=group_by_length,
        lr_scheduler_type=lr_scheduler_type,
        report_to="tensorboard"
    )

    # Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=peft_config,
        formatting_func=formatting_prompts_func,
        max_seq_length=max_seq_length,
        tokenizer=tokenizer,
        args=training_arguments,
        packing=packing,
    )

    print("Starting Training...")
    trainer.train()
    
    print(f"Saving Fine-Tuned Model Adapter to {final_save_path}...")
    trainer.model.save_pretrained(final_save_path)
    tokenizer.save_pretrained(final_save_path)
    
    print("Training Complete. Adapter saved.")

if __name__ == "__main__":
    fire.Fire(train)
