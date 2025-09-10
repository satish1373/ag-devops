```jsx
// ExportButton.js
import React from 'react';
import PropTypes from 'prop-types';
import { saveAs } from 'file-saver';
import { CSVLink } from "react-csv";

const ExportButton = ({ data }) => {
  // Error handling for empty or invalid data
  if (!data || !Array.isArray(data) || !data.length) {
    return <p>No data to export</p>;
  }

  const headers = Object.keys(data[0]);

  return (
    <CSVLink
      data={data}
      headers={headers}
      filename={"todo-list.csv"}
      className="btn btn-primary"
      target="_blank"
    >
      Export
    </CSVLink>
  );
};

ExportButton.propTypes = {
  data: PropTypes.array.isRequired,
};

export default ExportButton;

// SearchBar.js
import React, { useState } from 'react';
import PropTypes from 'prop-types';

const SearchBar = ({ onSearch }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const handleSearch = (event) => {
    setSearchTerm(event.target.value);
    onSearch(event.target.value);
  };

  const handleClear = () => {
    setSearchTerm('');
    onSearch('');
  };

  return (
    <div>
      <input
        type="text"
        value={searchTerm}
        onChange={handleSearch}
        placeholder="Search..."
      />
      <button onClick={handleClear}>Clear</button>
    </div>
  );
};

SearchBar.propTypes = {
  onSearch: PropTypes.func.isRequired,
};

export default SearchBar;

// Modal.js
import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';

const Modal = ({ isOpen, onClose, children }) => {
  const modalRef = useRef();

  useEffect(() => {
    function handleOutsideClick(event) {
      if (!modalRef.current.contains(event.target)) {
        if (isOpen) onClose();
      }
    }

    window.addEventListener('click', handleOutsideClick);
    return () => window.removeEventListener('click', handleOutsideClick);
  }, [isOpen, onClose]);

  return (
    <div ref={modalRef}>
      {isOpen ? (
        <div>
          <button onClick={onClose}>Close</button>
          {children}
        </div>
      ) : null}
    </div>
  );
};

Modal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  children: PropTypes.node,
};

export default Modal;
```