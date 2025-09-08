#!/bin/bash

# Anaconda Setup Script for LangGraph DevOps Autocoder

set -e

echo "🚀 LangGraph DevOps Autocoder - Anaconda Setup"
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

# Check if conda is available
check_conda() {
    if command -v conda &> /dev/null; then
        CONDA_VERSION=$(conda --version)
        print_status "Conda found: $CONDA_VERSION"
        return 0
    else
        print_error "Conda not found. Please ensure Anaconda/Miniconda is installed and in PATH."
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
        print_warning "Node.js not found. Will install via conda."
        return 1
    fi
}

# Create or activate conda environment
setup_conda_env() {
    print_info "Setting up conda environment..."
    
    ENV_NAME="langgraph-devops"
    
    # Check if environment exists
    if conda env list | grep -q "^${ENV_NAME} "; then
        print_warning "Environment ${ENV_NAME} already exists. Activating..."
        conda activate ${ENV_NAME}
    else
        print_info "Creating new conda environment: ${ENV_NAME}"
        conda create -n ${ENV_NAME} python=3.11 -y
        conda activate ${ENV_NAME}
        print_status "Created and activated conda environment: ${ENV_NAME}"
    fi
    
    # Verify Python
    PYTHON_VERSION=$(python --version)
    print_status "Using Python: $PYTHON_VERSION"
}

# Install Node.js via conda if not available
install_nodejs() {
    if ! command -v node &> /dev/null; then
        print_info "Installing Node.js via conda..."
        conda install -c conda-forge nodejs npm -y
        print_status "Node.js installed via conda"
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
    
    # Create environment.yml for conda
    cat > environment.yml << 'EOF'
name: langgraph-devops
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - pip
  - nodejs
  - npm
  - pip:
    - fastapi>=0.104.0
    - uvicorn>=0.24.0
    - python-dotenv>=1.0.0
    - requests>=2.31.0
    - aiofiles>=23.2.0
    - GitPython>=3.1.40
    - jira>=3.5.0
    - pydantic>=2.4.0
    - httpx>=0.25.0
    - pytest>=7.4.0
    - pytest-asyncio>=0.21.0
    - structlog>=23.1.0
EOF

    # Create requirements.txt as backup
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

# Install Python dependencies via conda/pip
install_python_deps() {
    print_info "Installing Python dependencies..."
    
    # Try to install from environment.yml first
    if [ -f "environment.yml" ]; then
        print_info "Installing from environment.yml..."
        conda env update -f environment.yml --prune
    else
        print_info "Installing from requirements.txt..."
        pip install -r requirements.txt
    fi
    
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
    ["Test the automation", "Try the LangGraph automation features", "medium"]);
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
  console.log(`🔗 Health check: http://localhost:${PORT}/health`);
  console.log(`📡 API endpoint: http://localhost:${PORT}/api/todos`);
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

    # Create minimal App component (will be enhanced by automation)
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
        <div className="automation-status">
          <span className="ready-badge">🤖 Ready for Automation</span>
        </div>
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
          <p>📊 Total todos: {todos.length} | ⏳ Ready for automation features!</p>
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
            <p>🎯 No todos yet. Add one above and watch the automation magic!</p>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
EOF

    # Create enhanced CSS with automation-ready styling
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
  margin-bottom: 15px;
}

.automation-status {
  display: inline-block;
}

.ready-badge {
  background: rgba(40, 167, 69, 0.9);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
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
  transition: border-color 0.2s;
}

.add-todo input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
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
  transition: all 0.2s;
}

.add-todo button:hover {
  background: #5a67d8;
  transform: translateY(-1px);
}

.filter-info {
  text-align: center;
  margin-bottom: 20px;
  color: #666;
  font-size: 14px;
  font-weight: 500;
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
  transform: translateY(-1px);
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
  font-weight: 500;
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
  padding: 8px;
  border-radius: 4px;
  transition: all 0.2s;
  font-size: 16px;
}

