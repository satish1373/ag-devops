import React, { useState } from 'react';

const TodoList = () => {
    const [todos, setTodos] = useState([]);
    const [input, setInput] = useState('');

    const handleInputChange = (event) => {
        setInput(event.target.value);
    };

    const handleAddTodo = () => {
        setTodos([...todos, input]);
        setInput('');
    };

    const handleDeleteTodo = (index) => {
        const newTodos = [...todos];
        newTodos.splice(index, 1);
        setTodos(newTodos);
    };

    return (
        <div>
            <input 
                type="text" 
                value={input} 
                onChange={handleInputChange} 
                placeholder="Add a todo" 
                aria-label="Add a todo"
            />
            <button onClick={handleAddTodo}>Add</button>
            <ul>
                {todos.map((todo, index) => (
                    <li key={index}>
                        {todo}
                        <button onClick={() => handleDeleteTodo(index)}>Delete</button>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default TodoList;