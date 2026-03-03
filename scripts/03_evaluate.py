#!/usr/bin/env python3
"""
Evaluate CodeT5 model on test set.

This script:
1. Loads trained model
2. Runs inference on test set
3. Computes metrics (accuracy, F1, precision, recall)
4. Generates confusion matrix
5. Saves predictions
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import torch
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    roc_curve,
    auc,
    roc_auc_score
)

from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Evaluate vulnerability detection model"""
    
    def __init__(
        self,
        model_dir: str,
        test_data_path: str,
        output_dir: str = 'outputs/evaluation',
        max_length: int = 512,
        batch_size: int = 32,
        device: str = None
    ):
        """
        Initialize evaluator
        
        Args:
            model_dir: Directory with saved model
            test_data_path: Path to test data JSONL
            output_dir: Output directory for results
            max_length: Maximum sequence length
            batch_size: Batch size for inference
            device: Device to use ('cuda' or 'cpu')
        """
        self.model_dir = model_dir
        self.test_data_path = test_data_path
        self.output_dir = Path(output_dir)
        self.max_length = max_length
        self.batch_size = batch_size
        
        # Set device
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        logger.info(f"Using device: {self.device}")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load model and tokenizer
        logger.info(f"Loading model from {model_dir}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        self.model.to(self.device)
        self.model.eval()
        
        logger.info(f"Model loaded successfully")
    
    def load_test_data(self) -> List[Dict]:
        """Load test data from JSONL"""
        logger.info(f"Loading test data from {self.test_data_path}...")
        
        data = []
        with open(self.test_data_path, 'r', encoding='utf-8') as f:
            for line_idx, line in enumerate(f):
                try:
                    record = json.loads(line.strip())
                    data.append(record)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse line {line_idx}")
                    continue
        
        logger.info(f"Loaded {len(data)} test samples")
        return data
    
    def predict_batch(self, codes: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get predictions for a batch of code snippets
        
        Args:
            codes: List of code strings
        
        Returns:
            Tuple of (logits, predictions)
        """
        # Tokenize
        encoding = self.tokenizer(
            codes,
            max_length=self.max_length,
            truncation='max_length',
            padding='max_length',
            return_tensors='pt'
        )
        
        # Move to device
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        # Predict
        with torch.no_grad():
            outputs = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
        
        logits = outputs.logits.cpu().numpy()
        predictions = np.argmax(logits, axis=1)
        
        return logits, predictions
    
    def evaluate(self) -> Dict:
        """
        Run full evaluation
        
        Returns:
            Dictionary of metrics
        """
        logger.info("Starting evaluation...")
        
        # Load data
        test_data = self.load_test_data()
        
        # Get predictions
        all_logits = []
        all_predictions = []
        all_labels = []
        all_codes = []
        
        logger.info("Running inference...")
        
        for i in tqdm(range(0, len(test_data), self.batch_size)):
            batch = test_data[i:i+self.batch_size]
            codes = [r['code'] for r in batch]
            labels = [r['label'] for r in batch]
            
            logits, predictions = self.predict_batch(codes)
            
            all_logits.append(logits)
            all_predictions.append(predictions)
            all_labels.extend(labels)
            all_codes.extend(codes)
        
        # Concatenate
        all_logits = np.vstack(all_logits)
        all_predictions = np.concatenate(all_predictions)
        all_labels = np.array(all_labels)
        
        # Compute metrics
        metrics = self._compute_metrics(all_logits, all_predictions, all_labels)
        
        # Save results
        self._save_results(metrics, all_predictions, all_labels, all_codes, all_logits)
        
        return metrics
    
    def _compute_metrics(
        self,
        logits: np.ndarray,
        predictions: np.ndarray,
        labels: np.ndarray
    ) -> Dict:
        """Compute evaluation metrics"""
        
        metrics = {}
        
        # Basic metrics
        metrics['accuracy'] = accuracy_score(labels, predictions)
        metrics['precision'] = precision_score(labels, predictions, zero_division=0)
        metrics['recall'] = recall_score(labels, predictions, zero_division=0)
        metrics['f1'] = f1_score(labels, predictions, zero_division=0)
        
        # Get probability of positive class
        probs = np.softmax(logits, axis=1)[:, 1]
        
        # ROC-AUC
        try:
            metrics['roc_auc'] = roc_auc_score(labels, probs)
        except:
            metrics['roc_auc'] = None
        
        # Confusion matrix
        metrics['confusion_matrix'] = confusion_matrix(labels, predictions).tolist()
        
        # Per-class metrics
        report = classification_report(labels, predictions, output_dict=True, zero_division=0)
        metrics['classification_report'] = report
        
        # Log metrics
        logger.info("\n" + "="*60)
        logger.info("EVALUATION RESULTS")
        logger.info("="*60)
        logger.info(f"Accuracy:  {metrics['accuracy']:.4f}")
        logger.info(f"Precision: {metrics['precision']:.4f}")
        logger.info(f"Recall:    {metrics['recall']:.4f}")
        logger.info(f"F1 Score:  {metrics['f1']:.4f}")
        if metrics['roc_auc']:
            logger.info(f"ROC-AUC:   {metrics['roc_auc']:.4f}")
        logger.info("="*60 + "\n")
        
        # Detailed report
        logger.info("Classification Report:")
        logger.info(classification_report(labels, predictions, target_names=['Non-vulnerable', 'Vulnerable']))
        
        return metrics
    
    def _save_results(
        self,
        metrics: Dict,
        predictions: np.ndarray,
        labels: np.ndarray,
        codes: List[str],
        logits: np.ndarray
    ):
        """Save evaluation results"""
        
        # Save metrics as JSON
        metrics_path = self.output_dir / 'metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        logger.info(f"Metrics saved to {metrics_path}")
        
        # Save predictions
        predictions_path = self.output_dir / 'predictions.json'
        predictions_data = []
        for code, pred, label, logit in zip(codes, predictions, labels, logits):
            predictions_data.append({
                'code': code[:200],  # Truncate for readability
                'predicted_label': int(pred),
                'true_label': int(label),
                'predicted_prob_non_vul': float(logit[0]),
                'predicted_prob_vul': float(logit[1]),
                'correct': int(pred == label)
            })
        
        with open(predictions_path, 'w') as f:
            json.dump(predictions_data, f, indent=2)
        logger.info(f"Predictions saved to {predictions_path}")
        
        # Generate confusion matrix plot
        self._plot_confusion_matrix(metrics['confusion_matrix'])
        
        # Generate ROC curve
        probs = np.softmax(logits, axis=1)[:, 1]
        if metrics['roc_auc']:
            self._plot_roc_curve(labels, probs, metrics['roc_auc'])
    
    def _plot_confusion_matrix(self, cm: List[List[int]]):
        """Plot and save confusion matrix"""
        plt.figure(figsize=(8, 6))
        sns.heatmap(
            cm,
            annot=True,
            fmt='d',
            cmap='Blues',
            xticklabels=['Non-vulnerable', 'Vulnerable'],
            yticklabels=['Non-vulnerable', 'Vulnerable']
        )
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        
        cm_path = self.output_dir / 'confusion_matrix.png'
        plt.savefig(cm_path, dpi=300)
        logger.info(f"Confusion matrix saved to {cm_path}")
        plt.close()
    
    def _plot_roc_curve(self, labels: np.ndarray, probs: np.ndarray, auc_score: float):
        """Plot and save ROC curve"""
        fpr, tpr, _ = roc_curve(labels, probs)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {auc_score:.3f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random Classifier')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curve')
        plt.legend(loc="lower right")
        plt.tight_layout()
        
        roc_path = self.output_dir / 'roc_curve.png'
        plt.savefig(roc_path, dpi=300)
        logger.info(f"ROC curve saved to {roc_path}")
        plt.close()


def main():
    """Main evaluation function"""
    parser = argparse.ArgumentParser(description="Evaluate CodeT5 vulnerability detector")
    
    parser.add_argument('--model_dir', type=str, default='models/codet5_base_vuln_detector')
    parser.add_argument('--test_data', type=str, default='Data/processed/test.json')
    parser.add_argument('--output_dir', type=str, default='outputs/evaluation')
    parser.add_argument('--max_length', type=int, default=512)
    parser.add_argument('--batch_size', type=int, default=32)
    parser.add_argument('--device', type=str, default=None)
    
    args = parser.parse_args()
    
    # Create evaluator
    evaluator = ModelEvaluator(
        model_dir=args.model_dir,
        test_data_path=args.test_data,
        output_dir=args.output_dir,
        max_length=args.max_length,
        batch_size=args.batch_size,
        device=args.device
    )
    
    # Run evaluation
    metrics = evaluator.evaluate()
    
    logger.info(f"Evaluation results saved to {args.output_dir}")


if __name__ == '__main__':
    main()
