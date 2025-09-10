import { useState, useEffect } from 'react';
import SearchBar from './components/SearchBar';

function App() {
  const [todos, setTodos] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    // Fetch todos here
  }, []);

  const clearSearch = () => setSearchTerm('');

  const filteredTodos = todos.filter(todo => todo.title.includes(searchTerm) || todo.description.includes(searchTerm));

  return (
    <div>
      <SearchBar searchTerm={searchTerm} setSearchTerm={setSearchTerm} clearSearch={clearSearch} />
      <p>{filteredTodos.length} / {todos.length}</p>
      {filteredTodos.map(todo => <p key={todo.id}>{todo.title}</p>)}
    </div>
  );
}

export default App;