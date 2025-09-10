import React from 'react';

const SearchBar = ({ searchTerm, onSearchChange }) => {
  return (
    <div className="search-bar">
      <input
        type="text"
        placeholder="Search todos..."
        value={searchTerm}
        onChange={(e) => onSearchChange(e.target.value)}
        className="search-input"
      />
      {searchTerm && (
        <button onClick={() => onSearchChange('')} className="clear-btn">
          Clear
        </button>
      )}
    </div>
  );
};

export default SearchBar;