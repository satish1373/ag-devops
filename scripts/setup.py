#!/usr/bin/env python3
"""Setup script for LangGraph DevOps Autocoder"""

import subprocess
import sys
from pathlib import Path

def run_command(command):
    """Run shell command and handle errors"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {command}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {command}")
        print(f"Error: {e.stderr}")
        return None

def main():
    """Main setup function"""
    print("🚀 Setting up LangGraph DevOps Autocoder...")
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ required")
        sys.exit(1)
    
    # Create directories
    directories = ["logs", "reports", "tests/fixtures"]
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")
    
    # Install dependencies
    print("\n📦 Installing Python dependencies...")
    run_command("pip install -r requirements.txt")
    
    # Install Playwright browsers
    print("\n🎭 Installing Playwright browsers...")
    run_command("playwright install")
    
    # Run tests
    print("\n🧪 Running tests...")
    run_command("python -m pytest tests/ -v")
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Update .env with your configuration")
    print("2. Run: python src/server.py")
    print("3. Test webhook: POST to http://localhost:8000/webhook/jira")

if __name__ == "__main__":
    main()