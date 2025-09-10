#!/bin/bash

# Jira Webhook Trigger Shell Script
# Wrapper script for easier interaction with the Jira ticket reader

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_header() { echo -e "${PURPLE}🚀 $1${NC}"; }

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/jira_webhook_trigger.py"

# Check if Python script exists
check_python_script() {
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        print_error "Python script not found: $PYTHON_SCRIPT"
        echo "Please ensure jira_webhook_trigger.py is in the same directory"
        exit 1
    fi
}

# Check if virtual environment is available
check_virtual_env() {
    if [[ -d "$SCRIPT_DIR/venv" ]]; then
        print_info "Activating virtual environment..."
        source "$SCRIPT_DIR/venv/bin/activate"
    elif [[ -n "$VIRTUAL_ENV" ]]; then
        print_info "Using existing virtual environment: $VIRTUAL_ENV"
    else
        print_warning "No virtual environment detected"
    fi
}

# Check if LangGraph server is running
check_langgraph_server() {
    local webhook_url="${WEBHOOK_URL:-http://localhost:8000/webhook/jira}"
    local base_url=$(echo "$webhook_url" | sed 's|/webhook/jira||')
    
    if curl -s "$base_url/health" > /dev/null 2>&1; then
        print_status "LangGraph server is running at $base_url"
        return 0
    else
        print_warning "LangGraph server not responding at $base_url"
        print_info "Start the server with: python src/server.py"
        return 1
    fi
}

# Show help
show_help() {
    cat << EOF
🚀 Jira Webhook Trigger Helper Script

USAGE:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    ticket <KEY>        Process specific Jira ticket (e.g., DEVOPS-123)
    search <JQL>        Search tickets using JQL query
    sample              Use sample tickets for testing
    interactive         Interactive mode for ticket selection
    status              Check server status and recent activity
    help                Show this help message

OPTIONS:
    --no-send           Generate curl commands without sending webhooks
    --max-results N     Maximum number of tickets to process (default: 10)
    --webhook-url URL   Override webhook URL
    --dry-run           Show what would be done without doing it
    --verbose           Enable verbose output

EXAMPLES:
    # Process a specific ticket
    $0 ticket DEVOPS-123

    # Search for automation-related tickets
    $0 search "labels in (automation) AND status = 'To Do'"

    # Use sample tickets for testing
    $0 sample

    # Interactive mode
    $0 interactive

    # Check server status
    $0 status

    # Generate commands without sending
    $0 ticket DEVOPS-123 --no-send

ENVIRONMENT VARIABLES:
    JIRA_URL            Your Jira instance URL
    JIRA_USERNAME       Your Jira username/email
    JIRA_TOKEN          Your Jira API token
    JIRA_PROJECT_KEY    Default project key (default: DEVOPS)
    WEBHOOK_URL         LangGraph webhook URL (default: http://localhost:8000/webhook/jira)

SETUP:
    1. Copy .env.example to .env and configure your Jira credentials
    2. Start LangGraph server: python src/server.py
    3. Run this script with your desired command

EOF
}

# Interactive mode
interactive_mode() {
    print_header "Interactive Jira Webhook Trigger"
    echo
    
    while true; do
        echo "Choose an option:"
        echo "1. 🎯 Process specific ticket"
        echo "2. 🔍 Search tickets with JQL"
        echo "3. 🧪 Use sample tickets"
        echo "4. 📊 Check server status"
        echo "5. 🔧 Quick setup guide"
        echo "6. 🚪 Exit"
        echo
        
        read -p "Enter your choice (1-6): " choice
        
        case $choice in
            1)
                read -p "Enter Jira ticket key (e.g., DEVOPS-123): " ticket_key
                if [[ -n "$ticket_key" ]]; then
                    python3 "$PYTHON_SCRIPT" --ticket "$ticket_key"
                else
                    print_warning "No ticket key provided"
                fi
                ;;
            2)
                echo "Examples of JQL queries:"
                echo "  project = DEVOPS AND status = 'To Do'"
                echo "  labels in (automation) AND created >= -7d"
                echo "  assignee = currentUser() AND priority = High"
                echo
                read -p "Enter JQL query: " jql_query
                if [[ -n "$jql_query" ]]; then
                    read -p "Max results [10]: " max_results
                    max_results=${max_results:-10}
                    python3 "$PYTHON_SCRIPT" --jql "$jql_query" --max-results "$max_results"
                else
                    print_warning "No JQL query provided"
                fi
                ;;
            3)
                python3 "$PYTHON_SCRIPT" --sample
                ;;
            4)
                check_server_status
                ;;
            5)
                show_setup_guide
                ;;
            6)
                print_status "Goodbye! 👋"
                exit 0
                ;;
            *)
                print_warning "Invalid choice. Please select 1-6."
                ;;
        esac
        
        echo
        read -p "Press Enter to continue..."
        echo
    done
}

