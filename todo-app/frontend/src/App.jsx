```jsx
import React, { useState, useEffect } from 'react';
import SearchBar from './components/SearchBar';
import TodoList from './components/TodoList';
import ExportButton from './components/ExportButton';
import ExportModal from './components/ExportModal';
import './App.css';

function App() {
  const [todos, setTodos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [exportModalOpen, setExportModalOpen] = useState(false);

  useEffect(() => {
    fetchTodos();
  }, []);

  const fetchTodos = async () => {
    try {
      const response = await fetch('http://localhost:3001/api/todos');
      const data = await response.json();
      setTodos(data);
    } catch (error) {
      console.error('Failed to fetch todos:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchChange = (term) => setSearchTerm(term);

  const handleExport = () => {
    setExportModalOpen(true);
  };

  const handleExportClose = () => {
    setExportModalOpen(false);
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="app">
      <h1>Todo App</h1>
      <SearchBar searchTerm={searchTerm} onSearchChange={handleSearchChange} />
      <ExportButton onExport={handleExport} />
      <TodoList todos={todos} />
      {exportModalOpen && (
        <ExportModal todos={todos} onClose={handleExportClose} />
      )}
    </div>
  );
}

export default App;
```

In this updated code, I have imported the new components `ExportButton` and `ExportModal`. I have also added a new state variable `exportModalOpen` to manage the visibility of the `ExportModal`. The `handleExport` function is used to open the `ExportModal` when the `ExportButton` is clicked, and the `handleExportClose` function is used to close the `ExportModal`. The `ExportModal` is conditionally rendered based on the `exportModalOpen` state. The `todos` are passed to the `ExportModal` as a prop.