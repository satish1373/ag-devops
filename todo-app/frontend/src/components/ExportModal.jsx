```jsx
import React, { useState } from 'react';
import PropTypes from 'prop-types';

// Import common components
import ExportButton from './ExportButton';
import SearchBar from './SearchBar';
import Modal from './Modal';

// ExportModal component
const ExportModal = ({ isOpen, onClose, onExport }) => {
  // State for the selected export format
  const [exportFormat, setExportFormat] = useState('csv');

  // Handle export format change
  const handleExportFormatChange = (event) => {
    setExportFormat(event.target.value);
  };

  // Handle export confirmation
  const handleExportConfirm = () => {
    // Call the onExport function with the selected format
    onExport(exportFormat);
    // Close the modal
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} aria-label="Export modal">
      <h2>Export Data</h2>
      <SearchBar />
      <div>
        <label>
          Export format:
          <select value={exportFormat} onChange={handleExportFormatChange}>
            <option value="csv">CSV</option>
            <option value="json">JSON</option>
          </select>
        </label>
      </div>
      <ExportButton onClick={handleExportConfirm} />
    </Modal>
  );
};

// Prop types for the ExportModal component
ExportModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onExport: PropTypes.func.isRequired,
};

export default ExportModal;
```

Please note that the `ExportButton`, `SearchBar`, and `Modal` components are not included in this code. They should be implemented separately and imported into this component.