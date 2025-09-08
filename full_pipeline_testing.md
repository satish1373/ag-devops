# Complete Pipeline Testing Guide for LangGraph DevOps Autocoder

## Prerequisites Setup

Before testing the full pipeline, ensure you have:

### 1. Copy the Main LangGraph Code
```bash
# Copy the LangGraph multi-agent system code to src/main.py
# (Use the code from the first artifact I provided)
```

### 2. Install Additional Dependencies
```bash
# Make sure you have all required packages
pip install langgraph langchain langchain-openai httpx GitPython jira pytest pytest-asyncio playwright python-dotenv pydantic fastapi uvicorn aiofiles structlog
```

### 3. Update Your .env File
```env
# Jira Configuration (get these from your Jira instance)
JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your-email@domain.com
JIRA_TOKEN=your-jira-api-token
JIRA_WEBHOOK_SECRET=your-webhook-secret

# GitHub Configuration
GITHUB_TOKEN=your-github-personal-access-token
GITHUB_WEBHOOK_SECRET=your-github-webhook-secret
GITHUB_REPO=your-username/your-repo-name

# Application Configuration
APP_NAME=todo-app
DEPLOYMENT_URL_BASE=https://app.example.com

# OpenAI Configuration (optional for enhanced LLM features)
OPENAI_API_KEY=your-openai-api-key

# Logging
LOG_LEVEL=INFO
```

## Phase 1: Basic Server Testing

### Step 1: Start the Development Server
```bash
# Activate your virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start the FastAPI server
python src/server.py
```

You should see:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Test Basic Endpoints
Open a new terminal and test:

```bash
# Test health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"devops-autocoder"}

# Test root endpoint
curl http://localhost:8000/

# Expected response:
# {"service":"LangGraph DevOps Autocoder","version":"1.0.0","endpoints":{...}}
```

## Phase 2: Webhook Integration Testing

### Step 3: Test Webhook Processing

#### Option A: Using curl
```bash
curl -X POST http://localhost:8000/webhook/jira \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=test_signature" \
  -d '{
    "issue": {
      "key": "PROJ-123",
      "fields": {
        "summary": "Add todo priority feature",
        "issuetype": {"name": "Story"},
        "description": "Add priority field to todos with UI updates and database changes"
      }
    }
  }'
```

#### Option B: Using VSCode REST Client
Create `tests/webhook_test.http`:
```http
### Test Jira Webhook - Basic
POST http://localhost:8000/webhook/jira
Content-Type: application/json
X-Hub-Signature-256: sha256=test_signature

{
    "issue": {
        "key": "PROJ-123",
        "fields": {
            "summary": "Add todo priority feature",
            "issuetype": {"name": "Story"},
            "description": "Add priority field to todos with UI updates and database changes"
        }
    }
}

### Test Jira Webhook - Complex Story
POST http://localhost:8000/webhook/jira
Content-Type: application/json
X-Hub-Signature-256: sha256=test_signature

{
    "issue": {
        "key": "PROJ-124",
        "fields": {
            "summary": "Implement user authentication",
            "issuetype": {"name": "Epic"},
            "description": "Create login system with JWT tokens, password reset, and user registration. Needs database changes and UI updates."
        }
    }
}

### Test Jira Webhook - Bug Fix
POST http://localhost:8000/webhook/jira
Content-Type: application/json
X-Hub-Signature-256: sha256=test_signature

{
    "issue": {
        "key": "PROJ-125",
        "fields": {
            "summary": "Fix todo deletion not working",
            "issuetype": {"name": "Bug"},
            "description": "Delete button in todo list is not working. API endpoint returns 500 error."
        }
    }
}
```

### Step 4: Monitor Pipeline Execution

#### Check Server Logs
In your server terminal, you should see detailed logs like:
```
INFO - [abc-123-def] Starting DevOps automation pipeline
INFO - [abc-123-def] Starting webhook verification
INFO - [abc-123-def] Verification successful for PROJ-123
INFO - [abc-123-def] Analyzing requirements
INFO - [abc-123-def] Creating implementation plan
INFO - [abc-123-def] Generating code
...
```