.delete-btn:hover {
  background: #fed7d7;
  transform: scale(1.1);
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #718096;
  font-size: 16px;
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  font-size: 18px;
  color: white;
}

/* Responsive Design */
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

/* Animation for new features that will be added */
.feature-highlight {
  animation: highlight 3s ease-in-out;
}

@keyframes highlight {
  0% { background-color: rgba(255, 235, 59, 0.3); }
  50% { background-color: rgba(255, 235, 59, 0.6); }
  100% { background-color: transparent; }
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
            print_warning "npm not found, attempting to install via conda..."
            conda install -c conda-forge nodejs npm -y
            npm install
            print_status "Backend dependencies installed (via conda npm)"
        fi
        cd ../..
    fi
    
    # Install frontend dependencies
    if [ -d "todo-app/frontend" ]; then
        cd todo-app/frontend
        npm install
        print_status "Frontend dependencies installed"
        cd ../..
    fi
}

# Create conda-specific startup scripts
create_conda_scripts() {
    print_info "Creating conda-specific startup scripts..."
    
    # Create conda-aware start-all script
    cat > start-all-conda.sh << 'EOF'
#!/bin/bash

# Start all services for LangGraph DevOps Autocoder (Conda Version)

echo "🚀 Starting LangGraph DevOps Autocoder System (Conda)"
echo "=================================================="

# Function to check if port is in use
check_port() {
    if netstat -an 2>/dev/null | grep ":$1 " | grep -q LISTEN; then
        echo "⚠️ Port $1 is already in use"
        return 1
    else
        return 0
    fi
}

# Activate conda environment
if conda env list | grep -q "langgraph-devops"; then
    echo "🐍 Activating conda environment: langgraph-devops"
    conda activate langgraph-devops
    echo "✅ Conda environment activated"
else
    echo "❌ Conda environment 'langgraph-devops' not found. Run setup-conda.sh first."
    exit 1
fi

# Verify Python and Node
echo "🔍 Verifying environment..."
python --version
node --version
npm --version

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
echo "🎉 All services started successfully!"
echo "======================================="
echo "🐍 Conda Environment: langgraph-devops"
echo "📱 Frontend:          http://localhost:3000"
echo "🔧 Backend API:       http://localhost:3001"
echo "🤖 LangGraph Server:  http://localhost:8000"
echo "📊 Health Check:      http://localhost:8000/health"
echo ""
echo "💡 Quick Tests:"
echo "curl -X POST http://localhost:8000/test/export"
echo "curl -X POST http://localhost:8000/test/search"
echo ""
echo "🔧 System Commands:"
echo "curl http://localhost:8000/health    # Check system health"
echo "curl http://localhost:8000/logs      # View recent logs"
echo "curl http://localhost:8000/files     # List generated files"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait and handle shutdown
trap 'echo ""; echo "🛑 Shutting down services..."; kill $BACKEND_PID $FRONTEND_PID $LANGGRAPH_PID 2>/dev/null; echo "✅ All services stopped"; exit' INT

# Keep script running
wait
EOF

    # Create conda-aware stop script
    cat > stop-all-conda.sh << 'EOF'
#!/bin/bash

echo "🛑 Stopping all LangGraph DevOps services (Conda)..."

# Kill processes on specific ports
for port in 3000 3001 8000; do
    # Try different methods to find and kill processes
    if command -v lsof &> /dev/null; then
        PID=$(lsof -ti:$port 2>/dev/null)
    elif command -v netstat &> /dev/null; then
        PID=$(netstat -tulpn 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1)
    fi
    
    if [ ! -z "$PID" ]; then
        kill $PID 2>/dev/null
        echo "✅ Stopped service on port $port (PID: $PID)"
    else
        echo "ℹ️ No service running on port $port"
    fi
done

echo "✅ All services stopped"
echo "🐍 Conda environment 'langgraph-devops' is still active"
echo "💡 Deactivate with: conda deactivate"
EOF

    # Create conda test script
    cat > test-system-conda.sh << 'EOF'
#!/bin/bash

echo "🧪 Testing LangGraph DevOps Autocoder System (Conda)"
echo "=================================================="

# Activate conda environment if not already active
if [ "$CONDA_DEFAULT_ENV" != "langgraph-devops" ]; then
    echo "🐍 Activating conda environment..."
    conda activate langgraph-devops
fi

echo "🔍 Environment Check:"
echo "Python: $(python --version)"
echo "Node:   $(node --version)"
echo "Conda:  $CONDA_DEFAULT_ENV"
echo ""

# Test health endpoint
echo "1. 🏥 Testing health endpoint..."
if curl -s http://localhost:8000/health | python -m json.tool 2>/dev/null; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed - make sure services are running"
    echo "💡 Run: ./start-all-conda.sh"
    exit 1
fi

echo ""
echo "2. 📤 Testing export functionality automation..."
EXPORT_RESULT=$(curl -s -X POST http://localhost:8000/test/export)
if echo "$EXPORT_RESULT" | python -m json.tool > /dev/null 2>&1; then
    echo "$EXPORT_RESULT" | python -m json.tool
    echo "✅ Export automation test completed"
else
    echo "❌ Export test failed"
fi

echo ""
echo "3. 🔍 Testing search functionality automation..."
SEARCH_RESULT=$(curl -s -X POST http://localhost:8000/test/search)
if echo "$SEARCH_RESULT" | python -m json.tool > /dev/null 2>&1; then
    echo "$SEARCH_RESULT" | python -m json.tool
    echo "✅ Search automation test completed"
else
    echo "❌ Search test failed"
fi

echo ""
echo "4. 📁 Checking generated files..."
FILES_RESULT=$(curl -s http://localhost:8000/files)
if echo "$FILES_RESULT" | python -m json.tool > /dev/null 2>&1; then
    echo "$FILES_RESULT" | python -c "
import json, sys
data = json.load(sys.stdin)
print(f'📊 Total files: {data[\"total\"]}')
for file in data['files'][:5]:
    print(f'  📄 {file[\"path\"]} ({file[\"type\"]}) - {file[\"size\"]} bytes')
if data['total'] > 5:
    print(f'  ... and {data[\"total\"] - 5} more files')
"
    echo "✅ File system check completed"
else
    echo "❌ File check failed"
fi

echo ""
echo "5. 📊 System Status Summary..."
curl -s http://localhost:8000/health | python -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'🤖 LangGraph Available: {data.get(\"langgraph_available\", \"Unknown\")}')
    print(f'📦 Active Processes: {data.get(\"active_processes\", 0)}')
    print(f'🎨 Todo Frontend: {\"✅\" if data.get(\"todo_app\", {}).get(\"frontend\") else \"❌\"}')
    print(f'🔧 Todo Backend: {\"✅\" if data.get(\"todo_app\", {}).get(\"backend\") else \"❌\"}')
except:
    print('❌ Unable to parse health status')
"

echo ""
echo "✅ System tests completed!"
echo ""
echo "🎯 Manual Verification Steps:"
echo "1. Open http://localhost:3000 to see the Todo app"
echo "2. Open http://localhost:8000 to see the LangGraph API"
echo "3. Try adding a todo and see if export/search features were added"
echo ""
echo "🚀 Custom webhook test:"
echo 'curl -X POST http://localhost:8000/webhook/jira -H "Content-Type: application/json" -d '"'"'{"issue": {"key": "CUSTOM-001", "fields": {"summary": "Add notifications", "issuetype": {"name": "Story"}, "description": "Add notification system with due date alerts"}}}'"'"''
EOF

    # Create conda environment management script
    cat > manage-conda-env.sh << 'EOF'
#!/bin/bash

case "$1" in
    "create")
        echo "🐍 Creating conda environment..."
        conda env create -f environment.yml
        echo "✅ Environment created. Activate with: conda activate langgraph-devops"
        ;;
    "update")
        echo "🔄 Updating conda environment..."
        conda env update -f environment.yml --prune
        echo "✅ Environment updated"
        ;;
    "activate")
        echo "🐍 To activate the environment, run:"
        echo "conda activate langgraph-devops"
        ;;
    "deactivate")
        echo "🚪 To deactivate the environment, run:"
        echo "conda deactivate"
        ;;
    "remove")
        echo "🗑️ Removing conda environment..."
        conda env remove -n langgraph-devops
        echo "✅ Environment removed"
        ;;
    "info")
        echo "📊 Conda Environment Information:"
        conda env list | grep langgraph-devops || echo "Environment not found"
        if [ "$CONDA_DEFAULT_ENV" = "langgraph-devops" ]; then
            echo "✅ Currently active"
            conda list | head -20
        else
            echo "❌ Not currently active"
        fi
        ;;
    *)
        echo "🐍 Conda Environment Manager for LangGraph DevOps"
        echo "Usage: $0 {create|update|activate|deactivate|remove|info}"
        echo ""
        echo "Commands:"
        echo "  create     - Create new environment from environment.yml"
        echo "  update     - Update existing environment"
        echo "  activate   - Show activation command"
        echo "  deactivate - Show deactivation command"  
        echo "  remove     - Remove the environment"
        echo "  info       - Show environment information"
        ;;
