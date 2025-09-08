import React from 'react';

const SearchBar = ({ searchTerm, onSearchChange, placeholder = "🔍 Search todos..." }) => {
  return (
    <div className="search-bar">
      <input
        type="text"
        placeholder={placeholder}
        value={searchTerm}
        onChange={(e) => onSearchChange(e.target.value)}
        className="search-input"
      />
      {searchTerm && (
        <button 
          onClick={() => onSearchChange('')}
          className="search-clear"
          title="Clear search"
        >
          ✕
        </button>
      )}
    </div>
  );
};

export default SearchBar;