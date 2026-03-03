#!/usr/bin/env python3
"""
Run inference on new code samples using trained CodeT5 model.

This script provides:
1. Batch inference for multiple codes
2. Single code inference
3. Probability calibration
4. Confidence scoring
"""

import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Tuple

import torch
import numpy as np
from tqdm import tqdm

from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VulnerabilityPredictor:
    """Predict vulnerabilities in code using trained CodeT5 model"""
    
    def __init__(
        self,
        model_dir: str,
        max_length: int = 512,
        batch_size: int = 32,
        device: str = None,
        confidence_threshold: float = 0.5
    ):
        """
        Initialize predictor
        
        Args:
            model_dir: Directory with saved model
            max_length: Maximum sequence length
            batch_size: Batch size for inference
            device: Device to use ('cuda' or 'cpu')
            confidence_threshold: Threshold for vulnerability prediction
        """
        self.model_dir = model_dir
        self.max_length = max_length
        self.batch_size = batch_size
        self.confidence_threshold = confidence_threshold
        
        # Set device
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        logger.info(f"Using device: {self.device}")
        
        # Load model and tokenizer
        logger.info(f"Loading model from {model_dir}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        self.model.to(self.device)
        self.model.eval()
        
        logger.info("Model loaded successfully")
    
    def predict_code(self, code: str) -> Dict:
        """
        Predict vulnerability for a single code snippet
        
        Args:
            code: Code string to analyze
        
        Returns:
            Prediction result dictionary
        """
        return self.predict_batch([code])[0]
    
    def predict_batch(self, codes: List[str], show_progress: bool = True) -> List[Dict]:
        """
        Predict vulnerabilities for multiple code snippets
        
        Args:
            codes: List of code strings
            show_progress: Show progress bar
        
        Returns:
            List of prediction dictionaries
        """
        results = []
        
        # Process in batches
        iterator = tqdm(range(0, len(codes), self.batch_size)) if show_progress else range(0, len(codes), self.batch_size)
        
        for i in iterator:
            batch_codes = codes[i:i+self.batch_size]
            batch_results = self._predict_batch_internal(batch_codes)
            results.extend(batch_results)
        
        return results
    
    def _predict_batch_internal(self, codes: List[str]) -> List[Dict]:
        """Internal batch prediction"""
        
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
        
        # Process results
        results = []
        for code, logit in zip(codes, logits):
            # Get probabilities
            probs = self._softmax(logit)
            prob_non_vuln = float(probs[0])
            prob_vuln = float(probs[1])
            
            # Determine prediction
            pred_label = 1 if prob_vuln > self.confidence_threshold else 0
            
            result = {
                'code': code,
                'predicted_label': pred_label,
                'label_name': 'Vulnerable' if pred_label == 1 else 'Non-vulnerable',
                'confidence': max(prob_non_vuln, prob_vuln),
                'probability_vulnerable': prob_vuln,
                'probability_non_vulnerable': prob_non_vuln,
            }
            
            results.append(result)
        
        return results
    
    @staticmethod
    def _softmax(x: np.ndarray) -> np.ndarray:
        """Compute softmax"""
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum(axis=0)
    
    def predict_from_file(self, input_file: str, output_file: str = None) -> List[Dict]:
        """
        Predict on codes from JSON Lines file
        
        Args:
            input_file: Path to JSONL file with 'code' field
            output_file: Optional path to save results
        
        Returns:
            List of predictions
        """
        logger.info(f"Loading codes from {input_file}...")
        
        codes = []
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_idx, line in enumerate(f):
                try:
                    record = json.loads(line.strip())
                    codes.append(record['code'])
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to parse line {line_idx}: {e}")
        
        logger.info(f"Loaded {len(codes)} codes")
        
        # Predict
        results = self.predict_batch(codes)
        
        # Save if output file specified
        if output_file:
            logger.info(f"Saving predictions to {output_file}...")
            with open(output_file, 'w') as f:
                for result in results:
                    f.write(json.dumps(result) + '\n')
            logger.info(f"Saved {len(results)} predictions")
        
        return results
    
    def explain_prediction(self, code: str) -> Dict:
        """
        Get detailed explanation for prediction
        
        Args:
            code: Code to analyze
        
        Returns:
            Detailed prediction with explanation
        """
        prediction = self.predict_code(code)
        
        # Add explanation
        explanation = {
            **prediction,
            'explanation': self._create_explanation(prediction)
        }
        
        return explanation
    
    @staticmethod
    def _create_explanation(prediction: Dict) -> str:
        """Create human-readable explanation"""
        confidence = prediction['confidence']
        prob_vul = prediction['probability_vulnerable']
        label = prediction['label_name']
        
        if confidence < 0.6:
            confidence_level = "low confidence"
        elif confidence < 0.75:
            confidence_level = "moderate confidence"
        else:
            confidence_level = "high confidence"
        
        return (
            f"The model predicts this code is {label.lower()} with "
            f"{confidence_level} ({confidence:.1%}). "
            f"Probability of vulnerability: {prob_vul:.1%}"
        )


def interactive_mode(predictor: VulnerabilityPredictor):
    """Interactive prediction mode"""
    print("\nCodeT5 Vulnerability Predictor - Interactive Mode")
    print("=" * 60)
    print("Enter code snippets to analyze (type 'quit' to exit)")
    print("=" * 60 + "\n")
    
    while True:
        print("Enter code (type 'END' on a new line when done):")
        lines = []
        while True:
            line = input()
            if line == 'END':
                break
            lines.append(line)
        
        code = '\n'.join(lines)
        
        if code.lower() == 'quit':
            break
        
        if not code.strip():
            print("No code entered. Please try again.\n")
            continue
        
        # Predict
        result = predictor.explain_prediction(code)
        
        # Print result
        print("\n" + "=" * 60)
        print(f"Prediction: {result['label_name']}")
        print(f"Confidence: {result['confidence']:.1%}")
        print(f"Probability Vulnerable: {result['probability_vulnerable']:.1%}")
        print(f"Probability Non-vulnerable: {result['probability_non_vulnerable']:.1%}")
        print(f"Explanation: {result['explanation']}")
        print("=" * 60 + "\n")


def main():
    """Main inference function"""
    parser = argparse.ArgumentParser(description="Predict code vulnerabilities")
    
    parser.add_argument(
        '--model_dir',
        type=str,
        default='models/codet5_base_vuln_detector',
        help='Path to saved model'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['interactive', 'batch', 'file'],
        default='interactive',
        help='Inference mode'
    )
    parser.add_argument(
        '--input_file',
        type=str,
        help='Input JSONL file (for file mode)'
    )
    parser.add_argument(
        '--output_file',
        type=str,
        help='Output file for predictions'
    )
    parser.add_argument(
        '--code',
        type=str,
        help='Single code string to analyze (for batch mode)'
    )
    parser.add_argument(
        '--max_length',
        type=int,
        default=512,
        help='Maximum code length'
    )
    parser.add_argument(
        '--batch_size',
        type=int,
        default=32,
        help='Batch size'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.5,
        help='Confidence threshold for vulnerability'
    )
    parser.add_argument(
        '--device',
        type=str,
        default=None,
        help='Device to use (cuda or cpu)'
    )
    
    args = parser.parse_args()
    
    # Create predictor
    predictor = VulnerabilityPredictor(
        model_dir=args.model_dir,
        max_length=args.max_length,
        batch_size=args.batch_size,
        device=args.device,
        confidence_threshold=args.threshold
    )
    
    # Run based on mode
    if args.mode == 'interactive':
        interactive_mode(predictor)
    
    elif args.mode == 'batch' and args.code:
        result = predictor.explain_prediction(args.code)
        print(json.dumps(result, indent=2))
    
    elif args.mode == 'file' and args.input_file:
        predictor.predict_from_file(args.input_file, args.output_file)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