#### Check Generated Files
Monitor the following directories for generated content:
```bash
# Watch for generated reports
ls -la reports/

# Check logs
tail -f logs/devops_autocoder.log

# Look for generated code (if Git integration is working)
git status
git log --oneline
```

## Phase 3: End-to-End Pipeline Verification

### Step 5: Verify Each Agent's Output

#### Requirements Analysis
Check that the system extracted requirements:
```json
{
  "functional": ["Create new functionality"],
  "technical": ["API modifications required"],
  "ui_changes": ["UI modifications required"],
  "api_changes": ["New API endpoint required"],
  "database_changes": ["Database schema changes"],
  "priority": "medium"
}
```

#### Code Generation
Look for generated files in the response or file system:
- React components (`src/components/TodoList.jsx`)
- API routes (`server/routes/todos.js`)
- CSS styles (`src/styles/main.css`)
- Database migrations (`migrations/add_new_fields.sql`)

#### Test Suite Creation
Verify test files are generated:
- Unit tests (`tests/unit/todoController.test.js`)
- Integration tests (`tests/integration/todos.test.js`)
- E2E tests (`tests/e2e/todoFlow.test.js`)

### Step 6: Test Different Issue Types

#### Story Test
```bash
curl -X POST http://localhost:8000/webhook/jira \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=test" \
  -d '{
    "issue": {
      "key": "STORY-001",
      "fields": {
        "summary": "Add todo categories",
        "issuetype": {"name": "Story"},
        "description": "Users should be able to categorize their todos into Work, Personal, Shopping, etc."
      }
    }
  }'
```

#### Bug Test
```bash
curl -X POST http://localhost:8000/webhook/jira \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=test" \
  -d '{
    "issue": {
      "key": "BUG-001",
      "fields": {
        "summary": "Todo completion status not saving",
        "issuetype": {"name": "Bug"},
        "description": "When users mark a todo as complete, the status reverts back to incomplete after page refresh."
      }
    }
  }'
```

#### Epic Test
```bash
curl -X POST http://localhost:8000/webhook/jira \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=test" \
  -d '{
    "issue": {
      "key": "EPIC-001",
      "fields": {
        "summary": "Mobile app support",
        "issuetype": {"name": "Epic"},
        "description": "Create mobile responsive version of the todo app with touch interfaces and offline support."
      }
    }
  }'
```

## Phase 4: Advanced Testing Scenarios

### Step 7: Test Error Handling

#### Invalid Webhook Signature
```bash
curl -X POST http://localhost:8000/webhook/jira \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=invalid_signature" \
  -d '{"issue": {"key": "TEST-ERROR"}}'
```

#### Malformed JSON
```bash
curl -X POST http://localhost:8000/webhook/jira \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=test" \
  -d '{"invalid": "json", "missing": "issue"}'
```

#### Missing Required Fields
```bash
curl -X POST http://localhost:8000/webhook/jira \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=test" \
  -d '{
    "issue": {
      "fields": {
        "summary": "Missing issue key"
      }
    }
  }'
```

### Step 8: Load Testing

#### Concurrent Webhook Processing
```bash
# Test multiple webhooks simultaneously
for i in {1..5}; do
  curl -X POST http://localhost:8000/webhook/jira \
    -H "Content-Type: application/json" \
    -H "X-Hub-Signature-256: sha256=test" \
    -d "{
      \"issue\": {
        \"key\": \"LOAD-$i\",
        \"fields\": {
          \"summary\": \"Load test issue $i\",
          \"issuetype\": {\"name\": \"Story\"},
          \"description\": \"Testing concurrent processing of issue $i\"
        }
      }
    }" &
done
wait
```

## Phase 5: Integration Testing

### Step 9: Test with Real Jira (Optional)

If you have access to a real Jira instance:

#### Configure Webhook in Jira
1. Go to Jira Settings → System → Webhooks
2. Create new webhook with URL: `http://your-server:8000/webhook/jira`
3. Select events: Issue Created, Issue Updated
4. Add secret for webhook signing

#### Create Test Issues
1. Create a new Story in Jira
2. Watch your server logs for automatic processing
3. Check generated reports in `/reports/` directory

### Step 10: Monitor Full Pipeline

