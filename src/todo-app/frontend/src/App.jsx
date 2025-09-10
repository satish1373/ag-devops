import React, { useState } from 'react';
import AdvancedSearch from './AdvancedSearch';

const App = () => {
  const [todos, setTodos] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [error, setError] = useState(null);

  const handleSearch = async (filters) => {
    try {
      const results = await AdvancedSearch.search(todos, filters);
      setSearchResults(results);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div>
      <AdvancedSearch onSearch={handleSearch} />
      {error && <div>Error: {error}</div>}
      <ul>
        {searchResults.map((todo, index) => (
          <li key={index}>{todo}</li>
        ))}
      </ul>
    </div>
  );
};

export default App;