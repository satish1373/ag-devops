#!/usr/bin/env python3
"""Test runner script"""

import subprocess
import sys

def run_tests():
    """Run all tests with coverage"""
    commands = [
        "python -m pytest tests/ -v --tb=short",
        "python -m pytest tests/ --cov=src --cov-report=html",
        "python -m pytest tests/integration/ -v",
    ]
    
    for cmd in commands:
        try:
            subprocess.run(cmd, shell=True, check=True)
            print(f"✅ {cmd}")
        except subprocess.CalledProcessError:
            print(f"❌ {cmd}")
            
if __name__ == "__main__":
    run_tests()