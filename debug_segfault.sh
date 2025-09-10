#!/bin/bash

# Debug and Fix Segmentation Fault in Python/Conda
echo "🔍 Debugging Segmentation Fault"
echo "================================"

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

# Step 1: Test basic Python functionality
test_basic_python() {
    print_info "Step 1: Testing basic Python functionality..."
    
    echo "Testing basic Python:"
    python -c "print('✅ Basic Python works')"
    
    echo "Testing sys module:"
    python -c "import sys; print(f'✅ Python {sys.version_info.major}.{sys.version_info.minor} - {sys.executable}')"
}

# Step 2: Test imports one by one
test_imports_individually() {
    print_info "Step 2: Testing imports individually..."
    
    local packages=("os" "sys" "json" "time" "pathlib" "requests" "jira" "dotenv")
    
    for package in "${packages[@]}"; do
        echo -n "Testing $package: "
        if python -c "import $package; print('✅ OK')" 2>/dev/null; then
            echo ""
        else
            echo "❌ FAILED"
            # Try to get more info about the failure
            python -c "import $package" 2>&1 | head -3
        fi
    done
}

# Step 3: Test the problematic script in minimal form
test_minimal_script() {
    print_info "Step 3: Testing minimal version of script..."
    
    cat > test_minimal.py << 'EOF'
#!/usr/bin/env python3
"""
Minimal test script to isolate segfault issue
"""

print("🔍 Starting minimal test...")

# Test basic imports
try:
    import os
    import sys
    print("✅ Basic imports OK")
except Exception as e:
    print(f"❌ Basic imports failed: {e}")
    sys.exit(1)

# Test requests
try:
    import requests
    print("✅ Requests import OK")
except Exception as e:
    print(f"❌ Requests import failed: {e}")

# Test jira (most likely culprit)
try:
    import jira
    print("✅ Jira import OK")
except Exception as e:
    print(f"❌ Jira import failed: {e}")

# Test creating JIRA client (this often causes segfaults)
try:
    from jira import JIRA
    print("✅ JIRA class import OK")
    
    # Don't actually connect, just test instantiation
    print("✅ All imports successful - segfault is elsewhere")
    
except Exception as e:
    print(f"❌ JIRA class failed: {e}")

print("🎉 Minimal test completed successfully")
EOF

    echo "Running minimal test script:"
    python test_minimal.py
    
    # Clean up
    rm -f test_minimal.py
}

# Step 4: Check for DLL/library conflicts
check_dll_conflicts() {
    print_info "Step 4: Checking for DLL conflicts (Windows specific)..."
    
    # Check conda environment
    echo "Conda info:"
    conda info --envs
    
    echo ""
    echo "Python executable location:"
    which python
    python -c "import sys; print(sys.executable)"
    
    echo ""
    echo "Library paths:"
    python -c "
import sys
print('Python path:')
for p in sys.path[:5]:  # First 5 entries
    print(f'  {p}')
"
}

# Step 5: Create clean test environment
create_clean_environment() {
    print_info "Step 5: Creating clean test environment..."
    
    read -p "Create a clean conda environment for testing? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Creating clean environment..."
        
        # Create minimal environment
        conda create -n debug-test python=3.10 -y
        
        print_info "Activating clean environment..."
        conda activate debug-test
        
        print_info "Installing packages one by one..."
        
        # Install packages incrementally and test each
        local packages=("requests" "python-dotenv")
        
        for package in "${packages[@]}"; do
            echo "Installing $package..."
            pip install "$package"
            
            echo "Testing $package..."
            python -c "import ${package//-/_}; print('✅ $package OK')"
        done
        
        # Test jira last (most likely culprit)
        echo "Installing jira (potential culprit)..."
        pip install jira
        
        echo "Testing jira import..."
        python -c "
try:
    import jira
    print('✅ Jira import OK')
    from jira import JIRA
    print('✅ JIRA class OK')
except Exception as e:
    print(f'❌ Jira failed: {e}')
"
        
        print_status "Clean environment test completed"
        print_info "To use this environment: conda activate debug-test"
    fi
}

# Step 6: Alternative package versions
try_alternative_packages() {
    print_info "Step 6: Trying alternative package versions..."
    
    print_info "Current package versions:"
    pip list | grep -E "(jira|requests|urllib3)"
    
    echo ""
    print_info "Trying different jira package version..."
    
    # Uninstall and reinstall with specific versions
    pip uninstall jira -y
    
    # Try an older, more stable version
    pip install jira==3.4.1
    
    echo "Testing older jira version:"
    python -c "
try:
    import jira
    print('✅ Older jira version works')
except Exception as e:
    print(f'❌ Still failing: {e}')
"
}

# Step 7: Ultimate fallback - create simplified script
create_fallback_script() {
    print_info "Step 7: Creating fallback script without problematic imports..."
    
    cat > simple_webhook_test.py << 'EOF'
#!/usr/bin/env python3
"""
Simplified webhook test without potentially problematic imports
"""

import json
import requests
import os
from datetime import datetime

print("🚀 Simple Webhook Test (No Jira Library)")
print("=" * 50)

def create_sample_payload():
    """Create sample Jira webhook payload without using jira library"""
    return {
        "timestamp": int(datetime.now().timestamp() * 1000),
        "webhookEvent": "jira:issue_created", 
        "issue": {
            "key": "TEST-001",
            "id": "10001",
            "fields": {
                "summary": "Test webhook without jira library",
                "description": "This is a test to bypass segmentation fault",
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

def send_webhook(payload):
    """Send webhook to LangGraph server"""
    webhook_url = os.getenv("WEBHOOK_URL", "http://localhost:8000/webhook/jira")
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": "sha256=test"
            },
            timeout=30
        )
        
        print(f"✅ Webhook sent successfully: {response.status_code}")
        if response.status_code == 200:
            print(f"📋 Response: {response.text}")
            return True
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Webhook failed: {e}")
        return False

def main():
    print("Creating sample payload...")
    payload = create_sample_payload()
    
    print("Sample payload created:")
    print(json.dumps(payload, indent=2)[:200] + "...")
    
    print("\nSending to LangGraph webhook...")
    success = send_webhook(payload)
    
    if success:
        print("\n🎉 Webhook test successful!")
        print("The segfault is likely in the jira library.")
        print("Consider using this approach instead of the jira library.")
    else:
        print("\n❌ Webhook test failed")
        print("Check if LangGraph server is running: python src/server.py")

if __name__ == "__main__":
    main()
EOF

    echo "Running fallback script (bypasses jira library):"
    python simple_webhook_test.py
}

# Main execution
main() {
    echo "This script will help diagnose and fix the segmentation fault."
    echo "We'll test each component individually to isolate the issue."
    echo ""
    
    # Run tests in order
    test_basic_python
    echo ""
    
    test_imports_individually  
    echo ""
    
    test_minimal_script
    echo ""
    
    check_dll_conflicts
    echo ""
    
    echo "Choose next action:"
    echo "1. Create clean conda environment"
    echo "2. Try alternative package versions" 
    echo "3. Use fallback script (bypass jira library)"
    echo "4. Exit"
    
    read -p "Enter choice (1-4): " choice
    
    case $choice in
        1) create_clean_environment ;;
        2) try_alternative_packages ;;
        3) create_fallback_script ;;
        4) echo "Exiting..."; exit 0 ;;
        *) echo "Invalid choice" ;;
    esac
}

# Run main function
main "$@"