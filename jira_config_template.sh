#!/bin/bash

# Jira Integration Setup Script
# Creates configuration files and sets up Jira webhook integration

set -e

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

echo "🔧 Jira Integration Setup for LangGraph DevOps"
echo "=============================================="

# Create .env.example template
create_env_template() {
    cat > .env.example << 'EOF'
# Jira Configuration
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your.email@company.com
JIRA_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=DEVOPS
JIRA_WEBHOOK_SECRET=your-webhook-secret

# GitHub Configuration (optional)
GITHUB_TOKEN=your-github-token
GITHUB_WEBHOOK_SECRET=your-github-webhook-secret
GITHUB_REPO=your-username/your-repo

# Application Configuration
APP_NAME=todo-app
DEPLOYMENT_URL_BASE=https://app.example.com

# Project Paths
PROJECT_ROOT=.
FRONTEND_PATH=todo-app/frontend
BACKEND_PATH=todo-app/backend

# Development Server URLs
FRONTEND_DEV_URL=http://localhost:3000
BACKEND_DEV_URL=http://localhost:3001

# LangGraph Configuration
WEBHOOK_URL=http://localhost:8000/webhook/jira
OPENAI_API_KEY=your-openai-api-key

# Logging
LOG_LEVEL=INFO
EOF

    print_status "Created .env.example template"
}

# Interactive configuration
interactive_setup() {
    print_info "Starting interactive Jira configuration..."
    echo
    
    # Get Jira details
    read -p "Enter your Jira URL (e.g., https://company.atlassian.net): " jira_url
    read -p "Enter your Jira username/email: " jira_username
    echo "Get your API token from: https://id.atlassian.com/manage-profile/security/api-tokens"
    read -s -p "Enter your Jira API token: " jira_token
    echo
    read -p "Enter your Jira project key [DEVOPS]: " jira_project
    jira_project=${jira_project:-DEVOPS}
    
    # Generate webhook secret
    webhook_secret=$(openssl rand -hex 16 2>/dev/null || echo "$(date +%s)-secret")
    
    # Optional OpenAI API key
    echo
    print_info "OpenAI API key is optional but enables enhanced AI-powered code generation"
    read -p "Enter OpenAI API key (or press Enter to skip): " openai_key
    
    # Create .env file
    cat > .env << EOF
# Jira Configuration
JIRA_URL=$jira_url
JIRA_USERNAME=$jira_username
JIRA_TOKEN=$jira_token
JIRA_PROJECT_KEY=$jira_project
JIRA_WEBHOOK_SECRET=$webhook_secret

# GitHub Configuration (optional)
GITHUB_TOKEN=
GITHUB_WEBHOOK_SECRET=
GITHUB_REPO=

# Application Configuration
APP_NAME=todo-app
DEPLOYMENT_URL_BASE=https://app.example.com

# Project Paths
PROJECT_ROOT=.
FRONTEND_PATH=todo-app/frontend
BACKEND_PATH=todo-app/backend

# Development Server URLs
FRONTEND_DEV_URL=http://localhost:3000
BACKEND_DEV_URL=http://localhost:3001

# LangGraph Configuration
WEBHOOK_URL=http://localhost:8000/webhook/jira
OPENAI_API_KEY=$openai_key

# Logging
LOG_LEVEL=INFO
EOF

    print_status "Created .env configuration file"
}

# Test Jira connection
test_jira_connection() {
    print_info "Testing Jira connection..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found"
        return 1
    fi
    
    # Test connection with Python
    python3 - << 'EOF'
import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from jira import JIRA
    
    jira_url = os.getenv("JIRA_URL")
    jira_username = os.getenv("JIRA_USERNAME") 
    jira_token = os.getenv("JIRA_TOKEN")
    
    if not all([jira_url, jira_username, jira_token]):
        print("❌ Missing Jira configuration")
        sys.exit(1)
    
    jira = JIRA(server=jira_url, basic_auth=(jira_username, jira_token))
    
    # Test by getting user info
    user = jira.current_user()
    print(f"✅ Connected to Jira as: {user}")
    
    # Test project access
    project_key = os.getenv("JIRA_PROJECT_KEY", "DEVOPS")
    try:
        project = jira.project(project_key)
        print(f"✅ Project access confirmed: {project.name}")
    except:
        print(f"⚠️ Cannot access project {project_key} (may not exist)")
    
except ImportError:
    print("❌ python-jira not installed. Run: pip install jira")
    sys.exit(1)
except Exception as e:
    print(f"❌ Jira connection failed: {e}")
    sys.exit(1)
EOF

    if [[ $? -eq 0 ]]; then
        print_status "Jira connection test passed"
        return 0
    else
        print_error "Jira connection test failed"
        return 1
    fi
}

