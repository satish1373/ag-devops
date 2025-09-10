```jsx
import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { CSVLink } from 'react-csv';
import Button from '@material-ui/core/Button';
import ErrorOutlineIcon from '@material-ui/icons/ErrorOutline';

const ExportButton = ({ todos }) => {
  const [error, setError] = useState(null);

  const headers = [
    { label: 'ID', key: 'id' },
    { label: 'Title', key: 'title' },
    { label: 'Description', key: 'description' },
    { label: 'Status', key: 'status' },
    { label: 'Created At', key: 'createdAt' },
    { label: 'Updated At', key: 'updatedAt' },
  ];

  const csvReport = {
    filename: 'TodoReport.csv',
    headers: headers,
    data: todos,
  };

  const handleDownload = () => {
    if (!todos.length) {
      setError('No todos available for download');
    }
  };

  return (
    <div>
      {error && (
        <div role="alert">
          <ErrorOutlineIcon color="error" />
          <span>{error}</span>
        </div>
      )}
      <CSVLink {...csvReport} onClick={handleDownload}>
        <Button variant="contained" color="primary">
          Export to CSV
        </Button>
      </CSVLink>
    </div>
  );
};

ExportButton.propTypes = {
  todos: PropTypes.array.isRequired,
};

export default ExportButton;
```

This component uses the `react-csv` library to generate a CSV file from the `todos` prop. The `CSVLink` component is used to create a download link for the CSV file. The `handleDownload` function checks if there are any todos to download and sets an error message if there are none. The error message is displayed using an `ErrorOutlineIcon` and a `span` element. The `Button` component from Material-UI is used to style the download link.