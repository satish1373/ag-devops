import React from 'react';

const PrioritySort = ({ onSort }) => {
  return (
    <div>
      <label htmlFor="prioritySort">Sort by priority:</label>
      <select id="prioritySort" onChange={e => onSort(e.target.value)}>
        <option value="">None</option>
        <option value="low">Low</option>
        <option value="medium">Medium</option>
        <option value="high">High</option>
      </select>
    </div>
  );
};

export default PrioritySort;