import React from 'react';

const CategoryFilter = ({ categories, onCategoryChange }) => {
  return (
    <div>
      <label htmlFor="category">Category:</label>
      <select id="category" onChange={onCategoryChange}>
        <option value="">All</option>
        {categories.map((category, index) => (
          <option key={index} value={category}>
            {category}
          </option>
        ))}
      </select>
    </div>
  );
};

export default CategoryFilter;