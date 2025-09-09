import React, { useState } from 'react';

const AdvancedSearch = () => {
    const [searchTerm, setSearchTerm] = useState('');
    const [category, setCategory] = useState('');
    const [priority, setPriority] = useState('');
    const [dateRange, setDateRange] = useState({ start: '', end: '' });

    const handleSearchChange = (event) => {
        setSearchTerm(event.target.value);
    };

    const handleCategoryChange = (event) => {
        setCategory(event.target.value);
    };

    const handlePriorityChange = (event) => {
        setPriority(event.target.value);
    };

    const handleDateChange = (event) => {
        setDateRange({ ...dateRange, [event.target.name]: event.target.value });
    };

    const handleSubmit = (event) => {
        event.preventDefault();
        // Implement search functionality here
    };

    return (
        <form onSubmit={handleSubmit}>
            <input type="text" value={searchTerm} onChange={handleSearchChange} placeholder="Search..." />
            <select value={category} onChange={handleCategoryChange}>
                <option value="">All Categories</option>
                {/* Add category options here */}
            </select>
            <select value={priority} onChange={handlePriorityChange}>
                <option value="">All Priorities</option>
                {/* Add priority options here */}
            </select>
            <input type="date" name="start" value={dateRange.start} onChange={handleDateChange} />
            <input type="date" name="end" value={dateRange.end} onChange={handleDateChange} />
            <button type="submit">Search</button>
        </form>
    );
};

export default AdvancedSearch;