import { useState, useEffect } from 'react';
import ConfirmationDialog from './components/ConfirmationDialog';

function App() {
  const [todos, setTodos] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedTodo, setSelectedTodo] = useState(null);

  const deleteTodo = (todo) => {
    setSelectedTodo(todo);
    setDialogOpen(true);
  };

  const confirmDelete = () => {
    setTodos(todos.filter(t => t !== selectedTodo));
    setDialogOpen(false);
  };

  return (
    <div className='App'>
      {todos.map(todo => (
        <div key={todo.id}>
          <p>{todo.title}</p>
          <button onClick={() => deleteTodo(todo)}>Delete</button>
        </div>
      ))}
      <ConfirmationDialog
        isOpen={dialogOpen}
        message='Are you sure you want to delete this todo?'
        onConfirm={confirmDelete}
        onCancel={() => setDialogOpen(false)}
      />
    </div>
  );
}

export default App;