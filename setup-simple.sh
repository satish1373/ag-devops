#!/bin/bash

# Simple Windows Setup for LangGraph DevOps Autocoder

echo "🚀 LangGraph DevOps Autocoder - Simple Windows Setup"
echo "================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️ $1${NC}"; }

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check conda
    if ! command -v conda &> /dev/null; then
        print_error "Conda not found"
        return 1
    fi
    print_status "Conda found: $(conda --version)"
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js not found. Please install from https://nodejs.org/"
        return 1
    fi
    print_status "Node.js found: $(node --version)"
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm not found"
        return 1
    fi
    print_status "npm found: $(npm --version)"
    
    return 0
}

# Setup conda environment
setup_conda_env() {
    print_info "Setting up conda environment..."
    
    ENV_NAME="langgraph-devops"
    
    # Check if environment exists
    if conda env list | grep -q "$ENV_NAME"; then
        print_status "Conda environment already exists"
    else
        print_info "Creating conda environment: $ENV_NAME"
        conda create -n $ENV_NAME python=3.11 -y
        print_status "Conda environment created"
    fi
    
    # Install Python packages
    print_info "Installing Python packages..."
    conda run -n $ENV_NAME pip install fastapi uvicorn python-dotenv requests aiofiles GitPython jira pydantic httpx pytest pytest-asyncio structlog
    print_status "Python packages installed"
}

# Create directory structure
create_directories() {
    print_info "Creating directory structure..."
    
    directories=(
        "src" "src/utils" "tests" "logs" "reports" "backups"
        "todo-app" "todo-app/frontend/src/components" "todo-app/backend"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
    done
    
    print_status "Directory structure created"
}

# Create configuration files
create_config_files() {
    print_info "Creating configuration files..."
    
    # Create __init__.py files
    touch src/__init__.py src/utils/__init__.py tests/__init__.py
    
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
    jira_url: str = os.getenv("JIRA_URL", "https://example.atlassian.net")
    jira_username: str = os.getenv("JIRA_USERNAME", "test@example.com")
    jira_token: str = os.getenv("JIRA_TOKEN", "test-token")
    jira_webhook_secret: str = os.getenv("JIRA_WEBHOOK_SECRET", "test-secret")
    
    github_token: str = os.getenv("GITHUB_TOKEN", "test-github-token")
    github_webhook_secret: str = os.getenv("GITHUB_WEBHOOK_SECRET", "test-github-secret")
    github_repo: str = os.getenv("GITHUB_REPO", "test/repo")
    
    app_name: str = os.getenv("APP_NAME", "todo-app")
    deployment_url_base: str = os.getenv("DEPLOYMENT_URL_BASE", "https://app.example.com")
    
    project_root: str = os.getenv("PROJECT_ROOT", ".")
    frontend_path: str = os.getenv("FRONTEND_PATH", "todo-app/frontend")
    backend_path: str = os.getenv("BACKEND_PATH", "todo-app/backend")
    
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
    Path("logs").mkdir(exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if logger.handlers:
        return logger
    
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    
    file_handler = logging.FileHandler('logs/devops_autocoder.log')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger
EOF

    print_status "Configuration files created"
}

# Create Todo app
create_todo_app() {
    print_info "Creating Todo app..."
    
    # Backend package.json
    cat > todo-app/backend/package.json << 'EOF'
{
  "name": "todo-backend",
  "version": "1.0.0",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "sqlite3": "^5.1.6"
  }
}
EOF

    # Backend server
    cat > todo-app/backend/server.js << 'EOF'
const express = require('express');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();

const app = express();
const PORT = 3001;

app.use(cors());
app.use(express.json());

const db = new sqlite3.Database(':memory:');

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
  
  db.run("INSERT INTO todos (title, description, priority) VALUES (?, ?, ?)", 
    ["Welcome to Todo App", "Ready for automation!", "high"]);
  db.run("INSERT INTO todos (title, description, priority) VALUES (?, ?, ?)", 
    ["Test LangGraph", "Try the automation features", "medium"]);
});

app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

app.get('/api/todos', (req, res) => {
  db.all('SELECT * FROM todos ORDER BY created_at DESC', (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(rows);
  });
});

app.post('/api/todos', (req, res) => {
  const { title, description, priority = 'medium', category = 'general' } = req.body;
  if (!title) return res.status(400).json({ error: 'Title required' });
  
  db.run('INSERT INTO todos (title, description, priority, category) VALUES (?, ?, ?, ?)',
    [title, description, priority, category], function(err) {
      if (err) return res.status(500).json({ error: err.message });
      db.get('SELECT * FROM todos WHERE id = ?', [this.lastID], (err, row) => {
        if (err) return res.status(500).json({ error: err.message });
        res.status(201).json(row);
      });
    });
});

app.put('/api/todos/:id', (req, res) => {
  const { id } = req.params;
  const { title, description, completed, priority, category } = req.body;
  
  db.run(`UPDATE todos SET title = COALESCE(?, title), description = COALESCE(?, description),
     completed = COALESCE(?, completed), priority = COALESCE(?, priority),
     category = COALESCE(?, category) WHERE id = ?`,
    [title, description, completed, priority, category, id], function(err) {
      if (err) return res.status(500).json({ error: err.message });
      if (this.changes === 0) return res.status(404).json({ error: 'Not found' });
      db.get('SELECT * FROM todos WHERE id = ?', [id], (err, row) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(row);
      });
    });
});

app.delete('/api/todos/:id', (req, res) => {
  const { id } = req.params;
  db.run('DELETE FROM todos WHERE id = ?', [id], function(err) {
    if (err) return res.status(500).json({ error: err.message });
    if (this.changes === 0) return res.status(404).json({ error: 'Not found' });
    res.json({ message: 'Deleted successfully' });
  });
});

