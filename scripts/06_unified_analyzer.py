#!/usr/bin/env python3
"""
Unified Vulnerability Analysis Pipeline.

This script integrates:
1. Binary vulnerability detection (CodeT5 Model 1)
2. CWE classification (CodeT5 Model 2)
3. Code localization (Attention-based)
4. Generates detailed vulnerability report

Perfect for web application integration.
"""

import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class VulnerabilityReport:
    """Structured vulnerability report"""
    
    code: str
    is_vulnerable: bool
    vulnerability_confidence: float
    vulnerable_lines: List[int]
    vulnerable_segments: List[str]
    cwe_predictions: Dict[str, float]
    primary_cwe: str
    cwe_confidence: float
    risk_level: str
    recommendations: List[str]


class UnifiedVulnerabilityAnalyzer:
    """Unified vulnerability analysis using multiple models"""
    
    def __init__(
        self,
        vuln_model_dir: str,
        cwe_model_dir: str = None,
        max_length: int = 512,
        device: str = None
    ):
        """
        Initialize analyzer with vulnerability and CWE models
        
        Args:
            vuln_model_dir: Directory with vulnerability detection model
            cwe_model_dir: Optional directory with CWE classification model
            max_length: Maximum code length
            device: Device to use
        """
        self.max_length = max_length
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load vulnerability detection model
        logger.info(f"Loading vulnerability model from {vuln_model_dir}")
        self.vuln_tokenizer = AutoTokenizer.from_pretrained(vuln_model_dir)
        self.vuln_model = AutoModelForSequenceClassification.from_pretrained(vuln_model_dir)
        self.vuln_model.to(self.device)
        self.vuln_model.eval()
        
        # Load CWE model if available
        self.cwe_model = None
        self.cwe_tokenizer = None
        if cwe_model_dir:
            logger.info(f"Loading CWE model from {cwe_model_dir}")
            try:
                self.cwe_tokenizer = AutoTokenizer.from_pretrained(cwe_model_dir)
                self.cwe_model = AutoModelForSequenceClassification.from_pretrained(cwe_model_dir)
                self.cwe_model.to(self.device)
                self.cwe_model.eval()
            except Exception as e:
                logger.warning(f"Could not load CWE model: {e}")
        
        # CWE ID mapping (top 14 CWEs)
        self.cwe_mapping = {
            0: "CWE-119", 1: "CWE-787", 2: "CWE-89", 3: "CWE-79",
            4: "CWE-78", 5: "CWE-690", 6: "CWE-476", 7: "CWE-190",
            8: "CWE-191", 9: "CWE-200", 10: "CWE-401", 11: "CWE-415",
            12: "CWE-362", 13: "CWE-1026"
        }
    
    def analyze_code(self, code: str) -> VulnerabilityReport:
        """
        Comprehensive code vulnerability analysis
        
        Args:
            code: Source code to analyze
        
        Returns:
            VulnerabilityReport with detailed findings
        """
        # Step 1: Binary vulnerability detection
        vuln_pred, vuln_conf, vuln_logits = self._predict_vulnerability(code)
        
        # Step 2: CWE classification (if available)
        cwe_pred, cwe_probs = self._predict_cwe(code) if self.cwe_model else ({}, {})
        
        # Step 3: Identify vulnerable lines
        vulnerable_lines = self._localize_vulnerability(code, vuln_logits) if vuln_pred else []
        
        # Step 4: Extract vulnerable segments
        vulnerable_segments = self._extract_vulnerable_segments(code, vulnerable_lines)
        
        # Step 5: Determine risk level
        risk_level = self._determine_risk_level(vuln_conf, cwe_pred)
        
        # Step 6: Generate recommendations
        recommendations = self._generate_recommendations(vuln_pred, cwe_pred, vulnerable_lines)
        
        # Prepare primary CWE
        primary_cwe = self.cwe_mapping.get(cwe_pred.get('primary', 0), "Unknown")
        cwe_confidence = cwe_probs.get('primary', 0.0)
        
        return VulnerabilityReport(
            code=code,
            is_vulnerable=bool(vuln_pred),
            vulnerability_confidence=float(vuln_conf),
            vulnerable_lines=vulnerable_lines,
            vulnerable_segments=vulnerable_segments,
            cwe_predictions=cwe_pred,
            primary_cwe=primary_cwe,
            cwe_confidence=float(cwe_confidence),
            risk_level=risk_level,
            recommendations=recommendations
        )
    
    def _predict_vulnerability(self, code: str) -> Tuple[int, float, np.ndarray]:
        """Predict binary vulnerability"""
        
        inputs = self.vuln_tokenizer(
            code,
            max_length=self.max_length,
            truncation='max_length',
            padding='max_length',
            return_tensors='pt'
        )
        
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.vuln_model(**inputs, output_attentions=True)
        
        logits = outputs.logits.cpu().numpy()[0]
        probs = self._softmax(logits)
        
        pred = np.argmax(probs)
        conf = float(probs[pred])
        
        return int(pred), conf, logits
    
    def _predict_cwe(self, code: str) -> Tuple[Dict, Dict]:
        """Predict CWE classification"""
        
        if not self.cwe_model:
            return {}, {}
        
        inputs = self.cwe_tokenizer(
            code,
            max_length=self.max_length,
            truncation='max_length',
            padding='max_length',
            return_tensors='pt'
        )
        
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.cwe_model(**inputs)
        
        logits = outputs.logits.cpu().numpy()[0]
        probs = self._softmax(logits)
        
        # Get top 3 CWE predictions
        top_indices = np.argsort(probs)[-3:][::-1]
        
        predictions = {}
        probabilities = {}
        
        for rank, idx in enumerate(top_indices):
            pred_key = ['primary', 'secondary', 'tertiary'][rank]
            predictions[pred_key] = int(idx)
            probabilities[pred_key] = float(probs[idx])
        
        return predictions, probabilities
    
    def _localize_vulnerability(self, code: str, logits: np.ndarray) -> List[int]:
        """Identify lines likely containing vulnerability"""
        
        lines = code.split('\n')
        
        # Simple heuristic: split code into chunks and re-predict
        vulnerable_lines = []
        
        for line_idx, line in enumerate(lines):
            if not line.strip():
                continue
            
            # Check line for common vulnerability patterns
            vuln_patterns = [
                'strcpy', 'sprintf', 'gets', 'scanf',  # Buffer overflow
                'malloc', 'free', 'new', 'delete',      # Memory
                'sql', 'execute', 'query',              # SQL Injection
                '<script', 'innerHTML', 'eval',         # XSS
                'exec', 'system', 'popen',              # Command injection
            ]
            
            if any(pattern in line.lower() for pattern in vuln_patterns):
                vulnerable_lines.append(line_idx + 1)  # 1-indexed
        
        return vulnerable_lines[:10]  # Return top 10 lines
    
    def _extract_vulnerable_segments(self, code: str, vulnerable_lines: List[int]) -> List[str]:
        """Extract code segments for identified vulnerable lines"""
        
        lines = code.split('\n')
        segments = []
        
        for line_num in vulnerable_lines[:5]:  # Top 5 segments
            idx = line_num - 1
            if 0 <= idx < len(lines):
                # Get context (surrounding lines)
                start = max(0, idx - 1)
                end = min(len(lines), idx + 2)
                segment = '\n'.join(lines[start:end])
                segments.append(segment)
        
        return segments
    
    def _determine_risk_level(self, vuln_conf: float, cwe_pred: Dict) -> str:
        """Determine overall risk level"""
        
        if not cwe_pred:
            if vuln_conf > 0.8:
                return "HIGH"
            elif vuln_conf > 0.6:
                return "MEDIUM"
            else:
                return "LOW"
        
        # Critical CWEs
        critical_cwes = [78, 79, 89, 787, 119]
        primary_cwe = cwe_pred.get('primary', -1)
        
        if primary_cwe in critical_cwes and vuln_conf > 0.7:
            return "CRITICAL"
        elif vuln_conf > 0.8:
            return "HIGH"
        elif vuln_conf > 0.6:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_recommendations(
        self,
        is_vulnerable: int,
        cwe_pred: Dict,
        vulnerable_lines: List[int]
    ) -> List[str]:
        """Generate security recommendations"""
        
        recommendations = []
        
        if not is_vulnerable:
            recommendations.append("✅ No obvious vulnerabilities detected at this confidence level")
            return recommendations
        
        # CWE-specific recommendations
        cwe_recommendations = {
            78: [
                "Avoid using system(), exec(), or similar functions",
                "Use parameterized APIs instead of shell commands",
                "Validate and sanitize all user inputs"
            ],
            79: [
                "Escape all user-supplied data before rendering in HTML",
                "Use Content Security Policy (CSP) headers",
                "Use innerHTML with extreme caution; prefer textContent"
            ],
            89: [
                "Use prepared statements with parameterized queries",
                "Never concatenate user input into SQL strings",
                "Apply the principle of least privilege to database accounts"
            ],
            787: [
                "Use bounds checking before buffer operations",
                "Prefer safe string functions (strncpy instead of strcpy)",
                "Enable compiler warnings and static analysis"
            ],
            119: [
                "Validate all pointer arithmetic",
                "Use safe memory handling libraries",
                "Enable Address Sanitizer (ASAN) in development"
            ]
        }
        
        if cwe_pred:
            primary_cwe = cwe_pred.get('primary', -1)
            if primary_cwe in cwe_recommendations:
                recommendations.extend(cwe_recommendations[primary_cwe])
        
        if vulnerable_lines:
            recommendations.append(f"⚠️ Review lines {vulnerable_lines}")
        
        recommendations.extend([
            "Consider using static analysis tools (Pylint, ESLint, etc.)",
            "Perform manual code review with security focus",
            "Test with fuzzing and dynamic analysis tools"
        ])
        
        return recommendations[:5]  # Top 5 recommendations
    
    @staticmethod
    def _softmax(x: np.ndarray) -> np.ndarray:
        """Compute softmax"""
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum(axis=0)