# Create sample JQL queries file
create_sample_queries() {
    cat > jql_queries.txt << 'EOF'
# Sample JQL Queries for LangGraph DevOps Automation
# Use these with: ./jira_trigger.sh search "<query>"

# Recent automation-related tickets
labels in (automation) AND created >= -7d

# Open development tasks assigned to you
project = DEVOPS AND status = "To Do" AND assignee = currentUser()

# High priority bugs
priority = High AND issuetype = Bug AND status != Done

# Export and download features
text ~ "export" OR text ~ "download" OR text ~ "csv"

# UI and frontend related tasks
labels in (frontend, ui) AND status in ("To Do", "In Progress")

# Recently updated tickets
updated >= -1d ORDER BY updated DESC

# Stories ready for automation
issuetype = Story AND labels in (automation) AND status = "To Do"

# Critical issues
priority = Highest OR labels in (critical, urgent)

# Search by component
component = "Frontend" AND status != Done

# Search by epic
"Epic Link" = DEVOPS-100

# Advanced: Complex automation queries
project = DEVOPS AND (
    (issuetype = Story AND labels in (automation, frontend)) OR
    (issuetype = Bug AND priority in (High, Highest)) OR
    (text ~ "export" AND status = "To Do")
) ORDER BY priority DESC, created ASC
EOF

    print_status "Created jql_queries.txt with sample queries"
}

# Create webhook test script
create_webhook_test() {
    cat > test_webhook.sh << 'EOF'
#!/bin/bash

# Test webhook connectivity and payload format

WEBHOOK_URL="${WEBHOOK_URL:-http://localhost:8000/webhook/jira}"
echo "Testing webhook at: $WEBHOOK_URL"

# Test health endpoint
echo "🔍 Testing server health..."
if curl -s "${WEBHOOK_URL%/webhook/jira}/health" | grep -q "healthy"; then
    echo "✅ Server is healthy"
else
    echo "❌ Server health check failed"
    exit 1
fi

# Test webhook endpoint with sample payload
echo "🚀 Testing webhook endpoint..."
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-Atlassian-Webhook-Identifier: test-webhook" \
  -H "X-Hub-Signature-256: sha256=test" \
  -d '{
    "timestamp": '$(date +%s)'000,
    "webhookEvent": "jira:issue_created",
    "issue": {
      "key": "TEST-001",
      "fields": {
        "summary": "Test webhook connectivity",
        "description": "This is a test webhook to verify connectivity",
        "issuetype": {"name": "Task"},
        "priority": {"name": "Medium"},
        "status": {"name": "To Do"}
      }
    }
  }' \
  -w "\nHTTP Status: %{http_code}\n"
EOF

    chmod +x test_webhook.sh
    print_status "Created test_webhook.sh script"
}

# Create Jira webhook configuration guide
create_webhook_guide() {
    cat > jira_webhook_setup.md << 'EOF'
# Jira Webhook Setup Guide

## 1. Create Webhook in Jira

1. Go to **Jira Settings** → **System** → **WebHooks**
2. Click **Create a WebHook**

## 2. Configure Webhook

**Name:** LangGraph DevOps Automation

**URL:** 
- For local development: `http://your-ngrok-url.ngrok.io/webhook/jira`
- For production: `https://your-domain.com/webhook/jira`

**Events to trigger:**
- [x] Issue Created
- [x] Issue Updated
- [x] Issue Deleted (optional)

**JQL Filter (optional):**
```
project = DEVOPS AND labels in (automation)
```

## 3. Webhook Security

**Secret:** Use the `JIRA_WEBHOOK_SECRET` from your .env file

## 4. Testing

1. **Test locally with ngrok:**
   ```bash
   # Install ngrok
   brew install ngrok  # or download from ngrok.com
   
   # Expose local server
   ngrok http 8000
   
   # Use the https URL in Jira webhook configuration
   ```

2. **Test webhook:**
   ```bash
   ./test_webhook.sh
   ```

3. **Create test ticket in Jira:**
   - Create new issue with label "automation"
   - Watch LangGraph logs for processing

## 5. Monitoring

**View logs:**
```bash
tail -f logs/devops_autocoder.log
```

**Check recent activity:**
```bash
./jira_trigger.sh status
```

## 6. Troubleshooting

**Common Issues:**

1. **Webhook not triggered:**
   - Check JQL filter
   - Verify webhook URL is accessible
   - Check Jira webhook logs

2. **Authentication errors:**
   - Verify JIRA_TOKEN is correct
   - Check JIRA_USERNAME format

3. **Signature verification:**
   - Ensure JIRA_WEBHOOK_SECRET matches
   - Check webhook secret configuration

**Debug mode:**
```bash
export LOG_LEVEL=DEBUG
python src/server.py
```
EOF

    print_status "Created jira_webhook_setup.md guide"
}

# Main setup function
main() {
    echo "Choose setup option:"
    echo "1. 🔧 Interactive setup (recommended)"
    echo "2. 📝 Create template files only"
    echo "3. 🧪 Test existing configuration"
    echo "4. 📚 Create documentation only"
    echo
    read -p "Enter choice (1-4): " choice
    
    case $choice in
        1)
            create_env_template
            interactive_setup
            test_jira_connection
            create_sample_queries
            create_webhook_test
            create_webhook_guide
            
            echo
            print_status "Setup completed successfully!"
            echo
            echo "Next steps:"
            echo "1. Start LangGraph server: python src/server.py"
            echo "2. Test connection: ./jira_trigger.sh sample"
            echo "3. Process real tickets: ./jira_trigger.sh ticket DEVOPS-123"
            echo "4. Setup webhook: see jira_webhook_setup.md"
            ;;
        2)
            create_env_template
            print_info "Template created. Copy .env.example to .env and configure."
            ;;
        3)
            if [[ -f ".env" ]]; then
                test_jira_connection
            else
                print_error ".env file not found. Run interactive setup first."
            fi
            ;;
        4)
            create_sample_queries
            create_webhook_test 
            create_webhook_guide
            print_status "Documentation files created"
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
}

main "$@"