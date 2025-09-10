#!/bin/bash

# Complete Todo App Setup Script
echo "🚀 Setting up complete Todo App with CRUD functionality..."

# Navigate to your project directory
cd /d/Projects/real_usecases/Draft/langgraph-devops-autocoder

# Create backend if it doesn't exist
mkdir -p todo-app/backend
cd todo-app/backend

# Initialize package.json
cat > package.json << 'EOF'
{
  "name": "todo-backend",
  "version": "1.0.0",
  "description": "Todo App Backend API",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "sqlite3": "^5.1.6",
    "uuid": "^9.0.0"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  }
}
EOF

# Create backend server
cat > server.js << 'EOF'
const express = require('express');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();
const { v4: uuidv4 } = require('uuid');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Database setup
const dbPath = path.join(__dirname, 'todos.db');
const db = new sqlite3.Database(dbPath);

// Create todos table
db.serialize(() => {
  db.run(`
    CREATE TABLE IF NOT EXISTS todos (
      id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      description TEXT,
      completed BOOLEAN DEFAULT 0,
      priority TEXT DEFAULT 'medium',
      category TEXT DEFAULT 'general',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Insert sample data
  db.run(`
    INSERT OR IGNORE INTO todos (id, title, description, completed, priority) 
    VALUES 
    ('1', 'Welcome to Todo App', 'This is your first todo item', 0, 'high'),
    ('2', 'Try adding a new todo', 'Click the + button to add a todo', 0, 'medium'),
    ('3', 'Mark todos as complete', 'Click the checkbox to complete tasks', 1, 'low')
  `);
});

// Routes
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Get all todos
app.get('/api/todos', (req, res) => {
  db.all('SELECT * FROM todos ORDER BY created_at DESC', (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(rows);
  });
});

// Get single todo
app.get('/api/todos/:id', (req, res) => {
  const { id } = req.params;
  db.get('SELECT * FROM todos WHERE id = ?', [id], (err, row) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    if (!row) {
      return res.status(404).json({ error: 'Todo not found' });
    }
    res.json(row);
  });
});

// Create new todo
app.post('/api/todos', (req, res) => {
  const { title, description, priority = 'medium', category = 'general' } = req.body;
  
  if (!title) {
    return res.status(400).json({ error: 'Title is required' });
  }

  const id = uuidv4();
  const now = new Date().toISOString();

  db.run(
    `INSERT INTO todos (id, title, description, priority, category, created_at, updated_at) 
     VALUES (?, ?, ?, ?, ?, ?, ?)`,
    [id, title, description, priority, category, now, now],
    function(err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      
      db.get('SELECT * FROM todos WHERE id = ?', [id], (err, row) => {
        if (err) {
          return res.status(500).json({ error: err.message });
        }
        res.status(201).json(row);
      });
    }
  );
});

// Update todo
app.put('/api/todos/:id', (req, res) => {
  const { id } = req.params;
  const { title, description, completed, priority, category } = req.body;
  const now = new Date().toISOString();

  db.run(
    `UPDATE todos 
     SET title = COALESCE(?, title),
         description = COALESCE(?, description),
         completed = COALESCE(?, completed),
         priority = COALESCE(?, priority),
         category = COALESCE(?, category),
         updated_at = ?
     WHERE id = ?`,
    [title, description, completed, priority, category, now, id],
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

// Delete todo
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
  console.log(`Server running on port ${PORT}`);
});

module.exports = app;
EOF

# Install backend dependencies
npm install

# Create frontend directory
cd ../
mkdir -p frontend/src/components
cd frontend

# Create package.json for frontend
cat > package.json << 'EOF'
{
  "name": "todo-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "react-csv": "^2.2.2"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
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

# Create public/index.html
mkdir -p public
cat > public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Todo App</title>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
EOF

# Create complete React App
cat > src/App.jsx << 'EOF'
import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [todos, setTodos] = useState([])
  const [loading, setLoading] = useState(true)
  const [newTodo, setNewTodo] = useState('')
  const [newDescription, setNewDescription] = useState('')
  const [newPriority, setNewPriority] = useState('medium')
  const [filter, setFilter] = useState('all')

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

  const addTodo = async (e) => {
    e.preventDefault()
    if (!newTodo.trim()) return

    try {
      const response = await fetch('http://localhost:3001/api/todos', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: newTodo,
          description: newDescription,
          priority: newPriority
        }),
      })

      if (response.ok) {
        const todo = await response.json()
        setTodos([todo, ...todos])
        setNewTodo('')
        setNewDescription('')
        setNewPriority('medium')
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
        body: JSON.stringify({ completed: !completed }),
      })

      if (response.ok) {
        const updatedTodo = await response.json()
        setTodos(todos.map(todo => 
          todo.id === id ? updatedTodo : todo
        ))
      }
    } catch (error) {
      console.error('Failed to toggle todo:', error)
    }
  }

  const deleteTodo = async (id) => {
    if (!window.confirm('Are you sure you want to delete this todo?')) return

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

  const filteredTodos = todos.filter(todo => {
    if (filter === 'active') return !todo.completed
    if (filter === 'completed') return todo.completed
    return true
  })

  if (loading) {
    return <div className="loading">Loading todos...</div>
  }

  return (
    <div className="app">
      <header className="header">
        <h1>🚀 Todo App</h1>
        <p>Stay organized and productive</p>
      </header>

      <main className="main-content">
        <form onSubmit={addTodo} className="add-todo">
          <div className="form-row">
            <input
              type="text"
              value={newTodo}
              onChange={(e) => setNewTodo(e.target.value)}
              placeholder="What needs to be done?"
              className="todo-input"
            />
            <select 
              value={newPriority} 
              onChange={(e) => setNewPriority(e.target.value)}
              className="priority-select"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
            <button type="submit" className="add-btn">Add Todo</button>
          </div>
          <input
            type="text"
            value={newDescription}
            onChange={(e) => setNewDescription(e.target.value)}
            placeholder="Add a description (optional)"
            className="description-input"
          />
        </form>

        <div className="filter-section">
          <div className="filter-buttons">
            <button 
              onClick={() => setFilter('all')}
              className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            >
              All ({todos.length})
            </button>
            <button 
              onClick={() => setFilter('active')}
              className={`filter-btn ${filter === 'active' ? 'active' : ''}`}
            >
              Active ({todos.filter(t => !t.completed).length})
            </button>
            <button 
              onClick={() => setFilter('completed')}
              className={`filter-btn ${filter === 'completed' ? 'active' : ''}`}
            >
              Completed ({todos.filter(t => t.completed).length})
            </button>
          </div>
        </div>

        <div className="todos">
          {filteredTodos.length === 0 ? (
            <div className="empty-state">
              <p>No todos yet. Add one above!</p>
            </div>
          ) : (
            filteredTodos.map(todo => (
              <div key={todo.id} className={`todo-item ${todo.completed ? 'completed' : ''} priority-${todo.priority}`}>
                <input
                  type="checkbox"
                  checked={todo.completed}
                  onChange={() => toggleTodo(todo.id, todo.completed)}
                  className="todo-checkbox"
                />
                <div className="todo-content">
                  <span className="todo-title">{todo.title}</span>
                  {todo.description && (
                    <span className="todo-description">{todo.description}</span>
                  )}
                  <div className="todo-meta">
                    <span className="priority">{todo.priority}</span>
                    <span className="date">
                      {new Date(todo.created_at).toLocaleDateString()}
                    </span>
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
            ))
          )}
        </div>
      </main>
    </div>
  )
}

export default App
EOF

# Create index.js
cat > src/index.js << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
EOF

# Create CSS
cat > src/App.css << 'EOF'
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
  margin-bottom: 30px;
}

.form-row {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.todo-input {
  flex: 1;
  padding: 12px;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  font-size: 16px;
}

.description-input {
  width: 100%;
  padding: 12px;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  font-size: 14px;
  color: #666;
}

.priority-select {
  padding: 12px;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  font-size: 16px;
  background: white;
}

.add-btn {
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

.add-btn:hover {
  background: #5a67d8;
}

.filter-section {
  margin-bottom: 20px;
}

.filter-buttons {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.filter-btn {
  padding: 8px 16px;
  border: 2px solid #e9ecef;
  border-radius: 20px;
  background: white;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.filter-btn.active,
.filter-btn:hover {
  border-color: #667eea;
  background: #667eea;
  color: white;
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

.todo-checkbox {
  width: 20px;
  height: 20px;
  margin-top: 2px;
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

.priority, .date {
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
  font-size: 16px;
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
  
  .form-row {
    flex-direction: column;
  }
  
  .filter-buttons {
    flex-wrap: wrap;
  }
}
EOF

echo ""
echo "✅ Complete Todo App setup finished!"
echo ""
echo "🚀 To start your app:"
echo "1. Start backend:  cd todo-app/backend && npm run dev"
echo "2. Start frontend: cd todo-app/frontend && npm start"
echo ""
echo "📍 Your app will be available at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:3001"
echo ""