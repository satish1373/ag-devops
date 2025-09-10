#!/bin/bash

# Enhanced Jira Webhook Simulator
# Simulates realistic Jira workflows for testing LangGraph DevOps Autocoder

echo "🎭 Enhanced Jira Webhook Simulator"
echo "=================================="

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

# Check if LangGraph server is running
check_server() {
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_status "LangGraph server is running"
        return 0
    else
        print_error "LangGraph server not running. Start with ./start-all.sh"
        return 1
    fi
}

# Generate realistic Jira issue key
generate_issue_key() {
    local project_key="$1"
    local number=$((RANDOM % 999 + 100))
    echo "${project_key}-${number}"
}

# Send webhook with realistic Jira payload
send_webhook() {
    local issue_key="$1"
    local summary="$2" 
    local description="$3"
    local issue_type="${4:-Story}"
    local priority="${5:-Medium}"
    local assignee="${6:-automation-bot}"
    
    print_info "Creating Jira issue: $issue_key"
    echo "📋 Summary: $summary"
    echo "📝 Type: $issue_type | Priority: $priority"
    echo ""
    
    # Realistic Jira webhook payload
    local webhook_payload=$(cat << EOF
{
    "timestamp": $(date +%s)000,
    "webhookEvent": "jira:issue_created",
    "issue_event_type_name": "issue_created",
    "user": {
        "self": "https://company.atlassian.net/rest/api/2/user?username=$assignee",
        "name": "$assignee",
        "emailAddress": "${assignee}@company.com",
        "displayName": "Automation Bot",
        "active": true
    },
    "issue": {
        "id": "$((RANDOM % 99999 + 10000))",
        "self": "https://company.atlassian.net/rest/api/2/issue/$((RANDOM % 99999 + 10000))",
        "key": "$issue_key",
        "fields": {
            "summary": "$summary",
            "description": "$description",
            "issuetype": {
                "self": "https://company.atlassian.net/rest/api/2/issuetype/10001",
                "id": "10001",
                "name": "$issue_type",
                "subtask": false
            },
            "priority": {
                "self": "https://company.atlassian.net/rest/api/2/priority/3",
                "id": "3",
                "name": "$priority"
            },
            "status": {
                "self": "https://company.atlassian.net/rest/api/2/status/10000",
                "id": "10000",
                "name": "To Do",
                "statusCategory": {
                    "id": 2,
                    "name": "To Do"
                }
            },
            "project": {
                "id": "10000",
                "key": "DEVOPS",
                "name": "DevOps Automation",
                "projectTypeKey": "software"
            },
            "assignee": {
                "name": "$assignee",
                "emailAddress": "${assignee}@company.com",
                "displayName": "Automation Bot"
            },
            "creator": {
                "name": "product-manager",
                "emailAddress": "pm@company.com", 
                "displayName": "Product Manager"
            },
            "created": "$(date -Iseconds)",
            "updated": "$(date -Iseconds)",
            "labels": ["automation", "frontend", "devops"]
        }
    },
    "changelog": {
        "id": "$((RANDOM % 99999))",
        "items": [
            {
                "field": "status",
                "fieldtype": "jira",
                "from": null,
                "fromString": null,
                "to": "10000",
                "toString": "To Do"
            }
        ]
    }
}
EOF
)

    # Send webhook
    local response=$(curl -s -X POST http://localhost:8000/webhook/jira \
        -H "Content-Type: application/json" \
        -H "X-Atlassian-Webhook-Identifier: $(uuidgen)" \
        -H "X-Hub-Signature-256: sha256=test" \
        -d "$webhook_payload")
    
    if echo "$response" | grep -q "accepted"; then
        print_status "✅ Webhook sent successfully"
        echo "📡 Response: $response"
        echo ""
        
        # Wait a moment for processing
        sleep 2
        
        # Check processing status
        print_info "Checking automation status..."
        local status_response=$(curl -s "http://localhost:8000/status/$issue_key")
        if echo "$status_response" | grep -q "completed"; then
            print_status "Automation completed successfully"
            echo "$status_response" | python3 -m json.tool 2>/dev/null || echo "$status_response"
        else
            print_warning "Automation still processing or failed"
            echo "$status_response"
        fi
        
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        return 0
    else
        print_error "Failed to send webhook"
        echo "Response: $response"
        return 1
    fi
}

