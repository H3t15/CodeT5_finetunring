#!/usr/bin/env python3
"""
QUICK START - Execute the complete CodeT5 fine-tuning pipeline in order.

This script runs all steps sequentially with sensible defaults.
"""

import subprocess
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_command(cmd: list, description: str) -> bool:
    """Run a command and report status"""
    logger.info(f"\n{'='*70}")
    logger.info(f"Step: {description}")
    logger.info(f"{'='*70}")
    
    try:
        result = subprocess.run(cmd, check=True, cwd=str(Path.cwd()))
        logger.info(f"✅ {description} completed successfully\n")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} failed with exit code {e.returncode}\n")
        return False
    except Exception as e:
        logger.error(f"❌ {description} failed: {e}\n")
        return False


def main():
    """Execute pipeline"""
    
    logger.info("\n" + "="*70)
    logger.info("CodeT5 VULNERABILITY DETECTION - COMPLETE PIPELINE")
    logger.info("="*70)
    
    steps = [
        # Step 1: Preprocessing
        (
            [
                sys.executable, "scripts/01_preprocess.py",
                "--raw_data", "Data/raw/megavul_simple.json",
                "--output_dir", "Data/processed",
                "--train_split", "0.7"
            ],
            "1. Dataset Preprocessing"
        ),
        
        # Step 2: Training
        (
            [
                sys.executable, "scripts/02_train.py",
                "--train_data", "Data/processed/train.json",
                "--val_data", "Data/processed/val.json",
                "--output_dir", "models/codet5_base_vuln_detector",
                "--model_name", "Salesforce/codet5-base",
                "--num_epochs", "5",
                "--batch_size", "16"
            ],
            "2. Model Fine-tuning"
        ),
        
        # Step 3: Evaluation
        (
            [
                sys.executable, "scripts/03_evaluate.py",
                "--model_dir", "models/codet5_base_vuln_detector",
                "--test_data", "Data/processed/test.json",
                "--output_dir", "outputs/evaluation"
            ],
            "3. Model Evaluation"
        ),
        
        # Step 4: Model Analysis
        (
            [
                sys.executable, "scripts/05_model_utils.py",
                "--model_dir", "models/codet5_base_vuln_detector",
                "--action", "analyze"
            ],
            "4. Model Analysis"
        ),
    ]
    
    completed = 0
    failed = 0
    
    for cmd, description in steps:
        if run_command(cmd, description):
            completed += 1
        else:
            failed += 1
            logger.warning("Continuing despite failure...")
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("PIPELINE SUMMARY")
    logger.info("="*70)
    logger.info(f"Completed: {completed}/{len(steps)}")
    logger.info(f"Failed: {failed}/{len(steps)}")
    
    if failed == 0:
        logger.info("\n✅ All pipeline steps completed successfully!")
        logger.info("\nNext steps:")
        logger.info("  1. Review evaluation results: cat outputs/evaluation/metrics.json")
        logger.info("  2. Run inference: python scripts/04_inference.py --mode interactive")
        logger.info("  3. Analyze code: python scripts/06_unified_analyzer.py --code 'your code'")
    else:
        logger.error(f"\n❌ Pipeline failed with {failed} errors")
        sys.exit(1)


if __name__ == '__main__':
    main()
