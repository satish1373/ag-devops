import { useState, useEffect } from 'react'
import SearchBar from './components/SearchBar'
import './App.css'

function App() {
  const [todos, setTodos] = useState([])
  const [loading, setLoading] = useState(true)
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
  const handleSearchChange = (term) => setSearchTerm(term)

  if (loading) return <div>Loading...</div>

  return (
    <div className="app">
      <h1>Todo App</h1>
        <SearchBar searchTerm={searchTerm} onSearchChange={handleSearchChange} />

      <div className="todos">
        {todos.map(todo => (
          <div key={todo.id} className="todo-item">
            <span>{todo.title}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App