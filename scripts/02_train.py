#!/usr/bin/env python3
"""
Fine-tune CodeT5 on MegaVul dataset for vulnerability detection.

This script:
1. Loads preprocessed data
2. Tokenizes code sequences
3. Fine-tunes CodeT5 model
4. Saves checkpoints and best model
5. Logs training metrics
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List
import random

import torch
import numpy as np
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback,
    set_seed
)
from datasets import load_dataset
import evaluate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CodeVulnerabilityDataset(Dataset):
    """Custom dataset for code vulnerability detection"""
    
    def __init__(
        self,
        data_path: str,
        tokenizer,
        max_length: int = 512,
        truncation: str = 'max_length'
    ):
        """
        Initialize dataset
        
        Args:
            data_path: Path to JSONL data file
            tokenizer: HuggingFace tokenizer
            max_length: Maximum sequence length
            truncation: Truncation strategy
        """
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.truncation = truncation
        
        # Load data
        self.data = []
        logger.info(f"Loading data from {data_path}...")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            for line_idx, line in enumerate(f):
                try:
                    record = json.loads(line.strip())
                    self.data.append(record)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse line {line_idx}: {e}")
                    continue
        
        logger.info(f"Loaded {len(self.data)} records from {data_path}")
        
        # Count labels
        vulnerable_count = sum(1 for r in self.data if r['label'] == 1)
        logger.info(f"Label distribution: {vulnerable_count} vulnerable, {len(self.data) - vulnerable_count} non-vulnerable")
    
    def __len__(self) -> int:
        """Return dataset size"""
        return len(self.data)
    
    def __getitem__(self, idx: int) -> Dict:
        """Get single sample"""
        record = self.data[idx]
        code = record['code']
        label = record['label']
        
        # Tokenize
        encoding = self.tokenizer(
            code,
            max_length=self.max_length,
            truncation=self.truncation,
            padding='max_length',
            return_tensors='pt'
        )
        
        # Remove batch dimension
        item = {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'labels': torch.tensor(label, dtype=torch.long)
        }
        
        # Add token_type_ids if available
        if 'token_type_ids' in encoding:
            item['token_type_ids'] = encoding['token_type_ids'].squeeze(0)
        
        return item


def compute_metrics(eval_pred):
    """
    Compute evaluation metrics
    
    Args:
        eval_pred: Predictions and labels from trainer
    
    Returns:
        Dictionary of metrics
    """
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    
    # Load metrics
    accuracy = evaluate.load('accuracy')
    f1 = evaluate.load('f1')
    precision = evaluate.load('precision')
    recall = evaluate.load('recall')
    
    # Compute metrics
    acc = accuracy.compute(predictions=predictions, references=labels)
    f1_score = f1.compute(predictions=predictions, references=labels, average='binary')
    prec = precision.compute(predictions=predictions, references=labels, average='binary')
    rec = recall.compute(predictions=predictions, references=labels, average='binary')
    
    return {
        'accuracy': acc['accuracy'],
        'f1': f1_score['f1'],
        'precision': prec['precision'],
        'recall': rec['recall']
    }


def setup_deterministic(seed: int = 42):
    """Set up deterministic training"""
    set_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    
    logger.info(f"Set random seed to {seed}")


def main():
    """Main training function"""
    parser = argparse.ArgumentParser(description="Fine-tune CodeT5 for vulnerability detection")
    
    # Data arguments
    parser.add_argument('--train_data', type=str, default='Data/processed/train.json')
    parser.add_argument('--val_data', type=str, default='Data/processed/val.json')
    parser.add_argument('--output_dir', type=str, default='models/codet5_base_vuln_detector')
    
    # Model arguments
    parser.add_argument(
        '--model_name',
        type=str,
        default='Salesforce/codet5-base',
        help='Model identifier from HuggingFace Hub'
    )
    parser.add_argument('--max_length', type=int, default=512)
    
    # Training arguments
    parser.add_argument('--batch_size', type=int, default=16)
    parser.add_argument('--eval_batch_size', type=int, default=32)
    parser.add_argument('--num_epochs', type=int, default=5)
    parser.add_argument('--learning_rate', type=float, default=2e-5)
    parser.add_argument('--warmup_steps', type=int, default=500)
    parser.add_argument('--weight_decay', type=float, default=0.01)
    parser.add_argument('--gradient_accumulation_steps', type=int, default=2)
    parser.add_argument('--max_grad_norm', type=float, default=1.0)
    
    # Other arguments
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--save_strategy', type=str, default='steps', choices=['steps', 'epoch'])
    parser.add_argument('--save_steps', type=int, default=500)
    parser.add_argument('--eval_steps', type=int, default=500)
    parser.add_argument('--logging_steps', type=int, default=100)
    parser.add_argument('--use_early_stopping', action='store_true', default=True)
    parser.add_argument('--early_stopping_patience', type=int, default=3)
    parser.add_argument('--early_stopping_threshold', type=float, default=0.001)
    
    args = parser.parse_args()
    
    # Set up deterministic training
    setup_deterministic(args.seed)
    
    # Check CUDA availability
    if torch.cuda.is_available():
        logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"Device count: {torch.cuda.device_count()}")
    else:
        logger.warning("CUDA not available. Training will be slow on CPU.")
    
    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load model and tokenizer
    logger.info(f"Loading model: {args.model_name}")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=2,
        hidden_dropout_prob=0.1,
        attention_probs_dropout_prob=0.1
    )
    
    logger.info(f"Model loaded: {model.config.model_type}")
    logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Load datasets
    logger.info("Loading datasets...")
    train_dataset = CodeVulnerabilityDataset(
        args.train_data,
        tokenizer,
        max_length=args.max_length
    )
    val_dataset = CodeVulnerabilityDataset(
        args.val_data,
        tokenizer,
        max_length=args.max_length
    )
    
    logger.info(f"Train dataset: {len(train_dataset)} samples")
    logger.info(f"Val dataset: {len(val_dataset)} samples")
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        overwrite_output_dir=True,
        
        # Training parameters
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        num_train_epochs=args.num_epochs,
        learning_rate=args.learning_rate,
        lr_scheduler_type='linear',
        warmup_steps=args.warmup_steps,
        weight_decay=args.weight_decay,
        max_grad_norm=args.max_grad_norm,
        
        # Evaluation and logging
        evaluation_strategy='steps',
        eval_steps=args.eval_steps,
        save_strategy=args.save_strategy,
        save_steps=args.save_steps,
        logging_steps=args.logging_steps,
        logging_dir=os.path.join(args.output_dir, 'logs'),
        
        # Optimization
        optim='adamw_torch',
        adam_beta1=0.9,
        adam_beta2=0.999,
        adam_epsilon=1e-8,
        
        # Save and load
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model='f1',
        greater_is_better=True,
        
        # Device
        fp16=torch.cuda.is_available(),
        seeds=args.seed,
        dataloader_pin_memory=True,
        dataloader_num_workers=4,
        
        # Report
        report_to=['wandb', 'tensorboard'],
        push_to_hub=False,
        hub_private_repo=True
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        callbacks=[
            EarlyStoppingCallback(
                early_stopping_patience=args.early_stopping_patience,
                early_stopping_threshold=args.early_stopping_threshold
            ) if args.use_early_stopping else None
        ]
    )
    
    # Remove None callbacks
    trainer.remove_callback([None])
    
    # Train
    logger.info("Starting training...")
    logger.info(f"Output directory: {args.output_dir}")
    
    train_result = trainer.train()
    
    # Save final model
    logger.info(f"Saving final model to {args.output_dir}...")
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    
    # Save training results
    training_results_path = os.path.join(args.output_dir, 'training_results.json')
    with open(training_results_path, 'w') as f:
        json.dump(train_result.metrics, f, indent=2)
    
    logger.info(f"Training results saved to {training_results_path}")
    logger.info("Training complete!")
    
    return args.output_dir


if __name__ == '__main__':
    main()
