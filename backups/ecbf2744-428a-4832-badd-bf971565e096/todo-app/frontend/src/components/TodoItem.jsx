import React from 'react';
import PropTypes from 'prop-types';

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

TodoItem.propTypes = {
    todo: PropTypes.shape({
        id: PropTypes.number.isRequired,
        title: PropTypes.string.isRequired,
        completed: PropTypes.bool.isRequired,
    }).isRequired,
    onToggle: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
};

export default TodoItem;