import { useState, useEffect } from 'react'
import DatePicker from 'react-datepicker'
import 'react-datepicker/dist/react-datepicker.css'
import './App.css'

function App() {
  const [todos, setTodos] = useState([])
  const [loading, setLoading] = useState(true)
  const [newTodo, setNewTodo] = useState('')
  const [dueDate, setDueDate] = useState(new Date())
  const [searchTerm, setSearchTerm] = useState('')

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
        body: JSON.stringify({ title: newTodo, dueDate, priority: 'medium' }),
      })
      
      if (response.ok) {
        const todo = await response.json()
        setTodos([todo, ...todos])
        setNewTodo('')
        setDueDate(new Date())
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

  const filteredTodos = todos.filter(todo => 
    todo.title.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) {
    return <div className="loading">Loading todos...</div>
  }

  return (
    <div className="app">
      <header className="header">
        <h1>Todo List</h1>
        <input 
          type="text" 
          placeholder="Search todos" 
          value={searchTerm} 
          onChange={e => setSearchTerm(e.target.value)} 
        />
        <input 
          type="text" 
          placeholder="New todo" 
          value={newTodo} 
          onChange={e => setNewTodo(e.target.value)} 
        />
        <DatePicker selected={dueDate} onChange={date => setDueDate(date)} />
        <button onClick={addTodo}>Add todo</button>
      </header>
      <main>
        {filteredTodos.map(todo => (
          <div key={todo.id} className={`todo ${todo.dueDate < new Date() ? 'overdue' : ''}`}>
            <input 
              type="checkbox" 
              checked={todo.completed} 
              onChange={() => toggleTodo(todo.id, !todo.completed)} 
            />
            <span>{todo.title}</span>
            <span>{new Date(todo.dueDate).toLocaleDateString()}</span>
          </div>
        ))}
      </main>
    </div>
  )
}

export default App