esac
EOF

    # Make all scripts executable
    chmod +x start-all-conda.sh stop-all-conda.sh test-system-conda.sh manage-conda-env.sh
    
    print_status "Conda-specific scripts created"
}

# Main installation function
main() {
    print_info "Starting Anaconda-based setup process..."
    
    # Check prerequisites
    if ! check_conda; then
        print_error "Conda is required but not found. Please ensure Anaconda/Miniconda is installed."
        exit 1
    fi
    
    # Setup conda environment
    setup_conda_env
    
    # Install Node.js if needed
    install_nodejs
    
    # Check Node.js again
    if ! check_node; then
        print_warning "Node.js still not available after conda installation"
    fi
    
    # Create directory structure
    create_directories
    
    # Create Python files
    create_python_files
    
    # Install Python dependencies
    install_python_deps
    
    # Create Todo app
    create_todo_app
    
    # Install Node dependencies
    if command -v npm &> /dev/null; then
        install_node_deps
    else
        print_warning "npm not available, skipping Node.js dependencies"
    fi
    
    # Create conda-specific scripts
    create_conda_scripts
    
    # Final instructions
    echo ""
    print_status "🎉 Anaconda setup completed successfully!"
    echo ""
    print_info "🐍 Conda Environment: langgraph-devops"
    print_info "📦 Environment file: environment.yml created"
    echo ""
    print_info "Next steps:"
    echo "1. Copy the enhanced LangGraph system code to src/main.py"
    echo "2. Copy the enhanced server code to enhanced_server.py"
    echo "3. Ensure conda environment is active: conda activate langgraph-devops"
    echo "4. Run: ./start-all-conda.sh"
    echo "5. Test: ./test-system-conda.sh"
    echo ""
    print_info "🚀 Conda-specific commands:"
    echo "• Start all:     ./start-all-conda.sh"
    echo "• Stop all:      ./stop-all-conda.sh"
    echo "• Test system:   ./test-system-conda.sh"
    echo "• Manage env:    ./manage-conda-env.sh info"
    echo ""
    print_info "🌐 URLs after startup:"
    echo "• Todo App:      http://localhost:3000"
    echo "• Backend API:   http://localhost:3001"
    echo "• LangGraph:     http://localhost:8000"
    echo ""
    print_info "⚡ Quick automation tests:"
    echo "• Export test:   curl -X POST http://localhost:8000/test/export"
    echo "• Search test:   curl -X POST http://localhost:8000/test/search"
    echo ""
    print_status "🎯 Ready for LangGraph DevOps automation with Anaconda! 🐍🚀"
}

# Run main function
main "$@"