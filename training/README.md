# Fine-Tuning LLaMA with LoRA for Ollama

This directory contains scripts to fine-tune LLaMA models (e.g., Llama 3) using Low-Rank Adaptation (LoRA) and export them for use with Ollama.

## Prerequisites

1.  **NVIDIA GPU**: Required for training (8GB+ VRAM recommended for 7B/8B models with 4-bit quantization).
2.  (Optional) **WSL 2**: Recommended for Windows users to avoid compatibility issues with `bitsandbytes`.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### 1. Prepare Dataset
Prepare a JSONL file with your training data. Format should generally match what `SFTTrainer` expects (e.g., a "text" field).

Example `dataset.jsonl`:
```json
{"text": "Q: What is the capital of France? A: Paris."}
{"text": "Q: Who is the CEO of Dilshaj Infotech? A: Mr. Dils."}
```

### 2. Run Training
Run the `train_lora.py` script. You can override defaults via command line arguments.

```bash
python train_lora.py \
  --base_model_name "meta-llama/Meta-Llama-3-8B-Instruct" \
  --dataset_name "dataset.jsonl" \
  --new_model_name "llama-3-8b-dilshaj-adapter" \
  --num_train_epochs 3
```

### 3. Merge and Export to GGUF (For Ollama)
To use the fine-tuned model in Ollama, you must merge the LoRA adapter with the base model and convert it to GGUF format.

**Recommended Tool**: `llama.cpp`

1.  **Merge Adapter**: You can use a script (often provided by `peft` or custom) to merge the adapter back into the base model.
    PRO TIP: Use `unsloth` or `merge_kit` for easier merging if possible.
    
    *Example merge script (pseudo-code):*
    ```python
    from peft import PeftModel
    from transformers import AutoModelForCausalLM
    base = AutoModelForCausalLM.from_pretrained("base_model")
    model = PeftModel.from_pretrained(base, "llama-3-8b-dilshaj-adapter")
    model = model.merge_and_unload()
    model.save_pretrained("merged_model")
    ```

2.  **Convert to GGUF**:
    Clone `llama.cpp`:
    ```bash
    git clone https://github.com/ggerganov/llama.cpp
    cd llama.cpp
    pip install -r requirements.txt
    python convert.py ../merged_model --outfile dilshaj-model.gguf --outtype f16
    ```

3.  **Quantize (Optional but recommended)**:
    ```bash
    ./quantize dilshaj-model.gguf dilshaj-model-q4_k_m.gguf q4_k_m
    ```

4.  **Import to Ollama**:
    Create a `Modelfile`:
    ```dockerfile
    FROM ./dilshaj-model-q4_k_m.gguf
    ```
    Run:
    ```bash
    ollama create dilshaj-ai -f Modelfile
    ```

## Notes for Windows Users
- If you encounter errors with `bitsandbytes`, try installing the Windows-specific wheel:
  `pip install bitsandbytes-windows` OR use WSL 2.
- Ensure CUDA toolkit is installed.
