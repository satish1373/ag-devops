#!/bin/bash

# Server Status Monitor for LangGraph DevOps Automation
# Checks if all required servers are running and healthy

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    if [ "$2" = "OK" ]; then
        echo -e "${GREEN}✅ $1${NC}"
    elif [ "$2" = "WARNING" ]; then
        echo -e "${YELLOW}⚠️ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
    fi
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

check_port() {
    local port=$1
    local name=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
        return 0
    else
        return 1
    fi
}

check_http() {
    local url=$1
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|404"; then
        return 0
    else
        return 1
    fi
}

get_ngrok_url() {
    curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    tunnels = data.get('tunnels', [])
    for tunnel in tunnels:
        if tunnel.get('config', {}).get('addr') == 'http://localhost:8000':
            print(tunnel['public_url'])
            break
except:
    pass
" 2>/dev/null
}

main() {
    clear
    echo "🔍 LangGraph DevOps Automation - Server Status Monitor"
    echo "======================================================"
    echo "$(date)"
    echo ""

    # Check if we're in the right directory
    if [ ! -f "src/server.py" ] || [ ! -d "todo-app" ]; then
        print_status "Wrong directory! Please run from langgraph-devops-autocoder/" "ERROR"
        echo "Current directory: $(pwd)"
        exit 1
    fi

    print_header "📋 Project Structure Check"
    
    if [ -f "todo-app/backend/server.js" ]; then
        print_status "Backend server file exists" "OK"
    else
        print_status "Backend server.js missing" "ERROR"
    fi
    
    if [ -f "todo-app/frontend/src/App.jsx" ]; then
        print_status "Frontend App.jsx exists" "OK"
    else
        print_status "Frontend App.jsx missing" "ERROR"
    fi
    
    if [ -f "src/server.py" ]; then
        print_status "Automation server.py exists" "OK"
    else
        print_status "Automation server.py missing" "ERROR"
    fi

    echo ""
    print_header "🔌 Port Status Check"

    # Check Backend (Port 3001)
    if check_port 3001; then
        print_status "Backend Server (Port 3001)" "OK"
        
        # Test backend health
        if check_http "http://localhost:3001/health"; then
            print_status "  └─ Backend API responding" "OK"
        else
            print_status "  └─ Backend API not responding" "ERROR"
        fi
    else
        print_status "Backend Server (Port 3001) - Not running" "ERROR"
        echo "  💡 Start with: cd todo-app/backend && npm start"
    fi

    # Check Frontend (Port 3000)
    if check_port 3000; then
        print_status "Frontend Server (Port 3000)" "OK"
        
        if check_http "http://localhost:3000"; then
            print_status "  └─ Frontend app responding" "OK"
        else
            print_status "  └─ Frontend app not responding" "WARNING"
        fi
    else
        print_status "Frontend Server (Port 3000) - Not running" "ERROR"
        echo "  💡 Start with: cd todo-app/frontend && npm start"
    fi

    # Check Automation Server (Port 8000)
    if check_port 8000; then
        print_status "Automation Server (Port 8000)" "OK"
        
        if check_http "http://localhost:8000/health"; then
            print_status "  └─ Automation API responding" "OK"
        else
            print_status "  └─ Automation API not responding" "ERROR"
        fi
    else
        print_status "Automation Server (Port 8000) - Not running" "ERROR"
        echo "  💡 Start with: python src/server.py"
    fi

    # Check Ngrok (Port 4040)
    if check_port 4040; then
        print_status "Ngrok Tunnel (Port 4040)" "OK"
        
        NGROK_URL=$(get_ngrok_url)
        if [ -n "$NGROK_URL" ]; then
            print_status "  └─ Public URL: $NGROK_URL" "OK"
            
            # Test external access
            if curl -s -o /dev/null -w "%{http_code}" "$NGROK_URL/health" | grep -q "200"; then
                print_status "  └─ External access working" "OK"
            else
                print_status "  └─ External access failed" "ERROR"
            fi
        else
            print_status "  └─ No active tunnel found" "WARNING"
        fi
    else
        print_status "Ngrok Tunnel - Not running" "ERROR"
        echo "  💡 Start with: ngrok http 8000"
    fi

    echo ""
    print_header "🔗 Integration Tests"

    # Test backend-frontend connection
    if check_port 3001 && check_port 3000; then
        # Check if frontend can reach backend
        BACKEND_RESPONSE=$(curl -s http://localhost:3001/api/todos 2>/dev/null)
        if echo "$BACKEND_RESPONSE" | grep -q "\["; then
            print_status "Frontend ↔ Backend connection" "OK"
        else
            print_status "Frontend ↔ Backend connection" "ERROR"
        fi
    else
        print_status "Frontend ↔ Backend connection - Can't test (servers not running)" "WARNING"
    fi

    # Test automation webhook
    if check_port 8000; then
        WEBHOOK_RESPONSE=$(curl -s -X POST http://localhost:8000/webhook/jira \
            -H "Content-Type: application/json" \
            -d '{"test": true}' 2>/dev/null)
        
        if echo "$WEBHOOK_RESPONSE" | grep -q "error\|success"; then
            print_status "Automation webhook endpoint" "OK"
        else
            print_status "Automation webhook endpoint" "ERROR"
        fi
    else
        print_status "Automation webhook endpoint - Can't test (server not running)" "WARNING"
    fi

    echo ""
    print_header "📊 System Resources"

    # Check Python virtual environment
    if [ -n "$VIRTUAL_ENV" ]; then
        print_status "Python virtual environment active" "OK"
    else
        print_status "Python virtual environment not active" "WARNING"
        echo "  💡 Activate with: source venv/bin/activate"
    fi

    # Check Node.js processes
    NODE_PROCESSES=$(ps aux | grep -E "(node|npm)" | grep -v grep | wc -l)
    if [ "$NODE_PROCESSES" -gt 0 ]; then
        print_status "Node.js processes running: $NODE_PROCESSES" "OK"
    else
        print_status "No Node.js processes running" "WARNING"
    fi

    # Check Python processes
    PYTHON_PROCESSES=$(ps aux | grep -E "python.*server.py" | grep -v grep | wc -l)
    if [ "$PYTHON_PROCESSES" -gt 0 ]; then
        print_status "Python automation processes: $PYTHON_PROCESSES" "OK"
    else
        print_status "No Python automation processes running" "WARNING"
    fi

    echo ""
    print_header "📝 Quick Access URLs"
    echo "🎨 Todo App:           http://localhost:3000"
    echo "🗄️ Backend API:        http://localhost:3001/health"
    echo "🤖 Automation Server:  http://localhost:8000"
    echo "📊 Ngrok Dashboard:    http://localhost:4040"
    
    if [ -n "$NGROK_URL" ]; then
        echo "🌐 Public Webhook URL: $NGROK_URL/webhook/jira"
    fi

    echo ""
    print_header "🚀 Quick Start Commands"
    echo "Start all servers:"
    echo "  Terminal 1: cd todo-app/backend && npm start"
    echo "  Terminal 2: cd todo-app/frontend && npm start"
    echo "  Terminal 3: source venv/bin/activate && python src/server.py"
    echo "  Terminal 4: ngrok http 8000"

    echo ""
    print_header "🧪 Test Automation"
    echo "Create a test Jira ticket or run:"
    echo "curl -X POST http://localhost:8000/webhook/jira \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"issue\":{\"key\":\"TEST-1\",\"fields\":{\"summary\":\"test export\",\"description\":\"add export button\",\"issuetype\":{\"name\":\"Story\"}}}}'"

    echo ""
    echo "🔄 Auto-refresh in 30 seconds... (Ctrl+C to stop)"
}

# Run once, then auto-refresh
main

# Auto-refresh every 30 seconds
while true; do
    sleep 30
    main
done