# Check server status
check_server_status() {
    print_header "Server Status Check"
    echo
    
    local webhook_url="${WEBHOOK_URL:-http://localhost:8000/webhook/jira}"
    local base_url=$(echo "$webhook_url" | sed 's|/webhook/jira||')
    
    # Check main server
    print_info "Checking LangGraph server..."
    if curl -s "$base_url/health" > /dev/null 2>&1; then
        print_status "LangGraph server is running at $base_url"
        
        # Get server info
        server_info=$(curl -s "$base_url/" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f\"Service: {data.get('service', 'Unknown')}\")
    print(f\"Version: {data.get('version', 'Unknown')}\")
except:
    print('Server info not available')
" 2>/dev/null)
        echo "   $server_info"
        
    else
        print_error "LangGraph server not responding at $base_url"
        print_info "Start with: python src/server.py"
    fi
    
    # Check Todo app servers
    print_info "Checking Todo app servers..."
    
    # Backend
    if curl -s "http://localhost:3001/health" > /dev/null 2>&1; then
        print_status "Todo backend running at http://localhost:3001"
    else
        print_warning "Todo backend not running at http://localhost:3001"
        print_info "Start with: cd todo-app/backend && npm run dev"
    fi
    
    # Frontend
    if curl -s "http://localhost:3000" > /dev/null 2>&1; then
        print_status "Todo frontend running at http://localhost:3000"
    else
        print_warning "Todo frontend not running at http://localhost:3000"
        print_info "Start with: cd todo-app/frontend && npm start"
    fi
    
    # Check recent activity
    print_info "Recent automation activity..."
    if [[ -f "logs/devops_autocoder.log" ]]; then
        echo "Last 5 log entries:"
        tail -5 logs/devops_autocoder.log | while read line; do
            echo "   $line"
        done
    else
        echo "   No log file found"
    fi
    
    # Check generated reports
    if [[ -d "reports" && -n "$(ls -A reports 2>/dev/null)" ]]; then
        echo
        echo "Generated reports:"
        ls -la reports/ | tail -5 | while read line; do
            echo "   $line"
        done
    else
        echo "   No reports generated yet"
    fi
}

# Show setup guide
show_setup_guide() {
    print_header "Quick Setup Guide"
    echo
    
    echo "🔧 Step 1: Environment Configuration"
    if [[ -f ".env" ]]; then
        print_status ".env file exists"
        echo "   Current configuration:"
        grep -E "^(JIRA_URL|JIRA_USERNAME|WEBHOOK_URL)" .env 2>/dev/null | while read line; do
            key=$(echo "$line" | cut -d'=' -f1)
            value=$(echo "$line" | cut -d'=' -f2-)
            if [[ "$key" == "JIRA_TOKEN" ]]; then
                echo "   $key=****"
            else
                echo "   $line"
            fi
        done
    else
        print_warning ".env file not found"
        echo "   Create .env file with:"
        echo "   JIRA_URL=https://your-company.atlassian.net"
        echo "   JIRA_USERNAME=your.email@company.com"
        echo "   JIRA_TOKEN=your-api-token"
        echo "   WEBHOOK_URL=http://localhost:8000/webhook/jira"
    fi
    
    echo
    echo "🔑 Step 2: Jira API Token"
    echo "   1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens"
    echo "   2. Create API token for 'LangGraph DevOps'"
    echo "   3. Add token to .env file as JIRA_TOKEN"
    
    echo
    echo "🚀 Step 3: Start Services"
    echo "   1. LangGraph server: python src/server.py"
    echo "   2. Todo backend: cd todo-app/backend && npm run dev"
    echo "   3. Todo frontend: cd todo-app/frontend && npm start"
    
    echo
    echo "🧪 Step 4: Test with Sample Tickets"
    echo "   Run: $0 sample"
    
    echo
    echo "🔗 Step 5: Connect Real Jira (Optional)"
    echo "   1. Configure webhook in Jira: Settings → System → WebHooks"
    echo "   2. URL: http://your-ngrok-url.ngrok.io/webhook/jira"
    echo "   3. Events: Issue Created, Issue Updated"
}

# Generate sample JQL queries
suggest_jql_queries() {
    print_header "Sample JQL Queries"
    echo
    
    echo "📋 Common automation queries:"
    echo "1. Recent automation tickets:"
    echo "   labels in (automation) AND created >= -7d"
    echo
    echo "2. Open development tasks:"
    echo "   project = DEVOPS AND status = \"To Do\" AND assignee in (currentUser())"
    echo
    echo "3. High priority bugs:"
    echo "   priority = High AND issuetype = Bug"
    echo
    echo "4. Export-related features:"
    echo "   text ~ \"export\" OR text ~ \"download\" OR text ~ \"csv\""
    echo
    echo "5. UI/Frontend tasks:"
    echo "   labels in (frontend, ui) AND status != Done"
    echo
    echo "6. Recently updated tickets:"
    echo "   updated >= -1d ORDER BY updated DESC"
}

# Validate environment
validate_environment() {
    print_info "Validating environment..."
    
    local issues=0
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found"
        ((issues++))
    fi
    
    # Check required Python packages
    python3 -c "import requests, jira" 2>/dev/null || {
        print_warning "Required Python packages not installed"
        echo "   Install with: pip install requests jira python-dotenv"
        ((issues++))
    }
    
    # Check .env file
    if [[ ! -f ".env" ]]; then
        print_warning ".env file not found"
        echo "   Copy .env.example to .env and configure"
        ((issues++))
    fi
    
    # Check Jira configuration
    if [[ -z "${JIRA_URL:-}" ]]; then
        print_warning "JIRA_URL not configured"
        ((issues++))
    fi
    
    if [[ $issues -eq 0 ]]; then
        print_status "Environment validation passed"
        return 0
    else
        print_warning "Found $issues environment issues"
        return 1
    fi
}

# Watch logs in real-time
watch_logs() {
    print_header "Watching LangGraph Automation Logs"
    echo "Press Ctrl+C to stop"
    echo
    
    if [[ -f "logs/devops_autocoder.log" ]]; then
        tail -f logs/devops_autocoder.log | while read line; do
            # Colorize log levels
            if [[ $line == *"ERROR"* ]]; then
                echo -e "${RED}$line${NC}"
            elif [[ $line == *"WARNING"* ]]; then
                echo -e "${YELLOW}$line${NC}"
            elif [[ $line == *"INFO"* ]]; then
                echo -e "${BLUE}$line${NC}"
            elif [[ $line == *"SUCCESS"* ]] || [[ $line == *"✅"* ]]; then
                echo -e "${GREEN}$line${NC}"
            else
                echo "$line"
            fi
        done
    else
        print_warning "Log file not found: logs/devops_autocoder.log"
        print_info "Start LangGraph server to generate logs"
    fi
}

# Monitor automation progress
monitor_progress() {
    print_header "Monitoring Automation Progress"
    echo
    
    while true; do
        clear
        echo "🔄 Live Automation Monitor (Press Ctrl+C to exit)"
        echo "Updated: $(date)"
        echo "=" * 60
        
        # Server status
        check_langgraph_server && echo
        
        # Recent activity
        if [[ -f "logs/devops_autocoder.log" ]]; then
            echo "📊 Recent Activity (last 5 entries):"
            tail -5 logs/devops_autocoder.log | while read line; do
                echo "   $line"
            done
            echo
        fi
        
        # File changes
        if [[ -d "todo-app" ]]; then
            echo "📁 Recent File Changes:"
            find todo-app -name "*.jsx" -o -name "*.js" -o -name "*.css" | \
            xargs ls -lt 2>/dev/null | head -5 | while read line; do
                echo "   $line"
            done
            echo
        fi
        
        # Reports
        if [[ -d "reports" ]] && [[ -n "$(ls -A reports 2>/dev/null)" ]]; then
            echo "📋 Generated Reports:"
            ls -lt reports/ | head -3 | while read line; do
                echo "   $line"
            done
        fi
        
        sleep 10
    done
}

# Main script logic
main() {
    check_python_script
    check_virtual_env
    
    # Handle no arguments
    if [[ $# -eq 0 ]]; then
        show_help
        exit 0
    fi
    
    local command="$1"
    shift
    
    case "$command" in
        "ticket"|"t")
            if [[ $# -eq 0 ]]; then
                print_error "Ticket key required"
                echo "Usage: $0 ticket <KEY>"
                exit 1
            fi
            local ticket_key="$1"
            shift
            check_langgraph_server
            python3 "$PYTHON_SCRIPT" --ticket "$ticket_key" "$@"
            ;;
        "search"|"s")
            if [[ $# -eq 0 ]]; then
                print_error "JQL query required"
                echo "Usage: $0 search <JQL>"
                suggest_jql_queries
                exit 1
            fi
            local jql_query="$1"
            shift
            check_langgraph_server
            python3 "$PYTHON_SCRIPT" --jql "$jql_query" "$@"
            ;;
        "sample"|"demo")
            check_langgraph_server
            python3 "$PYTHON_SCRIPT" --sample "$@"
            ;;
        "interactive"|"i")
            interactive_mode
            ;;
        "status"|"st")
            check_server_status
            ;;
        "setup")
            show_setup_guide
            ;;
        "validate"|"check")
            validate_environment
            ;;
        "logs"|"log")
            watch_logs
            ;;
        "monitor"|"watch")
            monitor_progress
            ;;
        "jql"|"queries")
            suggest_jql_queries
            ;;
        "help"|"h"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
    