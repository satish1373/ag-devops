import React, { useState } from 'react';
import PropTypes from 'prop-types';

const SearchBar = ({ onSearch }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value);
    onSearch(event.target.value);
  };

  return (
    <div>
      <label htmlFor="search-bar" className="visually-hidden">
        Search Todos
      </label>
      <input
        type="text"
        id="search-bar"
        placeholder="Search todos..."
        value={searchTerm}
        onChange={handleSearchChange}
      />
    </div>
  );
};

SearchBar.propTypes = {
  onSearch: PropTypes.func.isRequired,
};

export default SearchBar;