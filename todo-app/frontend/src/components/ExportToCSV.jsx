import React, { useState } from 'react';
import { CSVLink } from 'react-csv';
import PropTypes from 'prop-types';

const ExportToCSV = ({ todos }) => {
  const [csvData, setCsvData] = useState([]);

  const handleExport = () => {
    const formattedData = todos.map(todo => ({
      id: todo.id,
      task: todo.task,
      completed: todo.completed ? 'Yes' : 'No',
    }));
    setCsvData(formattedData);
  };

  return (
    <div>
      <button onClick={handleExport} aria-label="Export todos to CSV">
        Export to CSV
      </button>
      {csvData.length > 0 && (
        <CSVLink data={csvData} filename={"todos.csv"}>
          Download
        </CSVLink>
      )}
    </div>
  );
};

ExportToCSV.propTypes = {
  todos: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      task: PropTypes.string.isRequired,
      completed: PropTypes.bool.isRequired,
    })
  ).isRequired,
};

export default ExportToCSV;