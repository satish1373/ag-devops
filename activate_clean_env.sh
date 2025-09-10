#!/bin/bash

# Activate Clean Environment and Test Jira Integration
echo "🧪 Activating Clean Environment and Testing"
echo "==========================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Initialize conda for bash
init_conda() {
    print_info "Initializing conda for bash..."
    
    # Find conda installation
    if [[ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]]; then
        source "$HOME/anaconda3/etc/profile.d/conda.sh"
    elif [[ -f "/c/Users/$USER/anaconda3/etc/profile.d/conda.sh" ]]; then
        source "/c/Users/$USER/anaconda3/etc/profile.d/conda.sh"
    elif [[ -f "$CONDA_EXE" ]]; then
        eval "$(conda shell.bash hook)"
    else
        print_warning "Trying conda init..."
        conda init bash 2>/dev/null || true
        eval "$(conda shell.bash hook)" 2>/dev/null || true
    fi
}

# Activate debug-test environment
activate_clean_env() {
    print_info "Activating debug-test environment..."
    
    # Try different activation methods
    if conda activate debug-test 2>/dev/null; then
        print_status "Successfully activated debug-test environment"
        return 0
    elif eval "$(conda shell.bash hook)" && conda activate debug-test 2>/dev/null; then
        print_status "Successfully activated debug-test environment (method 2)"
        return 0
    else
        print_error "Failed to activate debug-test environment"
        
        # Show available environments
        print_info "Available environments:"
        conda env list
        
        print_info "Trying to activate manually..."
        export PATH="/c/Users/$USER/anaconda3/envs/debug-test/Scripts:$PATH"
        export PATH="/c/Users/$USER/anaconda3/envs/debug-test:$PATH"
        
        if python --version 2>/dev/null; then
            print_status "Manually activated debug-test environment"
            return 0
        else
            return 1
        fi
    fi
}

# Install packages in clean environment
install_packages() {
    print_info "Installing packages in clean environment..."
    
    # Verify we're in the right environment
    echo "Current Python:"
    which python
    python --version
    
    # Install packages
    local packages=("requests" "python-dotenv" "fastapi" "uvicorn")
    
    for package in "${packages[@]}"; do
        print_info "Installing $package..."
        pip install "$package"
        
        # Test import
        local import_name="$package"
        if [[ "$package" == "python-dotenv" ]]; then
            import_name="dotenv"
        fi
        
        if python -c "import $import_name; print('✅ $package OK')" 2>/dev/null; then
            print_status "$package installed successfully"
        else
            print_warning "$package installation may have issues"
        fi
    done
    
    # Install jira carefully
    print_info "Installing jira package..."
    pip install jira==3.4.1  # Use older stable version
    
    if python -c "import jira; from jira import JIRA; print('✅ Jira fully functional')" 2>/dev/null; then
        print_status "Jira package installed successfully"
    else
        print_error "Jira package installation failed"
        return 1
    fi
}

# Test the Jira script in clean environment
test_jira_script() {
    print_info "Testing Jira script in clean environment..."
    
    # Verify environment
    echo "Environment check:"
    echo "  Current environment: ${CONDA_DEFAULT_ENV:-unknown}"
    echo "  Python: $(which python)"
    echo "  Python version: $(python --version)"
    
    # Test all imports together
    print_info "Testing all imports together..."
    python -c "
import sys
print(f'Python executable: {sys.executable}')

try:
    import requests, jira, dotenv, fastapi
    from jira import JIRA
    print('✅ All imports successful')
except Exception as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
"
    
    if [[ $? -ne 0 ]]; then
        print_error "Import test failed"
        return 1
    fi
    
    # Set Python path
    export PYTHONPATH="$(pwd):${PYTHONPATH:-}"
    
    # Test the actual script
    print_info "Testing actual Jira webhook script..."
    
    if [[ ! -f "scripts/jira_webhook_trigger.py" ]]; then
        print_error "jira_webhook_trigger.py not found"
        return 1
    fi
    
    print_info "Running: python scripts/jira_webhook_trigger.py --sample --no-send"
    python scripts/jira_webhook_trigger.py --sample --no-send
    
    local exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
        print_status "🎉 SUCCESS! No segmentation fault in clean environment!"
        return 0
    else
        print_error "Script failed with exit code: $exit_code"
        return 1
    fi
}

# Create a simple test to verify it's working
create_simple_test() {
    print_info "Creating simple webhook test..."
    
    cat > simple_test.py << 'EOF'
#!/usr/bin/env python3
"""
Simple test to verify clean environment works
"""

import requests
import json
from datetime import datetime

print("🧪 Simple Clean Environment Test")
print("=" * 40)

# Test 1: Basic imports
try:
    import jira
    from jira import JIRA
    print("✅ Jira imports working")
except Exception as e:
    print(f"❌ Jira import failed: {e}")
    exit(1)

# Test 2: Create sample payload
sample_payload = {
    "timestamp": int(datetime.now().timestamp() * 1000),
    "webhookEvent": "jira:issue_created",
    "issue": {
        "key": "CLEAN-TEST-001",
        "id": "10001",
        "fields": {
            "summary": "Clean environment test",
            "description": "Testing in debug-test environment",
            "issuetype": {"name": "Story"},
            "priority": {"name": "Medium"},
            "status": {"name": "To Do"},
            "project": {"key": "TEST", "name": "Test Project"},
            "creator": {"name": "test-user", "displayName": "Test User"},
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat()
        }
    }
}

print("✅ Sample payload created")

# Test 3: Test webhook (if server is running)
webhook_url = "http://localhost:8000/webhook/jira"

try:
    response = requests.post(
        webhook_url,
        json=sample_payload,
        headers={"Content-Type": "application/json", "X-Hub-Signature-256": "sha256=test"},
        timeout=10
    )
    
    if response.status_code == 200:
        print("✅ Webhook test successful!")
        print(f"Response: {response.text}")
    else:
        print(f"⚠️ Webhook returned {response.status_code}")
        print("Make sure LangGraph server is running: python src/server.py")
        
except requests.exceptions.ConnectionError:
    print("⚠️ Could not connect to webhook (server not running)")
    print("Start server with: python src/server.py")
except Exception as e:
    print(f"❌ Webhook test failed: {e}")

print("🎉 Clean environment test completed!")
EOF

    print_info "Running simple test..."
    python simple_test.py
    
    # Clean up
    rm -f simple_test.py
}

# Main execution
main() {
    echo "This script will:"
    echo "1. Properly activate the debug-test environment"
    echo "2. Install required packages"
    echo "3. Test the Jira script without segmentation fault"
    echo ""
    
    # Initialize conda
    init_conda
    
    # Activate clean environment
    if ! activate_clean_env; then
        print_error "Failed to activate clean environment"
        exit 1
    fi
    
    echo ""
    print_status "Successfully activated clean environment"
    
    # Install packages
    if ! install_packages; then
        print_error "Package installation failed"
        exit 1
    fi
    
    echo ""
    print_status "All packages installed successfully"
    
    # Test the script
    echo ""
    if test_jira_script; then
        echo ""
        print_status "🎉 SUCCESS! Jira integration working in clean environment!"
        
        echo ""
        print_info "To use this environment in the future:"
        echo "  conda activate debug-test"
        echo "  cd /d/Projects/real_usecases/Draft/langgraph-devops-autocoder"
        echo "  python scripts/jira_webhook_trigger.py --sample"
        
    else
        echo ""
        print_warning "Script test failed, trying simple test..."
        create_simple_test
    fi
}

# Run main function
main "$@"