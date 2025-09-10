#!/bin/bash

# Complete Setup and Run Script for LangGraph DevOps Autocoder
# This script sets up and runs the entire system

set -e

echo "🚀 LangGraph DevOps Autocoder - Complete Setup"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Check if Python 3.9+ is installed
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
            print_status "Python $PYTHON_VERSION found"
            return 0
        else
            print_error "Python 3.9+ required, found $PYTHON_VERSION"
            return 1
        fi
    else
        print_error "Python 3 not found"
        return 1
    fi
}

# Check if Node.js is installed
check_node() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_status "Node.js $NODE_VERSION found"
        return 0
    else
        print_error "Node.js not found"
        return 1
    fi
}

# Create directory structure
create_directories() {
    print_info "Creating directory structure..."
    
    directories=(
        "src"
        "src/utils"
        "tests"
        "logs"
        "reports"
        "backups"
        "todo-app"
        "todo-app/frontend/src/components"
        "todo-app/backend"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        print_status "Created directory: $dir"
    done
}

# Create necessary Python files
create_python_files() {
    print_info "Creating Python configuration files..."
    
    # Create __init__.py files
    touch src/__init__.py
    touch src/utils/__init__.py
    touch tests/__init__.py
    
    # Create requirements.txt
    cat > requirements.txt << 'EOF'
fastapi>=0.104.0
uvicorn>=0.24.0
python-dotenv>=1.0.0
requests>=2.31.0
aiofiles>=23.2.0
GitPython>=3.1.40
jira>=3.5.0
pydantic>=2.4.0
httpx>=0.25.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
structlog>=23.1.0
pathlib
EOF

    # Create .env file
    cat > .env << 'EOF'
# Jira Configuration
JIRA_URL=https://example.atlassian.net
JIRA_USERNAME=test@example.com
JIRA_TOKEN=test-token
JIRA_WEBHOOK_SECRET=test-secret

# GitHub Configuration
GITHUB_TOKEN=test-github-token
GITHUB_WEBHOOK_SECRET=test-github-secret
GITHUB_REPO=test/repo

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

# Logging
LOG_LEVEL=INFO
EOF

    # Create config.py
    cat > src/config.py << 'EOF'
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    # Jira Configuration
    jira_url: str = os.getenv("JIRA_URL", "https://example.atlassian.net")
    jira_username: str = os.getenv("JIRA_USERNAME", "test@example.com")
    jira_token: str = os.getenv("JIRA_TOKEN", "test-token")
    jira_webhook_secret: str = os.getenv("JIRA_WEBHOOK_SECRET", "test-secret")
    
    # GitHub Configuration
    github_token: str = os.getenv("GITHUB_TOKEN", "test-github-token")
    github_webhook_secret: str = os.getenv("GITHUB_WEBHOOK_SECRET", "test-github-secret")
    github_repo: str = os.getenv("GITHUB_REPO", "test/repo")
    
    # Application Configuration
    app_name: str = os.getenv("APP_NAME", "todo-app")
    deployment_url_base: str = os.getenv("DEPLOYMENT_URL_BASE", "https://app.example.com")
    
    # Project paths
    project_root: str = os.getenv("PROJECT_ROOT", ".")
    frontend_path: str = os.getenv("FRONTEND_PATH", "todo-app/frontend")
    backend_path: str = os.getenv("BACKEND_PATH", "todo-app/backend")
    
    # Development server URLs
    frontend_dev_url: str = os.getenv("FRONTEND_DEV_URL", "http://localhost:3000")
    backend_dev_url: str = os.getenv("BACKEND_DEV_URL", "http://localhost:3001")

config = Config()
EOF

    # Create logger.py
    cat > src/utils/logger.py << 'EOF'
import logging
import sys
from pathlib import Path

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Setup structured logger with file and console output"""
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(name)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler('logs/devops_autocoder.log')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger
EOF

    print_status "Python configuration files created"
}

# Setup Python virtual environment
setup_python_env() {
    print_info "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_status "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_status "Virtual environment activated"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    print_info "Installing Python dependencies..."
    pip install -r requirements.txt
    print_status "Python dependencies installed"
}

# Create a simple Todo app for testing
create_todo_app() {
    print_info "Creating simple Todo app for testing..."
    
    # Create backend package.json
    cat > todo-app/backend/package.json << 'EOF'
{
  "name": "todo-backend",
  "version": "1.0.0",
  "description": "Simple Todo Backend for Testing",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "sqlite3": "^5.1.6"
  }
}
EOF

    # Create simple backend server
    cat > todo-app/backend/server.js << 'EOF'
const express = require('express');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// In-memory database for simplicity
const db = new sqlite3.Database(':memory:');

// Initialize database
db.serialize(() => {
  db.run(`CREATE TABLE todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    completed BOOLEAN DEFAULT 0,
    priority TEXT DEFAULT 'medium',
    category TEXT DEFAULT 'general',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )`);
  
  // Insert sample data
  db.run("INSERT INTO todos (title, description, priority) VALUES (?, ?, ?)", 
    ["Welcome to Todo App", "This is your first todo item", "high"]);
  db.run("INSERT INTO todos (title, description, priority) VALUES (?, ?, ?)", 
    ["Test the export feature", "Try the CSV export functionality", "medium"]);
});

// Routes
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

app.get('/api/todos', (req, res) => {
  db.all('SELECT * FROM todos ORDER BY created_at DESC', (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(rows);
  });
});

app.post('/api/todos', (req, res) => {
  const { title, description, priority = 'medium', category = 'general' } = req.body;
  
  if (!title) {
    return res.status(400).json({ error: 'Title is required' });
  }
  
  db.run(
    'INSERT INTO todos (title, description, priority, category) VALUES (?, ?, ?, ?)',
    [title, description, priority, category],
    function(err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      
      db.get('SELECT * FROM todos WHERE id = ?', [this.lastID], (err, row) => {
        if (err) {
          return res.status(500).json({ error: err.message });
        }
        res.status(201).json(row);
      });
    }
  );
});

app.put('/api/todos/:id', (req, res) => {
  const { id } = req.params;
  const { title, description, completed, priority, category } = req.body;
  
  db.run(
    `UPDATE todos SET 
     title = COALESCE(?, title),
     description = COALESCE(?, description),
     completed = COALESCE(?, completed),
     priority = COALESCE(?, priority),
     category = COALESCE(?, category)
     WHERE id = ?`,
    [title, description, completed, priority, category, id],
    function(err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      
      if (this.changes === 0) {
        return res.status(404).json({ error: 'Todo not found' });
      }
      
      db.get('SELECT * FROM todos WHERE id = ?', [id], (err, row) => {
        if (err) {
          return res.status(500).json({ error: err.message });
        }
        res.json(row);
      });
    }
  );
});

app.delete('/api/todos/:id', (req, res) => {
  const { id } = req.params;
  
  db.run('DELETE FROM todos WHERE id = ?', [id], function(err) {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    
    if (this.changes === 0) {
      return res.status(404).json({ error: 'Todo not found' });
    }
    
    res.json({ message: 'Todo deleted successfully' });
  });
});

app.listen(PORT, () => {
  console.log(`✅ Todo Backend Server running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
});
EOF

    # Create frontend structure
    mkdir -p todo-app/frontend/src/components
    mkdir -p todo-app/frontend/public
    
    # Create package.json for frontend
    cat > todo-app/frontend/package.json << 'EOF'
{
  "name": "todo-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
EOF

    # Create basic React app files
    cat > todo-app/frontend/public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Todo App - LangGraph DevOps Demo</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
EOF

    cat > todo-app/frontend/src/index.js << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
EOF

    cat > todo-app/frontend/src/App.jsx << 'EOF'
import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [todos, setTodos] = useState([])
  const [loading, setLoading] = useState(true)
  const [newTodo, setNewTodo] = useState('')

  useEffect(() => {
    fetchTodos()
  }, [])

  const fetchTodos = async () => {
    try {
      const response = await fetch('http://localhost:3001/api/todos')
      const data = await response.json()
      setTodos(data)
    } catch (error) {
      console.error('Failed to fetch todos:', error)
    } finally {
      setLoading(false)
    }
  }

  const addTodo = async () => {
    if (!newTodo.trim()) return
    
    try {
      const response = await fetch('http://localhost:3001/api/todos', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title: newTodo, priority: 'medium' }),
      })
      
      if (response.ok) {
        const todo = await response.json()
        setTodos([todo, ...todos])
        setNewTodo('')
      }
    } catch (error) {
      console.error('Failed to add todo:', error)
    }
  }

  const toggleTodo = async (id, completed) => {
    try {
      const response = await fetch(`http://localhost:3001/api/todos/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ completed }),
      })
      
      if (response.ok) {
        const updatedTodo = await response.json()
        setTodos(todos.map(todo => 
          todo.id === id ? updatedTodo : todo
        ))
      }
    } catch (error) {
      console.error('Failed to update todo:', error)
    }
  }

  const deleteTodo = async (id) => {
    if (!window.confirm('Are you sure you want to delete this todo?')) {
      return
    }
    
    try {
      const response = await fetch(`http://localhost:3001/api/todos/${id}`, {
        method: 'DELETE',
      })
      
      if (response.ok) {
        setTodos(todos.filter(todo => todo.id !== id))
      }
    } catch (error) {
      console.error('Failed to delete todo:', error)
    }
  }

  if (loading) {
    return <div className="loading">Loading todos...</div>
  }

  return (
    <div className="app">
      <header className="header">
        <h1>🚀 Todo App</h1>
        <p>Powered by LangGraph DevOps Automation</p>
      </header>
      
      <main className="main-content">
        <div className="add-todo">
          <input
            type="text"
            value={newTodo}
            onChange={(e) => setNewTodo(e.target.value)}
            placeholder="What needs to be done?"
            onKeyPress={(e) => e.key === 'Enter' && addTodo()}
          />
          <button onClick={addTodo}>Add Todo</button>
        </div>
        
        <div className="filter-info">
          <p>Total todos: {todos.length}</p>
        </div>
        
        <div className="todos">
          {todos.map(todo => (
            <div key={todo.id} className={`todo-item ${todo.completed ? 'completed' : ''} priority-${todo.priority}`}>
              <input
                type="checkbox"
                checked={todo.completed}
                onChange={(e) => toggleTodo(todo.id, e.target.checked)}
              />
              <div className="todo-content">
                <span className="todo-title">{todo.title}</span>
                {todo.description && <span className="todo-description">{todo.description}</span>}
                <div className="todo-meta">
                  <span className="priority">{todo.priority}</span>
                  <span className="category">{todo.category}</span>
                  <span className="date">{new Date(todo.created_at).toLocaleDateString()}</span>
                </div>
              </div>
              <button 
                onClick={() => deleteTodo(todo.id)}
                className="delete-btn"
                title="Delete todo"
              >
                🗑️
              </button>
            </div>
          ))}
        </div>
        
        {todos.length === 0 && (
          <div className="empty-state">
            <p>No todos yet. Add one above!</p>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
EOF

    # Create CSS file
    cat > todo-app/frontend/src/App.css << 'EOF'
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  color: #333;
}

.app {
  min-height: 100vh;
  padding: 20px;
}

.header {
  text-align: center;
  color: white;
  margin-bottom: 30px;
}

.header h1 {
  font-size: 2.5rem;
  margin-bottom: 10px;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.header p {
  font-size: 1.1rem;
  opacity: 0.9;
}

.main-content {
  max-width: 800px;
  margin: 0 auto;
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}

.add-todo {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.add-todo input {
  flex: 1;
  padding: 12px;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  font-size: 16px;
}

.add-todo input:focus {
  outline: none;
  border-color: #667eea;
}

.add-todo button {
  padding: 12px 24px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.add-todo button:hover {
  background: #5a67d8;
}

.filter-info {
  text-align: center;
  margin-bottom: 20px;
  color: #666;
  font-size: 14px;
}

.todos {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.todo-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  transition: all 0.2s;
  background: white;
}

.todo-item:hover {
  border-color: #dee2e6;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.todo-item.completed {
  opacity: 0.7;
  background: #f8f9fa;
}

.todo-item.priority-high {
  border-left: 6px solid #dc3545;
  background: linear-gradient(90deg, #fff5f5 0%, #ffffff 10%);
}

.todo-item.priority-medium {
  border-left: 6px solid #ffc107;
  background: linear-gradient(90deg, #fffdf0 0%, #ffffff 10%);
}

.todo-item.priority-low {
  border-left: 6px solid #28a745;
  background: linear-gradient(90deg, #f0fff4 0%, #ffffff 10%);
}

.todo-content {
  flex: 1;
}

.todo-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
  display: block;
  color: #2d3748;
}

.todo-item.completed .todo-title {
  text-decoration: line-through;
  color: #718096;
}

.todo-description {
  font-size: 14px;
  color: #4a5568;
  margin-bottom: 8px;
  display: block;
}

.todo-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 12px;
}

.priority, .category, .date {
  padding: 2px 6px;
  border-radius: 10px;
  background: #e2e8f0;
  color: #4a5568;
}

.priority {
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s;
}

.delete-btn:hover {
  background: #fed7d7;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #718096;
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  font-size: 18px;
  color: white;
}

@media (max-width: 768px) {
  .app {
    padding: 10px;
  }
  
  .main-content {
    padding: 20px;
  }
  
  .header h1 {
    font-size: 2rem;
  }
  
  .add-todo {
    flex-direction: column;
  }
  
  .todo-item {
    flex-direction: column;
    gap: 10px;
  }
  
  .delete-btn {
    align-self: flex-end;
  }
  
  .todo-meta {
    gap: 4px;
  }
}
EOF

    print_status "Todo app structure created"
}

# Install Node.js dependencies
install_node_deps() {
    print_info "Installing Node.js dependencies..."
    
    # Install backend dependencies
    if [ -d "todo-app/backend" ]; then
        cd todo-app/backend
        if command -v npm &> /dev/null; then
            npm install
            print_status "Backend dependencies installed"
        else
            print_warning "npm not found, skipping backend dependencies"
        fi
        cd ../..
    fi
    
    # Install frontend dependencies
    if [ -d "todo-app/frontend" ]; then
        cd todo-app/frontend
        if command -v npm &> /dev/null; then
            npm install
            print_status "Frontend dependencies installed"
        else
            print_warning "npm not found, skipping frontend dependencies"
        fi
        cd ../..
    fi
}

# Create startup scripts
create_startup_scripts() {
    print_info "Creating startup scripts..."
    
    # Create start-all script
    cat > start-all.sh << 'EOF'
#!/bin/bash

# Start all services for LangGraph DevOps Autocoder

echo "🚀 Starting LangGraph DevOps Autocoder System"
echo "============================================"

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️ Port $1 is already in use"
        return 1
    else
        return 0
    fi
}

# Activate Python virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Python virtual environment activated"
else
    echo "❌ Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Start backend server
if [ -d "todo-app/backend" ] && [ -f "todo-app/backend/server.js" ]; then
    if check_port 3001; then
        echo "🔧 Starting backend server..."
        cd todo-app/backend
        node server.js &
        BACKEND_PID=$!
        echo "✅ Backend server started (PID: $BACKEND_PID)"
        cd ../..
        sleep 2
    fi
else
    echo "⚠️ Backend server not found"
fi

# Start frontend server
if [ -d "todo-app/frontend" ] && [ -f "todo-app/frontend/package.json" ]; then
    if check_port 3000; then
        echo "🎨 Starting frontend server..."
        cd todo-app/frontend
        npm start &
        FRONTEND_PID=$!
        echo "✅ Frontend server started (PID: $FRONTEND_PID)"
        cd ../..
        sleep 3
    fi
else
    echo "⚠️ Frontend server not found"
fi

# Start LangGraph DevOps server
if check_port 8000; then
    echo "🤖 Starting LangGraph DevOps Autocoder server..."
    python enhanced_server.py &
    LANGGRAPH_PID=$!
    echo "✅ LangGraph server started (PID: $LANGGRAPH_PID)"
    sleep 2
fi

echo ""
echo "🎉 All services started!"
echo "================================"
echo "📱 Frontend:     http://localhost:3000"
echo "🔧 Backend API:  http://localhost:3001"
echo "🤖 LangGraph:    http://localhost:8000"
echo "📊 Health Check: http://localhost:8000/health"
echo ""
echo "💡 Quick tests:"
echo "curl -X POST http://localhost:8000/test/export"
echo "curl -X POST http://localhost:8000/test/search"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait and handle shutdown
trap 'echo ""; echo "🛑 Shutting down services..."; kill $BACKEND_PID $FRONTEND_PID $LANGGRAPH_PID 2>/dev/null; exit' INT

# Keep script running
wait
EOF

    # Create stop-all script
    cat > stop-all.sh << 'EOF'
#!/bin/bash

echo "🛑 Stopping all LangGraph DevOps services..."

# Kill processes on specific ports
for port in 3000 3001 8000; do
    PID=$(lsof -ti:$port)
    if [ ! -z "$PID" ]; then
        kill $PID 2>/dev/null
        echo "✅ Stopped service on port $port"
    else
        echo "ℹ️ No service running on port $port"
    fi
done

echo "✅ All services stopped"
EOF

    # Create test script
    cat > test-system.sh << 'EOF'
#!/bin/bash

echo "🧪 Testing LangGraph DevOps Autocoder System"
echo "==========================================="

# Test health endpoint
echo "1. Testing health endpoint..."
curl -s http://localhost:8000/health | jq . || echo "Health check failed"

echo ""
echo "2. Testing export functionality..."
curl -X POST http://localhost:8000/test/export | jq . || echo "Export test failed"

echo ""
echo "3. Testing search functionality..."
curl -X POST http://localhost:8000/test/search | jq . || echo "Search test failed"

echo ""
echo "4. Checking generated files..."
curl -s http://localhost:8000/files | jq . || echo "Files check failed"

echo ""
echo "✅ System tests completed!"
EOF

    # Make scripts executable
    chmod +x start-all.sh stop-all.sh test-system.sh
    
    print_status "Startup scripts created"
}

# Main installation function
main() {
    print_info "Starting complete setup process..."
    
    # Check prerequisites
    if ! check_python; then
        print_error "Python 3.9+ is required. Please install it first."
        exit 1
    fi
    
    if ! check_node; then
        print_warning "Node.js not found. Some features may not work."
    fi
    
    # Create directory structure
    create_directories
    
    # Create Python files
    create_python_files
    
    # Setup Python environment
    setup_python_env
    
    # Create Todo app
    create_todo_app
    
    # Install Node dependencies if available
    if command -v npm &> /dev/null; then
        install_node_deps
    else
        print_warning "npm not available, skipping Node.js dependencies"
    fi
    
    # Create startup scripts
    create_startup_scripts
    
    # Final instructions
    echo ""
    print_status "🎉 Setup completed successfully!"
    echo ""
    print_info "Next steps:"
    echo "1. Copy the enhanced LangGraph system code to src/main.py"
    echo "2. Copy the enhanced server code to enhanced_server.py"
    echo "3. Run: ./start-all.sh"
    echo "4. Test: ./test-system.sh"
    echo ""
    print_info "URLs after startup:"
    echo "• Frontend:  http://localhost:3000"
    echo "• Backend:   http://localhost:3001"
    echo "• LangGraph: http://localhost:8000"
    echo ""
    print_info "Quick tests:"
    echo "• curl -X POST http://localhost:8000/test/export"
    echo "• curl -X POST http://localhost:8000/test/search"
    echo ""
    print_status "Ready for LangGraph DevOps automation! 🚀"
}

# Run main function
main "$@"