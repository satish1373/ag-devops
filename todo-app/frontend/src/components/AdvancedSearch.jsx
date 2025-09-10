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

  const handleDateRangeChange = (event) => {
    setDateRange({
      ...dateRange,
      [event.target.name]: event.target.value,
    });
  };

  return (
    <div>
      <input
        type="text"
        placeholder="Search..."
        value={searchTerm}
        onChange={handleSearchChange}
        aria-label="Search"
      />
      <select value={category} onChange={handleCategoryChange} aria-label="Category">
        <option value="">All Categories</option>
        {/* Add more options as needed */}
      </select>
      <select value={priority} onChange={handlePriorityChange} aria-label="Priority">
        <option value="">All Priorities</option>
        {/* Add more options as needed */}
      </select>
      <input
        type="date"
        name="start"
        value={dateRange.start}
        onChange={handleDateRangeChange}
        aria-label="Start Date"
      />
      <input
        type="date"
        name="end"
        value={dateRange.end}
        onChange={handleDateRangeChange}
        aria-label="End Date"
      />
    </div>
  );
};

export default AdvancedSearch;