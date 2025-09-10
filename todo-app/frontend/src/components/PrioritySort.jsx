import React, { useState, useEffect } from 'react';

const PrioritySort = ({ onSortChange }) => {
    const [sort, setSort] = useState('low');

    const handleSortChange = (event) => {
        setSort(event.target.value);
    };

    useEffect(() => {
        onSortChange(sort);
    }, [sort, onSortChange]);

    return (
        <div>
            <label htmlFor="priority-sort">Sort by priority: </label>
            <select id="priority-sort" value={sort} onChange={handleSortChange}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
            </select>
        </div>
    );
};

export default PrioritySort;