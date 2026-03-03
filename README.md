# CodeT5 Vulnerability Detection Fine-tuning

Complete, production-ready implementation for fine-tuning CodeT5 on the MegaVul dataset for binary vulnerability detection.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Start](#quick-start)
3. [Step-by-Step Execution](#step-by-step-execution)
4. [Configuration](#configuration)
5. [Troubleshooting](#troubleshooting)
6. [Results & Interpretation](#results--interpretation)

---

## System Requirements

### Hardware

| Component | Minimum | Recommended | Ideal |
|-----------|---------|-------------|-------|
| GPU RAM | 12GB | 24GB | 48GB+ |
| System RAM | 16GB | 32GB | 64GB+ |
| Disk Space | 50GB | 100GB | 200GB+ |
| CUDA Version | 11.8 | 12.1 | 12.1+ |
| GPU Model | RTX 3090 | RTX 4090 | A100, H100 |

### Software

- Python 3.9 - 3.11 (3.11 recommended)
- NVIDIA CUDA Toolkit 12.1
- cuDNN 8.9+
- Git

### GPUs Tested

✅ NVIDIA RTX 4080, RTX 4090  
✅ NVIDIA A100, A6000  
✅ NVIDIA V100, H100  
✅ NVIDIA RTX 3090, RTX 3080 Ti  

---

## Quick Start

### 1. Environment Setup (Windows)

```batch
# Run setup script
setup_environment.bat

# Activate environment
conda activate codet5_vul

# Verify installation
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
```

### 2. Prepare Data

```bash
conda activate codet5_vul
python scripts/01_preprocess.py \
    --raw_data Data/raw/megavul_simple.json \
    --output_dir Data/processed \
    --train_split 0.7 \
    --max_code_length 1024
```

### 3. Train Model

```bash
python scripts/02_train.py \
    --train_data Data/processed/train.json \
    --val_data Data/processed/val.json \
    --output_dir models/codet5_base_vuln_detector \
    --model_name Salesforce/codet5-base \
    --num_epochs 5 \
    --batch_size 16 \
    --learning_rate 2e-5
```

### 4. Evaluate

```bash
python scripts/03_evaluate.py \
    --model_dir models/codet5_base_vuln_detector \
    --test_data Data/processed/test.json \
    --output_dir outputs/evaluation
```

### 5. Run Inference

```bash
# Interactive mode
python scripts/04_inference.py --model_dir models/codet5_base_vuln_detector

# Or batch mode
python scripts/04_inference.py \
    --mode batch \
    --code "your code here" \
    --model_dir models/codet5_base_vuln_detector
```

---

## Step-by-Step Execution

### Step 1: Conda Environment Setup

#### Windows Users

```batch
REM Option A: Use provided script
setup_environment.bat

REM Option B: Manual setup
conda create -n codet5_vul python=3.11 -y
conda activate codet5_vul

REM Install PyTorch with CUDA 12.1
conda install pytorch pytorch-cuda=12.1 -c pytorch -c nvidia -y

REM Install dependencies
pip install -r requirements.txt
```

#### Linux/Mac Users

```bash
# Create environment
conda create -n codet5_vul python=3.11 -y
conda activate codet5_vul

# PyTorch
conda install pytorch pytorch-cuda=12.1 -c pytorch -c nvidia -y

# Dependencies
pip install -r requirements.txt
```

#### Verify Installation

```bash
python -c "import torch; print('CUDA Available:', torch.cuda.is_available())"
python -c "import transformers; print('Transformers version:', transformers.__version__)"
python -c "import datasets; print('Datasets version:', datasets.__version__)"
```

### Step 2: Download & Inspect Dataset

Your dataset is already available at: `Data/raw/megavul_simple.json`

**Dataset Statistics:**
- Format: Single JSON array
- Total Size: ~1.1 GB
- Expected Records: 10,000+ vulnerability instances
- Fields: code, vulnerability label, metadata (CVE, CWE, etc.)

### Step 3: Preprocess Dataset

This step converts raw MegaVul data into train/val/test splits.

```bash
python scripts/01_preprocess.py \
    --raw_data Data/raw/megavul_simple.json \
    --output_dir Data/processed \
    --train_split 0.7 \
    --val_split 0.15 \
    --seed 42 \
    --max_code_length 1024 \
    --min_code_length 10
```

**Parameters:**
- `raw_data`: Path to megavul_simple.json
- `output_dir`: Output directory for processed data
- `train_split`: Ratio of training data (0.7 = 70%)
- `val_split`: Ratio of validation data (0.15 = 15%)
- `max_code_length`: Maximum code snippet length (chars)
- `min_code_length`: Minimum code snippet length (chars)
- `seed`: Random seed for reproducibility

**Output:**
```
Data/processed/
├── train.json          (70% of data, JSONL format)
├── val.json            (15% of data, JSONL format)
├── test.json           (15% of data, JSONL format)
└── dataset_info.txt    (Statistics and analysis)
```

**Expected Numbers (approximate):**
- Train samples: ~7,000-10,000
- Val samples: ~1,500-2,000
- Test samples: ~1,500-2,000
- Vulnerable ratio: ~30-40%

### Step 4: Model Fine-Tuning

#### Single GPU Training

```bash
python scripts/02_train.py \
    --train_data Data/processed/train.json \
    --val_data Data/processed/val.json \
    --output_dir models/codet5_base_vuln_detector \
    --model_name Salesforce/codet5-base \
    --batch_size 16 \
    --eval_batch_size 32 \
    --num_epochs 5 \
    --learning_rate 2e-5 \
    --warmup_steps 500 \
    --weight_decay 0.01 \
    --max_length 512 \
    --seed 42 \
    --use_early_stopping
```

#### Multi-GPU Training (2+ GPUs)

```bash
# Configure accelerate (one-time setup)
accelerate config

# Launch training
accelerate launch scripts/02_train.py \
    --train_data Data/processed/train.json \
    --val_data Data/processed/val.json \
    --output_dir models/codet5_base_vuln_detector \
    --batch_size 16 \
    --num_epochs 5
```

**Training Parameters Explained:**

| Parameter | Default | Notes |
|-----------|---------|-------|
| batch_size | 16 | Reduce if OOM; increase if GPU memory available (24, 32) |
| learning_rate | 2e-5 | Standard for fine-tuning; range: 1e-5 to 5e-5 |
| num_epochs | 5 | Usually sufficient; can go up to 10 for better performance |
| warmup_steps | 500 | Gradual LR increase at start |
| weight_decay | 0.01 | L2 regularization |
| max_length | 512 | CodeT5 context window |
| eval_steps | 500 | Evaluate every N steps |
| save_steps | 500 | Save checkpoint every N steps |

**Expected Training Time:**
- Single GPU (RTX 4090): ~2-4 hours
- Multi-GPU (2x RTX 4090): ~1-2 hours
- Single GPU (RTX 3090): ~4-6 hours

**Output:**
```
models/codet5_base_vuln_detector/
├── pytorch_model.bin         (Model weights)
├── config.json               (Model config)
├── tokenizer.json            (Tokenizer)
├── special_tokens_map.json   (Special tokens)
├── training_args.bin         (Training config)
├── logs/                      (TensorBoard logs)
├── checkpoint-500/           (Intermediate checkpoints)
└── training_results.json     (Training metrics)
```

**Monitor Training:**

```bash
# Open TensorBoard
tensorboard --logdir models/codet5_base_vuln_detector/logs

# Open in browser
http://localhost:6006
```

### Step 5: Model Evaluation

Run comprehensive evaluation on test set:

```bash
python scripts/03_evaluate.py \
    --model_dir models/codet5_base_vuln_detector \
    --test_data Data/processed/test.json \
    --output_dir outputs/evaluation \
    --batch_size 32 \
    --max_length 512
```

**Output:**
```
outputs/evaluation/
├── metrics.json              (All metrics)
├── predictions.json          (Per-sample predictions)
├── confusion_matrix.png      (Visualization)
└── roc_curve.png            (ROC curve)
```

**Expected Metrics:**
- Accuracy: 75-85%
- F1 Score: 70-80%
- Precision: 70-80%
- Recall: 70-85%
- ROC-AUC: 80-90%

### Step 6: Inference on New Code

#### Interactive Mode

```bash
python scripts/04_inference.py \
    --model_dir models/codet5_base_vuln_detector \
    --mode interactive
```

Then paste code when prompted:
```
Enter code (type 'END' on a new line when done):
    def vulnerable_function(data):
        buffer = [0] * 10
        for i in range(len(data)):  # Buffer overflow!
            buffer[i] = data[i]
        return buffer
END

Prediction: Vulnerable
Confidence: 87.3%
Probability Vulnerable: 87.3%
...
```

#### Batch Prediction

```bash
python scripts/04_inference.py \
    --model_dir models/codet5_base_vuln_detector \
    --mode batch \
    --code "def foo(): pass"
```

#### File-based Prediction

Create `codes_to_test.json`:
```json
{"code": "def vulnerable_func():\n    ..."}
{"code": "def safe_func():\n    ..."}
```

Then run:
```bash
python scripts/04_inference.py \
    --model_dir models/codet5_base_vuln_detector \
    --mode file \
    --input_file codes_to_test.json \
    --output_file predictions.json
```

---

## Configuration

### Model Selection

**CodeT5 Variants:**

```
Salesforce/codet5-base              # 250M params - RECOMMENDED (balanced)
Salesforce/codet5-large            # 774M params - Better performance, more VRAM
Salesforce/codet5-small            # 60M params - Faster, lower accuracy
Salesforce/codet5-small-multitask  # 60M params - Pre-trained on multiple tasks
```

### Hyperparameter Tuning

**For Better Performance:**
```python
learning_rate: 2e-5 -> 1e-5  # More conservative
num_epochs: 5 -> 10           # Longer training
warmup_steps: 500 -> 1000     # Longer warmup
batch_size: 16 -> 24/32       # Larger batches
```

**For Faster Training:**
```python
batch_size: 16 -> 8           # Fit more in training loop
num_epochs: 5 -> 3            # Less iterations
eval_steps: 500 -> 2000       # Less frequent eval
save_steps: 500 -> 2000       # Less checkpoints
```

---

## Common Errors & Fixes

### Error 1: Out of Memory (OOM)

```
RuntimeError: CUDA out of memory
```

**Fix:**
```bash
# Reduce batch size
python scripts/02_train.py --batch_size 8

# Reduce max_length
python scripts/02_train.py --max_length 384

# Enable gradient accumulation
python scripts/02_train.py \
    --batch_size 4 \
    --gradient_accumulation_steps 4
```

### Error 2: Model Not Found

```
OSError: Can't load 'Salesforce/codet5-base'
```

**Fix:**
```bash
# Ensure HuggingFace Hub access
huggingface-cli login
# Enter your HuggingFace token

# Or download manually
python -c "from transformers import AutoModel; AutoModel.from_pretrained('Salesforce/codet5-base')"
```

### Error 3: JSON Decode Error During Preprocessing

**Fix:**
```bash
# Verify JSON file
python -c "import json; json.load(open('Data/raw/megavul_simple.json'))"

# If error, the file might be corrupted. Re-download from:
# https://github.com/ZeoVan/MegaVul
```

### Error 4: CUDA Not Available

```
AssertionError: CUDA is not available
```

**Fix:**
```bash
# Check NVIDIA Driver
nvidia-smi

# Reinstall PyTorch with correct CUDA
conda install pytorch pytorch-cuda=12.1 -c pytorch -c nvidia -y
```

### Error 5: Insufficient Disk Space

**Fix:**
```bash
# Monitor disk usage
du -sh Data/ models/ outputs/

# Clear old checkpoints
rm -rf models/codet5_base_vuln_detector/checkpoint-*

# Clean pip cache
pip cache purge
```

---

## Results & Interpretation

### Understanding Metrics

**Accuracy:** Percentage of correct predictions
- High accuracy ≠ good model (if classes imbalanced)
- Formula: (TP + TN) / (TP + TN + FP + FN)

**Precision:** Of predicted vulnerabilities, how many are correct?
- Focus on reducing false positives
- Formula: TP / (TP + FP)

**Recall:** Of actual vulnerabilities, how many are found?
- Focus on reducing false negatives
- Formula: TP / (TP + FN)

**F1 Score:** Harmonic mean of precision and recall
- Balanced metric for imbalanced datasets
- Formula: 2 × (Precision × Recall) / (Precision + Recall)

**ROC-AUC:** Area under ROC curve
- 0.5 = random, 1.0 = perfect
- Best for comparing models

### Confusion Matrix

```
              Predicted
              Non-Vul  Vul
Actual  Non-Vul   TN    FP
        Vul       FN    TP
```

- **True Positives (TP):** Correctly identified vulnerabilities
- **False Positives (FP):** Non-vulnerable code marked as vulnerable
- **True Negatives (TN):** Correctly identified non-vulnerable code
- **False Negatives (FN):** Vulnerabilities missed

### Interpreting Predictions

```json
{
  "predicted_label": 1,
  "label_name": "Vulnerable",
  "confidence": 0.873,
  "probability_vulnerable": 0.873,
  "probability_non_vulnerable": 0.127
}
```

- **Confidence < 60%:** Low confidence, uncertain prediction
- **Confidence 60-75%:** Moderate confidence
- **Confidence > 75%:** High confidence

### Next Steps for Production Deployment

1. **Ensemble with Other Models**
   - Combine with binary (Model 1 & 2) predictions
   - Use voting or weighted average

2. **CWE Classification**
   - Fine-tune separate CodeT5 model on CWE labels
   - Use best CWE predictions alongside vulnerability detection

3. **Code Localization**
   - Use attention weights to highlight vulnerable sections
   - Combine with line-level analysis

4. **Fix Generation**
   - Train CodeT5 encoder-decoder model
   - Fine-tune on code-to-fixed-code pairs from MegaVul

5. **Web API Integration**
   - Wrap model in Flask/FastAPI
   - Deploy using Docker
   - Add rate limiting and caching

---

## Logs & Debugging

### Check Training Progress

```bash
# View TensorBoard
tensorboard --logdir models/codet5_base_vuln_detector/logs

# View training results
cat models/codet5_base_vuln_detector/training_results.json | python -m json.tool
```

### Common Log Messages

```
[INFO] Loaded 10000 records from Data/raw/megavul_simple.json
[INFO] Train: 7000 (70.0%), Val: 1500 (15.0%), Test: 1500 (15.0%)
[INFO] Loading model from Salesforce/codet5-base
[INFO] Starting training...
[INFO] ...Step 500/2800 (Training loss: 0.45, Eval F1: 0.78)
```

---

## Success Criteria

✅ Preprocessing completes without errors  
✅ Model trains without OOM errors  
✅ Training loss decreases over epochs  
✅ F1 score > 70% on test set  
✅ Can run inference on new code samples  

---

## Citation

If you use this implementation, please cite:

```bibtex
@article{wang2023codet5,
  title={CodeT5: Identifier-aware Unified Pre-trained Encoder-Decoder Models for Code Understanding and Generation},
  author={Wang, Yue and Wang, Weishi and Joty, Shafiq and others},
  journal={arXiv:2109.00859},
  year={2021}
}

@article{fan2023megavul,
  title={MegaVul: A Mega-scale Vulnerability Code Dataset from GitHub},
  author={Fan, Yayun and others},
  journal={arXiv:2310.07609},
  year={2023}
}
```

---

## Support & Documentation

- **HuggingFace Transformers:** https://huggingface.co/docs/transformers
- **CodeT5 Model Card:** https://huggingface.co/Salesforce/codet5-base
- **MegaVul Repository:** https://github.com/ZeoVan/MegaVul
- **Accelerate Documentation:** https://huggingface.co/docs/accelerate

---

**Last Updated:** March 2026  
**Status:** Production Ready ✅
