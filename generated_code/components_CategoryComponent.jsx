Sure, here is a simple example of a functional component in React that meets your requirements:

```jsx
import React, { useState } from 'react';
import PropTypes from 'prop-types';

const CategoryComponent = ({ categories, onCategoryChange }) => {
  const [selectedCategory, setSelectedCategory] = useState('');

  const handleCategoryChange = (event) => {
    setSelectedCategory(event.target.value);
    onCategoryChange(event.target.value);
  };

  if (!categories || categories.length === 0) {
    return <p>No categories available</p>;
  }

  return (
    <div>
      <label htmlFor="category-select">Choose a category:</label>
      <select
        id="category-select"
        value={selectedCategory}
        onChange={handleCategoryChange}
      >
        {categories.map((category) => (
          <option key={category} value={category}>
            {category}
          </option>
        ))}
      </select>
    </div>
  );
};

CategoryComponent.propTypes = {
  categories: PropTypes.arrayOf(PropTypes.string).isRequired,
  onCategoryChange: PropTypes.func.isRequired,
};

export default CategoryComponent;
```

This component receives a list of categories and a callback function to handle category changes as props. It uses the useState hook to manage its own state, and it includes basic error handling by checking if the categories prop is valid. It also includes accessibility features by using a label with a htmlFor attribute that matches the select element's id.