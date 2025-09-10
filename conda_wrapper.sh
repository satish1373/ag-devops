#!/bin/bash

# Quick Conda Fix - Update your existing jira_trigger.sh
# This fixes the Python path issues you're experiencing

# Add this to the top of your scripts/jira_trigger.sh file
# Or create a new conda_wrapper.sh

echo "🐍 Conda Environment Fix for LangGraph DevOps"
echo "=============================================="

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

# Function to setup conda environment
setup_conda_env() {
    print_info "Setting up conda environment..."
    
    # Check if conda is available
    if ! command -v conda &> /dev/null; then
        print_error "Conda not found. Please install Anaconda/Miniconda first."
        return 1
    fi
    
    # Initialize conda for bash if not already done
    if [[ -z "$CONDA_EXE" ]]; then
        print_info "Initializing conda..."
        eval "$(conda shell.bash hook)"
    fi
    
    # Check if we have an active environment
    if [[ -n "$CONDA_DEFAULT_ENV" ]]; then
        print_status "Using active conda environment: $CONDA_DEFAULT_ENV"
    else
        print_info "No conda environment active. Looking for suitable environment..."
        
        # Try to find and activate langgraph environment
        if conda env list | grep -q "langgraph"; then
            local env_name=$(conda env list | grep "langgraph" | head -1 | awk '{print $1}')
            print_info "Found environment: $env_name"
            conda activate "$env_name"
        elif conda env list | grep -q "devops"; then
            local env_name=$(conda env list | grep "devops" | head -1 | awk '{print $1}')
            print_info "Found environment: $env_name"
            conda activate "$env_name"
        else
            print_warning "No suitable environment found. Creating one..."
            conda create -n langgraph-devops python=3.10 -y
            conda activate langgraph-devops
        fi
    fi
    
    return 0
}

# Function to install required packages
install_required_packages() {
    print_info "Checking and installing required packages..."
    
    # List of required packages
    local packages=("requests" "jira" "python-dotenv" "fastapi" "uvicorn")
    local missing_packages=()
    
    # Check each package
    for package in "${packages[@]}"; do
        if ! python -c "import ${package//-/_}" 2>/dev/null; then
            missing_packages+=("$package")
        else
            print_status "$package: ✅ installed"
        fi
    done
    
    # Install missing packages
    if [[ ${#missing_packages[@]} -gt 0 ]]; then
        print_info "Installing missing packages: ${missing_packages[*]}"
        pip install "${missing_packages[@]}"
        
        # Verify installation
        for package in "${missing_packages[@]}"; do
            if python -c "import ${package//-/_}" 2>/dev/null; then
                print_status "$package: ✅ installed successfully"
            else
                print_error "$package: ❌ installation failed"
            fi
        done
    else
        print_status "All required packages are installed"
    fi
}

# Function to test the setup
test_setup() {
    print_info "Testing conda setup..."
    
    # Test Python
    local python_version=$(python --version 2>&1)
    print_status "Python: $python_version"
    print_status "Python path: $(which python)"
    
    # Test conda environment
    if [[ -n "$CONDA_DEFAULT_ENV" ]]; then
        print_status "Conda environment: $CONDA_DEFAULT_ENV"
    else
        print_warning "No conda environment active"
    fi
    
    # Test imports
    print_info "Testing package imports..."
    python -c "
import sys
print(f'Python executable: {sys.executable}')

packages = ['requests', 'jira', 'dotenv']
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg}: OK')
    except ImportError:
        print(f'❌ {pkg}: FAILED')
"
}

# Function to run jira scripts with conda
run_with_conda() {
    local script_args="$@"
    
    print_info "Running Jira script with conda..."
    
    # Ensure we're in the project root
    if [[ ! -f "scripts/jira_webhook_trigger.py" ]]; then
        print_error "jira_webhook_trigger.py not found in scripts/"
        print_info "Make sure you're in the project root directory"
        return 1
    fi
    
    # Set Python path
    export PYTHONPATH="$(pwd):${PYTHONPATH:-}"
    
    # Run the script
    print_info "Executing: python scripts/jira_webhook_trigger.py $script_args"
    python scripts/jira_webhook_trigger.py $script_args
}

# Main execution
main() {
    # Setup conda environment
    if ! setup_conda_env; then
        print_error "Failed to setup conda environment"
        exit 1
    fi
    
    # Install packages
    install_required_packages
    
    # Test setup
    test_setup
    
    echo
    print_status "Conda setup complete! You can now run:"
    echo "  $0 sample                 # Test with sample tickets"
    echo "  $0 ticket DEVOPS-123      # Process specific ticket"
    echo "  $0 status                 # Check system status"
    echo
    
    # If arguments provided, run the command
    if [[ $# -gt 0 ]]; then
        echo
        print_info "Running command with arguments: $@"
        run_with_conda "$@"
    fi
}

# Handle different commands
case "${1:-help}" in
    "setup")
        main
        ;;
    "sample")
        setup_conda_env && run_with_conda --sample
        ;;
    "ticket")
        if [[ -z "$2" ]]; then
            print_error "Ticket key required: $0 ticket DEVOPS-123"
            exit 1
        fi
        setup_conda_env && run_with_conda --ticket "$2"
        ;;
    "search")
        if [[ -z "$2" ]]; then
            print_error "JQL query required: $0 search 'project = DEVOPS'"
            exit 1
        fi
        setup_conda_env && run_with_conda --jql "$2"
        ;;
    "status")
        setup_conda_env && test_setup
        ;;
    "test")
        setup_conda_env && test_setup
        ;;
    "help"|*)
        echo "🐍 Conda-based Jira Integration"
        echo "Usage: $0 [command] [args]"
        echo ""
        echo "Commands:"
        echo "  setup                 - Setup conda environment and packages"
        echo "  sample                - Run sample tickets test"
        echo "  ticket <key>          - Process specific Jira ticket"
        echo "  search '<jql>'        - Search tickets with JQL"
        echo "  status                - Check system status"
        echo "  test                  - Test conda setup"
        echo ""
        echo "Examples:"
        echo "  $0 setup"
        echo "  $0 sample"
        echo "  $0 ticket DEVOPS-123"
        echo "  $0 search 'project = DEVOPS AND status = \"To Do\"'"
        ;;
esac