#### Real-time Monitoring
```bash
# Monitor logs in real-time
tail -f logs/devops_autocoder.log

# Watch for file changes
watch -n 1 'ls -la reports/ && echo "---" && ls -la src/components/ 2>/dev/null || echo "No components yet"'

# Monitor Git activity (if configured)
watch -n 2 'git status --porcelain'
```

#### Check Pipeline Metrics
After running several tests, verify:

```bash
# Count processed issues
grep "Pipeline completed" logs/devops_autocoder.log | wc -l

# Check error rate
grep "ERROR" logs/devops_autocoder.log | wc -l

# List generated reports
ls -la reports/

# Check Jira updates (if configured)
grep "Jira update" logs/devops_autocoder.log
```

## Phase 6: Performance and Quality Testing

### Step 11: Validate Generated Code Quality

#### Check Generated React Components
```bash
# If code was generated, validate syntax
npx eslint src/components/TodoList.jsx || echo "No React code generated yet"

# Check CSS validity
npx stylelint src/styles/main.css || echo "No CSS generated yet"
```

#### Validate Generated Tests
```bash
# Check if generated tests are valid
python -m pytest tests/unit/ -v --collect-only 2>/dev/null || echo "No unit tests generated yet"
```

### Step 12: End-to-End Verification

#### Complete Workflow Test
```bash
# Run a complete test with verification
curl -X POST http://localhost:8000/webhook/jira \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=test" \
  -d '{
    "issue": {
      "key": "E2E-001",
      "fields": {
        "summary": "Complete workflow test",
        "issuetype": {"name": "Story"},
        "description": "This is a comprehensive test of the entire DevOps pipeline from webhook to deployment."
      }
    }
  }' | jq '.'
```

#### Verify Response Structure
Expected response format:
```json
{
  "status": "success",
  "trace_id": "uuid-here",
  "message": "Webhook processed successfully"
}
```

## Phase 7: Troubleshooting Common Issues

### Step 13: Debug Common Problems

#### Import Errors
```bash
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Test imports manually
python -c "from src.main import process_jira_webhook; print('Import successful')"
```

#### LangGraph Issues
```bash
# Verify LangGraph installation
python -c "import langgraph; print(f'LangGraph version: {langgraph.__version__}')"

# Test basic graph creation
python -c "from langgraph.graph import StateGraph; print('StateGraph import successful')"
```

#### Missing Dependencies
```bash
# Check all required packages
pip list | grep -E "(langgraph|langchain|jira|httpx|fastapi)"

# Reinstall if needed
pip install --upgrade langgraph langchain jira httpx fastapi uvicorn
```

## Success Criteria Checklist

After completing all tests, verify:

- [ ] ✅ Webhook signature verification works
- [ ] ✅ Issue information is correctly extracted
- [ ] ✅ Requirements analysis produces structured output
- [ ] ✅ Code generation creates valid files
- [ ] ✅ UI tweaks are applied
- [ ] ✅ Test suites are generated
- [ ] ✅ Git integration works (if configured)
- [ ] ✅ CI/CD pipeline executes
- [ ] ✅ Deployment simulation completes
- [ ] ✅ Health monitoring functions
- [ ] ✅ Jira updates are logged
- [ ] ✅ Final reports are generated
- [ ] ✅ Audit trail is complete
- [ ] ✅ Error handling works correctly
- [ ] ✅ Multiple issue types are supported
- [ ] ✅ Concurrent processing works

## Expected Output Files

After successful testing, you should have:

```
reports/
├── PROJ-123.md
├── STORY-001.md
├── BUG-001.md
└── EPIC-001.md

logs/
└── devops_autocoder.log

src/components/          # (if Git integration is configured)
├── TodoList.jsx
└── TodoItem.jsx

tests/
├── unit/
├── integration/
└── e2e/
```

## Next Steps

Once pipeline testing is complete:

1. **Configure Real Integrations** - Set up actual Jira webhooks
2. **Deploy to Production** - Use Docker/Kubernetes
3. **Set Up Monitoring** - Add metrics and alerting
4. **Scale Testing** - Test with larger volumes
5. **Customize Agents** - Modify agents for your specific needs

Your LangGraph DevOps Autocoder is now fully tested and ready for production use!