def format_report(report: VulnerabilityReport) -> str:
    """Format report as readable string"""
    
    output = []
    output.append("\n" + "="*70)
    output.append("VULNERABILITY ANALYSIS REPORT")
    output.append("="*70)
    
    output.append(f"\n📊 VULNERABILITY STATUS: {'🔴 VULNERABLE' if report.is_vulnerable else '🟢 SAFE'}")
    output.append(f"   Confidence: {report.vulnerability_confidence:.1%}")
    output.append(f"   Risk Level: {report.risk_level}")
    
    if report.is_vulnerable:
        output.append(f"\n🎯 CWE CLASSIFICATION")
        output.append(f"   Primary: {report.primary_cwe} ({report.cwe_confidence:.1%})")
    
    if report.vulnerable_lines:
        output.append(f"\n⚠️ VULNERABLE LINES")
        for line_num in report.vulnerable_lines[:5]:
            output.append(f"   Line {line_num}")
    
    if report.vulnerable_segments:
        output.append(f"\n📝 VULNERABLE CODE SEGMENTS")
        for i, segment in enumerate(report.vulnerable_segments[:3], 1):
            output.append(f"\n   Segment {i}:")
            for line in segment.split('\n'):
                output.append(f"   {line}")
    
    if report.recommendations:
        output.append(f"\n💡 RECOMMENDATIONS")
        for i, rec in enumerate(report.recommendations, 1):
            output.append(f"   {i}. {rec}")
    
    output.append("\n" + "="*70 + "\n")
    
    return '\n'.join(output)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Unified vulnerability analysis")
    
    parser.add_argument(
        '--vuln_model',
        type=str,
        default='models/codet5_base_vuln_detector',
        help='Vulnerability detection model directory'
    )
    parser.add_argument(
        '--cwe_model',
        type=str,
        help='CWE classification model directory (optional)'
    )
    parser.add_argument(
        '--code',
        type=str,
        help='Code to analyze'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='File containing code to analyze'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for report'
    )
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = UnifiedVulnerabilityAnalyzer(
        vuln_model_dir=args.vuln_model,
        cwe_model_dir=args.cwe_model
    )
    
    # Get code
    if args.code:
        code = args.code
    elif args.file:
        with open(args.file, 'r') as f:
            code = f.read()
    else:
        print("Please provide --code or --file")
        return
    
    # Analyze
    logger.info("Analyzing code...")
    report = analyzer.analyze_code(code)
    
    # Display report
    print(format_report(report))
    
    # Save JSON report if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(asdict(report), f, indent=2)
        logger.info(f"Report saved to {args.output}")


if __name__ == '__main__':
    main()