# Predefined realistic test scenarios
scenario_export_feature() {
    print_info "🎯 Scenario 1: CSV Export Feature Request"
    local issue_key=$(generate_issue_key "DEVOPS")
    send_webhook "$issue_key" \
        "Add CSV export functionality to todo dashboard" \
        "As a user, I want to export my todos to CSV format so I can analyze them in Excel. The export should include all todo details: title, description, priority, category, completion status, and creation date. The button should show the number of todos being exported." \
        "Story" \
        "High" \
        "frontend-dev"
}

scenario_search_feature() {
    print_info "🎯 Scenario 2: Real-time Search Implementation"
    local issue_key=$(generate_issue_key "DEVOPS")
    send_webhook "$issue_key" \
        "Implement real-time search and filtering for todos" \
        "Add a search bar that allows users to filter todos in real-time. The search should work on both title and description fields. Include a clear button to reset the search. Show filtered count vs total count." \
        "Story" \
        "Medium" \
        "frontend-dev"
}

scenario_notification_system() {
    print_info "🎯 Scenario 3: Notification System"
    local issue_key=$(generate_issue_key "DEVOPS")
    send_webhook "$issue_key" \
        "Add notification system with due date alerts" \
        "Implement a notification system that shows alerts for overdue todos. Add due date fields and visual indicators for urgent tasks. Include notification badges and priority-based color coding." \
        "Story" \
        "High" \
        "fullstack-dev"
}

scenario_ui_enhancement() {
    print_info "🎯 Scenario 4: UI/UX Enhancement"
    local issue_key=$(generate_issue_key "DEVOPS")
    send_webhook "$issue_key" \
        "Enhance priority color scheme and visual design" \
        "Update the priority color system to be more accessible and visually appealing. High priority should be red, medium yellow, low green. Add better contrast and hover effects. Improve overall styling and responsiveness." \
        "Task" \
        "Low" \
        "ui-designer"
}

scenario_bug_fix() {
    print_info "🎯 Scenario 5: Critical Bug Fix"
    local issue_key=$(generate_issue_key "DEVOPS")
    send_webhook "$issue_key" \
        "Fix todo deletion confirmation dialog styling" \
        "The delete confirmation dialog is not properly styled and hard to read. Update the styling to match the application theme and ensure good contrast for accessibility." \
        "Bug" \
        "High" \
        "frontend-dev"
}

scenario_performance() {
    print_info "🎯 Scenario 6: Performance Optimization"
    local issue_key=$(generate_issue_key "DEVOPS")
    send_webhook "$issue_key" \
        "Optimize todo list rendering performance" \
        "The todo list becomes slow with many items. Implement virtualization or pagination for large todo lists. Add loading states and optimize re-rendering when todos are updated." \
        "Improvement" \
        "Medium" \
        "senior-dev"
}

# Custom scenario
scenario_custom() {
    echo ""
    print_info "🎨 Create Custom Scenario"
    echo ""
    
    read -p "📋 Issue Summary: " summary
    read -p "📝 Description: " description
    read -p "🏷️  Issue Type (Story/Task/Bug): " issue_type
    read -p "⚡ Priority (Low/Medium/High): " priority
    
    local issue_key=$(generate_issue_key "CUSTOM")
    send_webhook "$issue_key" "$summary" "$description" "${issue_type:-Story}" "${priority:-Medium}" "custom-user"
}

# Batch testing
run_batch_tests() {
    print_info "🚀 Running Batch Test Scenarios"
    echo ""
    
    scenario_export_feature
    sleep 3
    
    scenario_search_feature  
    sleep 3
    
    scenario_ui_enhancement
    sleep 3
    
    print_status "Batch testing completed!"
    echo ""
    print_info "Check your Todo app at http://localhost:3000 to see the changes!"
}