app.listen(PORT, () => {
  console.log(`✅ Backend running on http://localhost:${PORT}`);
});
EOF

    # Frontend files
    cat > todo-app/frontend/package.json << 'EOF'
{
  "name": "todo-frontend",
  "version": "0.1.0",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build"
  },
  "browserslist": {
    "production": [">0.2%", "not dead"],
    "development": ["last 1 chrome version"]
  }
}
EOF

    mkdir -p todo-app/frontend/public todo-app/frontend/src/components

    cat > todo-app/frontend/public/index.html << 'EOF'
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Todo App</title></head>
<body><div id="root"></div></body></html>
EOF

    cat > todo-app/frontend/src/index.js << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './App.css';

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
EOF

    cat > todo-app/frontend/src/App.jsx << 'EOF'
import { useState, useEffect } from 'react'

function App() {
  const [todos, setTodos] = useState([])
  const [loading, setLoading] = useState(true)
  const [newTodo, setNewTodo] = useState('')

  useEffect(() => { fetchTodos() }, [])

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
        headers: { 'Content-Type': 'application/json' },
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ completed }),
      })
      if (response.ok) {
        const updatedTodo = await response.json()
        setTodos(todos.map(todo => todo.id === id ? updatedTodo : todo))
      }
    } catch (error) {
      console.error('Failed to update todo:', error)
    }
  }

  const deleteTodo = async (id) => {
    if (!confirm('Delete this todo?')) return
    try {
      const response = await fetch(`http://localhost:3001/api/todos/${id}`, { method: 'DELETE' })
      if (response.ok) setTodos(todos.filter(todo => todo.id !== id))
    } catch (error) {
      console.error('Failed to delete todo:', error)
    }
  }

  if (loading) return <div className="loading">Loading...</div>

  return (
    <div className="app">
      <header className="header">
        <h1>🚀 Todo App</h1>
        <p>LangGraph DevOps Ready!</p>
      </header>
      <main className="main-content">
        <div className="add-todo">
          <input
            type="text"
            value={newTodo}
            onChange={(e) => setNewTodo(e.target.value)}
            placeholder="Add a todo..."
            onKeyPress={(e) => e.key === 'Enter' && addTodo()}
          />
          <button onClick={addTodo}>Add</button>
        </div>
        <div className="todos">
          {todos.map(todo => (
            <div key={todo.id} className={`todo-item ${todo.completed ? 'completed' : ''}`}>
              <input type="checkbox" checked={todo.completed} onChange={(e) => toggleTodo(todo.id, e.target.checked)} />
              <span className="todo-title">{todo.title}</span>
              <span className="priority">{todo.priority}</span>
              <button onClick={() => deleteTodo(todo.id)}>🗑️</button>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}

export default App
EOF

    cat > todo-app/frontend/src/App.css << 'EOF'
body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0; }
.app { min-height: 100vh; padding: 20px; }
.header { text-align: center; color: white; margin-bottom: 30px; }
.header h1 { font-size: 2.5rem; margin-bottom: 10px; }
.main-content { max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 30px; }
.add-todo { display: flex; gap: 10px; margin-bottom: 20px; }
.add-todo input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
.add-todo button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
.todos { display: flex; flex-direction: column; gap: 10px; }
.todo-item { display: flex; align-items: center; gap: 10px; padding: 10px; border: 1px solid #eee; border-radius: 4px; }
.todo-item.completed { opacity: 0.6; }
.todo-item.completed .todo-title { text-decoration: line-through; }
.todo-title { flex: 1; }
.priority { font-size: 12px; background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }
.loading { text-align: center; padding: 50px; }
EOF

    print_status "Todo app created"
}

# Create startup scripts
create_startup_scripts() {
    print_info "Creating startup scripts..."
    
    cat > start-all.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting LangGraph DevOps System"

# Start backend
cd todo-app/backend
npm install &>/dev/null
node server.js &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"
cd ../..

# Start frontend  
cd todo-app/frontend
npm install &>/dev/null
npm start &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"
cd ../..

# Start LangGraph server
conda run -n langgraph-devops python enhanced_server.py &
LANGGRAPH_PID=$!
echo "✅ LangGraph started (PID: $LANGGRAPH_PID)"

echo ""
echo "🎉 All services started!"
echo "Frontend:  http://localhost:3000"
echo "Backend:   http://localhost:3001"
echo "LangGraph: http://localhost:8000"
echo ""
echo "Test: curl -X POST http://localhost:8000/test/export"

trap 'kill $BACKEND_PID $FRONTEND_PID $LANGGRAPH_PID 2>/dev/null; exit' INT
wait
EOF

    cat > test-system.sh << 'EOF'
#!/bin/bash
echo "🧪 Testing system..."
curl -s http://localhost:8000/health && echo "✅ Health OK"
curl -s -X POST http://localhost:8000/test/export && echo "✅ Export test OK"
curl -s -X POST http://localhost:8000/test/search && echo "✅ Search test OK"
EOF

    chmod +x start-all.sh test-system.sh
    print_status "Startup scripts created"
}

# Main function
main() {
    if ! check_prerequisites; then
        print_error "Prerequisites not met"
        exit 1
    fi
    
    setup_conda_env
    create_directories  
    create_config_files
    create_todo_app
    create_startup_scripts
    
    echo ""
    print_status "🎉 Setup completed!"
    echo ""
    print_info "Next steps:"
    echo "1. Run: ./start-all.sh"
    echo "2. Test: ./test-system.sh" 
    echo ""
    print_info "URLs:"
    echo "• Frontend:  http://localhost:3000"
    echo "• Backend:   http://localhost:3001"
    echo "• LangGraph: http://localhost:8000"
    echo ""
    print_status "🚀 Ready!"
}

main "$@"