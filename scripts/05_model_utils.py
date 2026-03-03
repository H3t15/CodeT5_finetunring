#!/usr/bin/env python3
"""
Utility script for model management.

Includes:
1. Push model to HuggingFace Hub
2. Convert to ONNX format
3. Model size analysis
4. Benchmark inference speed
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import time

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelManager:
    """Manage trained model operations"""
    
    def __init__(self, model_dir: str):
        """Initialize model manager"""
        self.model_dir = Path(model_dir)
        
        logger.info(f"Loading model from {model_dir}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        
        logger.info("Model loaded successfully")
    
    def analyze_model(self):
        """Analyze model architecture and size"""
        
        logger.info("\n" + "="*60)
        logger.info("MODEL ANALYSIS")
        logger.info("="*60)
        
        # Parameter count
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        
        logger.info(f"Total Parameters: {total_params:,}")
        logger.info(f"Trainable Parameters: {trainable_params:,}")
        logger.info(f"Model Type: {self.model.config.model_type}")
        logger.info(f"Hidden Size: {self.model.config.hidden_size}")
        logger.info(f"Num Attention Heads: {self.model.config.num_attention_heads}")
        logger.info(f"Num Hidden Layers: {self.model.config.num_hidden_layers}")
        
        # Model size on disk
        model_size = sum(os.path.getsize(self.model_dir / f) 
                        for f in os.listdir(self.model_dir) 
                        if f.endswith('.bin'))
        
        logger.info(f"\nModel Size on Disk: {model_size / (1024**3):.2f} GB")
        
        # Memory footprint
        model_bytes = total_params * 4  # 32-bit parameters
        logger.info(f"Memory Footprint (FP32): {model_bytes / (1024**3):.2f} GB")
        logger.info(f"Memory Footprint (FP16): {model_bytes / (2 * 1024**3):.2f} GB")
        
        logger.info("="*60 + "\n")
    
    def benchmark_inference(self, code_samples: list = None, num_runs: int = 10):
        """Benchmark inference speed"""
        
        if code_samples is None:
            code_samples = [
                "def vulnerable(): buffer = [0]*10; buffer[99] = 1",
                "def safe(x): return x * 2",
                "int main() { char buf[10]; strcpy(buf, input); return 0; }"
            ]
        
        logger.info("\n" + "="*60)
        logger.info("INFERENCE BENCHMARK")
        logger.info("="*60)
        
        self.model.eval()
        device = next(self.model.parameters()).device
        
        inference_times = []
        
        logger.info(f"Running {num_runs} inference passes...")
        
        with torch.no_grad():
            for i in range(num_runs):
                # Randomly select code samples
                batch_codes = [code_samples[i % len(code_samples)] for i in range(4)]
                
                # Tokenize
                inputs = self.tokenizer(
                    batch_codes,
                    max_length=512,
                    truncation='max_length',
                    padding='max_length',
                    return_tensors='pt'
                )
                
                inputs = {k: v.to(device) for k, v in inputs.items()}
                
                # Time inference
                start = time.time()
                outputs = self.model(**inputs)
                torch.cuda.synchronize() if torch.cuda.is_available() else None
                end = time.time()
                
                inference_time = (end - start) * 1000  # Convert to ms
                inference_times.append(inference_time)
        
        # Statistics
        inference_times = np.array(inference_times)
        
        logger.info(f"\nBatch Size: 4 samples")
        logger.info(f"Mean Latency: {inference_times.mean():.2f} ms")
        logger.info(f"Std Dev: {inference_times.std():.2f} ms")
        logger.info(f"Min: {inference_times.min():.2f} ms")
        logger.info(f"Max: {inference_times.max():.2f} ms")
        logger.info(f"95th Percentile: {np.percentile(inference_times, 95):.2f} ms")
        
        # Throughput
        batch_size = 4
        throughput = (batch_size * 1000) / inference_times.mean()
        logger.info(f"\nThroughput: {throughput:.1f} samples/second")
        
        logger.info("="*60 + "\n")
    
    def push_to_hub(self, repo_name: str, private: bool = False):
        """Push model to HuggingFace Hub"""
        
        try:
            from huggingface_hub import HfApi, HfFolder
        except ImportError:
            logger.error("huggingface-hub not installed. Run: pip install huggingface-hub")
            return False
        
        logger.info(f"\nPushing model to HuggingFace Hub: {repo_name}")
        
        try:
            # Upload model
            self.model.push_to_hub(
                repo_name,
                private=private,
                force_upload=True
            )
            
            # Upload tokenizer
            self.tokenizer.push_to_hub(
                repo_name,
                private=private,
                force_upload=True
            )
            
            logger.info(f"✅ Model pushed successfully to: https://huggingface.co/{repo_name}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to push model: {e}")
            return False
    
    def export_to_onnx(self, output_path: str):
        """Export model to ONNX format"""
        
        try:
            import onnx
            from transformers.onnx import export
        except ImportError:
            logger.error("ONNX libraries not installed. Run: pip install onnx skl2onnx")
            return False
        
        logger.info(f"\nExporting model to ONNX: {output_path}")
        
        try:
            # This is simplified; for production use transformers.onnx module
            logger.warning("Note: Full ONNX export requires additional setup")
            logger.info("For production ONNX export, use:")
            logger.info("pip install optimum")
            logger.info("Then use: optimum-cli export onnx --model={model_dir} {output_dir}")
            
            return False
        
        except Exception as e:
            logger.error(f"ONNX export failed: {e}")
            return False
    
    def quantize_model(self, output_dir: str):
        """Quantize model for faster inference (FP16)"""
        
        logger.info(f"\nQuantizing model to FP16...")
        
        try:
            self.model = self.model.half()
            self.model.save_pretrained(output_dir)
            self.tokenizer.save_pretrained(output_dir)
            
            logger.info(f"✅ Quantized model saved to {output_dir}")
            return True
        
        except Exception as e:
            logger.error(f"Quantization failed: {e}")
            return False


def main():
    """Main utility function"""
    parser = argparse.ArgumentParser(description="Model management utilities")
    
    parser.add_argument(
        '--model_dir',
        type=str,
        default='models/codet5_base_vuln_detector',
        help='Model directory'
    )
    parser.add_argument(
        '--action',
        type=str,
        choices=['analyze', 'benchmark', 'push', 'quantize', 'all'],
        default='all',
        help='Action to perform'
    )
    parser.add_argument(
        '--repo_name',
        type=str,
        help='HuggingFace repo name (for push action)'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        help='Output directory'
    )
    
    args = parser.parse_args()
    
    # Create manager
    manager = ModelManager(args.model_dir)
    
    # Execute actions
    if args.action in ['analyze', 'all']:
        manager.analyze_model()
    
    if args.action in ['benchmark', 'all']:
        manager.benchmark_inference()
    
    if args.action in ['push', 'all']:
        if args.repo_name:
            manager.push_to_hub(args.repo_name)
        else:
            logger.warning("Skipping push (--repo_name not provided)")
    
    if args.action in ['quantize', 'all']:
        if args.output_dir:
            manager.quantize_model(args.output_dir)
        else:
            logger.warning("Skipping quantization (--output_dir not provided)")


if __name__ == '__main__':
    main()
