import React from 'react';

const TodoItem = ({ todo, onToggle, onDelete }) => {
  const handleToggle = () => {
    onToggle(todo.id);
  };

  const handleDelete = () => {
    onDelete(todo.id);
  };

  return (
    <div>
      <input 
        type="checkbox" 
        checked={todo.completed} 
        onChange={handleToggle} 
        aria-label={`Mark todo ${todo.id} as completed`}
      />
      <label>{todo.title}</label>
      <button onClick={handleDelete} aria-label={`Delete todo ${todo.id}`}>
        Delete
      </button>
    </div>
  );
};

export default TodoItem;