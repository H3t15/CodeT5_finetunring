#!/usr/bin/env python3
"""
Preprocess MegaVul dataset for CodeT5 fine-tuning.

This script:
1. Loads the MegaVul JSON array
2. Filters and cleans data
3. Creates train/val/test splits
4. Saves processed data in JSONL format
5. Generates dataset statistics
"""

import json
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import random
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MegaVulPreprocessor:
    """Preprocess MegaVul dataset for CodeT5"""
    
    def __init__(
        self,
        raw_data_path: str,
        output_dir: str,
        train_split: float = 0.7,
        val_split: float = 0.15,
        test_split: float = 0.15,
        max_code_length: int = 1024,
        min_code_length: int = 10,
        seed: int = 42
    ):
        """
        Initialize preprocessing parameters
        
        Args:
            raw_data_path: Path to megavul_simple.json
            output_dir: Directory to save processed data
            train_split: Training set ratio
            val_split: Validation set ratio
            test_split: Test set ratio
            max_code_length: Maximum code length (in characters)
            min_code_length: Minimum code length (in characters)
            seed: Random seed for reproducibility
        """
        self.raw_data_path = Path(raw_data_path)
        self.output_dir = Path(output_dir)
        self.train_split = train_split
        self.val_split = val_split
        self.test_split = test_split
        self.max_code_length = max_code_length
        self.min_code_length = min_code_length
        self.seed = seed
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set random seed
        random.seed(seed)
        
        # Verify that splits sum to 1.0
        splits_sum = train_split + val_split + test_split
        assert abs(splits_sum - 1.0) < 0.01, f"Splits must sum to 1.0, got {splits_sum}"
        
        logger.info(f"Initialized preprocessor with {train_split:.1%} train, {val_split:.1%} val, {test_split:.1%} test")
    
    def load_megavul_data(self) -> List[Dict]:
        """
        Load MegaVul dataset from JSON file
        
        Returns:
            List of vulnerability records
        """
        logger.info(f"Loading data from {self.raw_data_path}...")
        
        if not self.raw_data_path.exists():
            raise FileNotFoundError(f"Dataset not found at {self.raw_data_path}")
        
        try:
            with open(self.raw_data_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
            
            if not isinstance(dataset, list):
                raise ValueError(f"Expected list, got {type(dataset)}")
            
            logger.info(f"Loaded {len(dataset)} records")
            return dataset
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            raise
    
    def extract_code_and_label(self, record: Dict) -> Tuple[str, int, Dict]:
        """
        Extract code and vulnerability label from record
        
        Args:
            record: Single vulnerability record
        
        Returns:
            Tuple of (code, label, metadata)
        """
        # Use abstract code for better generalization
        code = record.get('abstract_func_before', record.get('func_before', ''))
        
        # Get vulnerability label
        is_vulnerable = int(record.get('is_vul', False))
        
        # Extract metadata
        metadata = {
            'cve_id': record.get('cve_id', 'unknown'),
            'cwe_ids': record.get('cwe_ids', []),
            'repo_name': record.get('repo_name', 'unknown'),
            'commit_hash': record.get('commit_hash', ''),
            'file_path': record.get('file_path', ''),
            'func_name': record.get('func_name', ''),
            'cvss_vector': record.get('cvss_vector', ''),
        }
        
        return code, is_vulnerable, metadata
    
    def validate_record(self, code: str, label: int) -> bool:
        """
        Validate if record meets quality criteria
        
        Args:
            code: Code snippet
            label: Vulnerability label
        
        Returns:
            True if record is valid
        """
        # Check code length
        if len(code.strip()) < self.min_code_length:
            return False
        
        if len(code) > self.max_code_length:
            # Could optionally truncate instead of filtering
            return False
        
        # Check for empty or whitespace-only code
        if not code.strip():
            return False
        
        # Check if code contains actual code (at least some non-whitespace)
        if len(code.split()) < 3:
            return False
        
        return True
    
    def preprocess_dataset(self, dataset: List[Dict]) -> Tuple[List, Dict]:
        """
        Preprocess and filter dataset
        
        Args:
            dataset: Raw dataset
        
        Returns:
            Tuple of (processed_records, statistics)
        """
        logger.info("Preprocessing dataset...")
        
        processed_records = []
        statistics = {
            'total_records': len(dataset),
            'valid_records': 0,
            'vulnerable': 0,
            'non_vulnerable': 0,
            'filtered_short_code': 0,
            'filtered_long_code': 0,
            'cwe_distribution': defaultdict(int),
            'repo_distribution': defaultdict(int),
        }
        
        for idx, record in enumerate(dataset):
            if (idx + 1) % 1000 == 0:
                logger.info(f"Processed {idx + 1}/{len(dataset)} records")
            
            try:
                code, label, metadata = self.extract_code_and_label(record)
                
                # Validate record
                if not self.validate_record(code, label):
                    if len(code.strip()) < self.min_code_length:
                        statistics['filtered_short_code'] += 1
                    else:
                        statistics['filtered_long_code'] += 1
                    continue
                
                # Create processed record
                processed_record = {
                    'code': code,
                    'label': label,
                    'metadata': metadata
                }
                
                processed_records.append(processed_record)
                statistics['valid_records'] += 1
                
                # Update statistics
                if label == 1:
                    statistics['vulnerable'] += 1
                else:
                    statistics['non_vulnerable'] += 1
                
                for cwe in metadata.get('cwe_ids', []):
                    statistics['cwe_distribution'][cwe] += 1
                
                statistics['repo_distribution'][metadata.get('repo_name', 'unknown')] += 1
            
            except Exception as e:
                logger.warning(f"Error processing record {idx}: {e}")
                continue
        
        logger.info(f"Preprocessing complete: {statistics['valid_records']} valid records")
        logger.info(f"Vulnerable: {statistics['vulnerable']}, Non-vulnerable: {statistics['non_vulnerable']}")
        
        return processed_records, statistics
    
    def split_dataset(self, records: List[Dict]) -> Tuple[List, List, List]:
        """
        Split dataset into train/val/test
        
        Uses stratified split to maintain vulnerability distribution
        
        Args:
            records: Preprocessed records
        
        Returns:
            Tuple of (train_records, val_records, test_records)
        """
        logger.info("Splitting dataset...")
        
        # Separate by label for stratified split
        vulnerable = [r for r in records if r['label'] == 1]
        non_vulnerable = [r for r in records if r['label'] == 0]
        
        logger.info(f"Vulnerable records: {len(vulnerable)}")
        logger.info(f"Non-vulnerable records: {len(non_vulnerable)}")
        
        # Shuffle
        random.shuffle(vulnerable)
        random.shuffle(non_vulnerable)
        
        # Split each group
        vul_train_idx = int(len(vulnerable) * self.train_split)
        vul_val_idx = vul_train_idx + int(len(vulnerable) * self.val_split)
        
        non_vul_train_idx = int(len(non_vulnerable) * self.train_split)
        non_vul_val_idx = non_vul_train_idx + int(len(non_vulnerable) * self.val_split)
        
        # Combine
        train = vulnerable[:vul_train_idx] + non_vulnerable[:non_vul_train_idx]
        val = vulnerable[vul_train_idx:vul_val_idx] + non_vulnerable[non_vul_train_idx:non_vul_val_idx]
        test = vulnerable[vul_val_idx:] + non_vulnerable[non_vul_val_idx:]
        
        # Final shuffle
        random.shuffle(train)
        random.shuffle(val)
        random.shuffle(test)
        
        logger.info(f"Train: {len(train)} ({len(train)/len(records):.1%})")
        logger.info(f"Val: {len(val)} ({len(val)/len(records):.1%})")
        logger.info(f"Test: {len(test)} ({len(test)/len(records):.1%})")
        
        return train, val, test
    
    def save_split(self, records: List[Dict], split_name: str) -> str:
        """
        Save split to JSONL file
        
        Args:
            records: Records to save
            split_name: 'train', 'val', or 'test'
        
        Returns:
            Path to saved file
        """
        output_path = self.output_dir / f"{split_name}.json"
        
        logger.info(f"Saving {split_name} split to {output_path}...")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Save as JSON lines (one record per line)
            for record in records:
                f.write(json.dumps(record) + '\n')
        
        logger.info(f"Saved {len(records)} records to {output_path}")
        return str(output_path)
    
    def save_statistics(self, statistics: Dict):
        """
        Save preprocessing statistics
        
        Args:
            statistics: Statistics dictionary
        """
        stats_path = self.output_dir / 'dataset_info.txt'
        
        logger.info(f"Saving statistics to {stats_path}...")
        
        with open(stats_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("MegaVul Dataset Preprocessing Statistics\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Total records: {statistics['total_records']}\n")
            f.write(f"Valid records: {statistics['valid_records']}\n")
            f.write(f"  Vulnerable: {statistics['vulnerable']}\n")
            f.write(f"  Non-vulnerable: {statistics['non_vulnerable']}\n")
            f.write(f"Filtered (short code): {statistics['filtered_short_code']}\n")
            f.write(f"Filtered (long code): {statistics['filtered_long_code']}\n\n")
            
            f.write("Top 20 CWE types:\n")
            cwe_sorted = sorted(
                statistics['cwe_distribution'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:20]
            for cwe, count in cwe_sorted:
                f.write(f"  {cwe}: {count}\n")
            
            f.write("\nTop 20 Repositories:\n")
            repo_sorted = sorted(
                statistics['repo_distribution'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:20]
            for repo, count in repo_sorted:
                f.write(f"  {repo}: {count}\n")
    
    def run(self):
        """Execute full preprocessing pipeline"""
        logger.info("Starting preprocessing pipeline...")
        
        # Load data
        dataset = self.load_megavul_data()
        
        # Preprocess
        processed_records, statistics = self.preprocess_dataset(dataset)
        
        # Split
        train, val, test = self.split_dataset(processed_records)
        
        # Save
        self.save_split(train, 'train')
        self.save_split(val, 'val')
        self.save_split(test, 'test')
        self.save_statistics(statistics)
        
        logger.info("Preprocessing complete!")
        logger.info(f"Output saved to {self.output_dir}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Preprocess MegaVul dataset for CodeT5 fine-tuning"
    )
    
    parser.add_argument(
        '--raw_data',
        type=str,
        default='Data/raw/megavul_simple.json',
        help='Path to raw MegaVul JSON file'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='Data/processed',
        help='Output directory for processed data'
    )
    parser.add_argument(
        '--train_split',
        type=float,
        default=0.7,
        help='Training set ratio'
    )
    parser.add_argument(
        '--val_split',
        type=float,
        default=0.15,
        help='Validation set ratio'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--max_code_length',
        type=int,
        default=1024,
        help='Maximum code length in characters'
    )
    parser.add_argument(
        '--min_code_length',
        type=int,
        default=10,
        help='Minimum code length in characters'
    )
    
    args = parser.parse_args()
    
    # Create preprocessor
    preprocessor = MegaVulPreprocessor(
        raw_data_path=args.raw_data,
        output_dir=args.output_dir,
        train_split=args.train_split,
        val_split=args.val_split,
        test_split=1.0 - args.train_split - args.val_split,
        max_code_length=args.max_code_length,
        min_code_length=args.min_code_length,
        seed=args.seed
    )
    
    # Run preprocessing
    preprocessor.run()


if __name__ == '__main__':
    main()
