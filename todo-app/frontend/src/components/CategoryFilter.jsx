import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

const CategoryFilter = ({ categories, onFilterChange }) => {
  const [selectedCategory, setSelectedCategory] = useState('');

  useEffect(() => {
    onFilterChange(selectedCategory);
  }, [selectedCategory, onFilterChange]);

  const handleCategoryChange = (event) => {
    setSelectedCategory(event.target.value);
  };

  return (
    <div>
      <label htmlFor="category-filter">Filter by category:</label>
      <select id="category-filter" value={selectedCategory} onChange={handleCategoryChange}>
        <option value="">All</option>
        {categories.map((category) => (
          <option key={category} value={category}>
            {category}
          </option>
        ))}
      </select>
    </div>
  );
};

CategoryFilter.propTypes = {
  categories: PropTypes.arrayOf(PropTypes.string).isRequired,
  onFilterChange: PropTypes.func.isRequired,
};

export default CategoryFilter;