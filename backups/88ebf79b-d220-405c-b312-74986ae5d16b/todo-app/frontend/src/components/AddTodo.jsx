import React, { useState } from 'react';

const AddTodo = ({ addTodo }) => {
  const [value, setValue] = useState('');

  const handleSubmit = e => {
    e.preventDefault();
    if (!value) return;
    addTodo(value);
    setValue('');
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        className="input"
        value={value}
        onChange={e => setValue(e.target.value)}
        placeholder="Add new todo"
        aria-label="Add new todo"
      />
      <button type="submit">Add</button>
    </form>
  );
};

export default AddTodo;