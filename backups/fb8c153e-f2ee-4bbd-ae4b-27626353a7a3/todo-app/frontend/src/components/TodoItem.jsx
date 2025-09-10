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
            <input type="checkbox" checked={todo.completed} onChange={handleToggle} />
            <label>{todo.title}</label>
            <button onClick={handleDelete}>Delete</button>
        </div>
    );
};

export default TodoItem;