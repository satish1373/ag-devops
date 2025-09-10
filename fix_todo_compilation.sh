#!/bin/bash

# Fix Todo App Compilation Errors
# Create missing components and fix file structure

echo "🔧 Fixing Todo App compilation errors..."

# Navigate to the frontend directory
cd todo-app/frontend

# Create the components directory if it doesn't exist
mkdir -p src/components

# Create the missing ExportButton component
cat > src/components/ExportButton.jsx << 'EOF'
import React from 'react';

const ExportButton = ({ todos }) => {
  const exportToCSV = () => {
    if (!todos || todos.length === 0) {
      alert('No todos to export!');
      return;
    }

    const headers = ['Title', 'Description', 'Priority', 'Category', 'Completed', 'Created Date'];
    const csvContent = [
      headers.join(','),
      ...todos.map(todo => [
        `"${(todo.title || '').replace(/"/g, '""')}"`,
        `"${(todo.description || '').replace(/"/g, '""')}"`,
        todo.priority || 'medium',
        todo.category || 'general',
        todo.completed ? 'Yes' : 'No',
        new Date(todo.created_at).toLocaleDateString()
      ].join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `todos-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    console.log(`Exported ${todos.length} todos to CSV`);
  };

  return (
    <button onClick={exportToCSV} className="export-btn" title="Export all todos to CSV file">
      📥 Export to CSV ({todos?.length || 0} todos)
    </button>
  );
};

export default ExportButton;
EOF

# Update the App.jsx to fix any import issues
cat > src/App.jsx << 'EOF'
import { useState, useEffect } from 'react'
import ExportButton from './components/ExportButton'
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
        
        <div className="export-section">
          <ExportButton todos={todos} />
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

# Update the CSS to include styles for the export button
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

/* Export functionality styles */
.export-section {
  margin-bottom: 20px;
  text-align: center;
}

.export-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 16px;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.export-btn:hover {
  background: #218838;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.export-btn:active {
  transform: translateY(0);
}

.export-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  transform: none;
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

# Create index.js if it doesn't exist
if [ ! -f src/index.js ]; then
cat > src/index.js << 'EOF'
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
fi

# Update package.json to ensure dependencies are correct
cat > package.json << 'EOF'
{
  "name": "todo-frontend",
  "version": "1.0.0",
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

echo "✅ Fixed compilation errors!"
echo ""
echo "🎯 What was fixed:"
echo "  ✓ Created missing ExportButton component"
echo "  ✓ Updated App.jsx with correct imports"
echo "  ✓ Added CSS styles for export functionality"
echo "  ✓ Ensured proper file structure"
echo ""
echo "🚀 Now run: npm start"
echo "📱 The app should compile and run at http://localhost:3000"
echo ""
echo "🎉 Features included:"
echo "  ✓ Todo creation and management"
echo "  ✓ CSV export functionality"
echo "  ✓ Priority color coding"
echo "  ✓ Responsive design"