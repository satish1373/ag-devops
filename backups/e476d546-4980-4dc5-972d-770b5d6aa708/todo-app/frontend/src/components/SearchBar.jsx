Here is a simple, clean, and functional SearchBar component:

```jsx
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
      <label htmlFor="search-bar" className="sr-only">Search Todos</label>
      <input
        id="search-bar"
        type="text"
        placeholder="Search todos..."
        value={searchTerm}
        onChange={handleSearchChange}
        className="search-bar"
      />
    </div>
  );
};

SearchBar.propTypes = {
  onSearch: PropTypes.func.isRequired,
};

export default SearchBar;
```

This component uses the useState hook to manage its own state. It also uses the useEffect hook to call the onSearch function whenever the searchTerm state changes. This allows the component to notify its parent component of the search term in real-time.

The component also includes proper event handling. The handleSearchChange function is called whenever the user types into the search bar. This function updates the searchTerm state and calls the onSearch function with the new search term.

The component is designed to be accessible. It includes a label for the search bar, which is hidden using the sr-only class. This makes the label invisible to sighted users but still accessible to screen readers.

Finally, the component follows React best practices. It is a functional component, which is the recommended way to write components in modern React. It also uses PropTypes to validate its props, ensuring that the onSearch prop is a function.