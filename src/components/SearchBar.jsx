import React from 'react';

const SearchBar = ({ searchTerm, setSearchTerm, clearSearch }) => {
  return (
    <div>
      <input type='text' value={searchTerm} onChange={e => setSearchTerm(e.target.value)} placeholder='Search todos...'/>
      <button onClick={clearSearch}>Clear</button>
    </div>
  );
};

export default SearchBar;