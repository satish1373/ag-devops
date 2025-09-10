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