# Monitor ongoing automation
monitor_automation() {
    print_info "📊 Monitoring Active Automations"
    echo ""
    
    echo "🔍 Recent Activity:"
    curl -s http://localhost:8000/logs?lines=20 | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for log in data['logs'][-10:]:
        print(f'  {log}')
except:
    print('  No recent logs available')
"
    
    echo ""
    echo "📁 Generated Files:"
    curl -s http://localhost:8000/files | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for file in data['files'][:10]:
        print(f'  📄 {file[\"path\"]} ({file[\"size\"]} bytes)')
    if data['total'] > 10:
        print(f'  ... and {data[\"total\"] - 10} more files')
except:
    print('  No files information available')
"
    
    echo ""
    echo "💾 Backup Status:"
    curl -s http://localhost:8000/backups | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'  Total backup sessions: {data[\"total\"]}')
    for backup in data['backups'][:3]:
        print(f'  🗃️  {backup[\"trace_id\"]} - {len(backup[\"files\"])} files backed up')
except:
    print('  No backup information available')
"
}

# Main menu
show_menu() {
    echo ""
    print_info "🎭 Jira Webhook Simulator - Test Scenarios"
    echo ""
    echo "Choose a test scenario:"
    echo ""
    echo "1. 📤 CSV Export Feature (Export todos to CSV)"
    echo "2. 🔍 Real-time Search (Filter todos by text)"  
    echo "3. 🔔 Notification System (Due date alerts)"
    echo "4. 🎨 UI Enhancement (Priority colors & styling)"
    echo "5. 🐛 Bug Fix (Delete dialog styling)"
    echo "6. ⚡ Performance (List optimization)"
    echo "7. 🎨 Custom Scenario (Create your own)"
    echo "8. 🚀 Batch Test (Run multiple scenarios)"
    echo "9. 📊 Monitor Activity (Check status)"
    echo "10. 🔗 Setup Real Jira (Connection guide)"
    echo "0. 🚪 Exit"
    echo ""
}

# Real Jira setup guide
setup_real_jira() {
    print_info "🔗 Setting Up Real Jira Integration"
    echo ""
    echo "To connect to your real Jira instance:"
    echo ""
    echo "1. 🔑 Get your Jira API token:"
    echo "   → Go to: https://id.atlassian.com/manage-profile/security/api-tokens"
    echo "   → Create API token for 'LangGraph DevOps'"
    echo ""
    echo "2. 🌐 Expose your local server:"
    echo "   → Install ngrok: brew install ngrok (or download from ngrok.com)"
    echo "   → Run: ngrok http 8000"
    echo "   → Copy the https URL (e.g., https://abc123.ngrok.io)"
    echo ""
    echo "3. ⚙️ Configure Jira webhook:"
    echo "   → Go to: Jira Settings → System → WebHooks"
    echo "   → Create webhook with URL: https://your-ngrok-url.ngrok.io/webhook/jira"
    echo "   → Select events: Issue Created, Issue Updated"
    echo ""
    echo "4. 📝 Update your .env file:"
    echo "   → JIRA_URL=https://yourcompany.atlassian.net"
    echo "   → JIRA_USERNAME=your.email@company.com"
    echo "   → JIRA_TOKEN=your-api-token"
    echo ""
    echo "5. 🎯 Create test issues in Jira with automation keywords:"
    echo "   → Use words like: export, search, filter, notification"
    echo "   → Add labels: automation, frontend, devops"
    echo ""
    print_status "Then create issues normally in Jira and watch the automation happen!"
}

# Main execution
main() {
    if ! check_server; then
        exit 1
    fi
    
    while true; do
        show_menu
        read -p "Enter your choice (0-10): " choice
        
        case $choice in
            1) scenario_export_feature ;;
            2) scenario_search_feature ;;
            3) scenario_notification_system ;;
            4) scenario_ui_enhancement ;;
            5) scenario_bug_fix ;;
            6) scenario_performance ;;
            7) scenario_custom ;;
            8) run_batch_tests ;;
            9) monitor_automation ;;
            10) setup_real_jira ;;
            0) 
                print_status "Thanks for testing LangGraph DevOps Autocoder! 🚀"
                exit 0
                ;;
            *)
                print_warning "Invalid choice. Please select 0-10."
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Run the simulator
main "$@"