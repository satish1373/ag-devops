import React from 'react';

const ExportModal = ({ todos, onClose }) => {
  const exportToCSV = () => {
    if (!todos || todos.length === 0) {
      alert('No todos to export!');
      return;
    }

    const headers = ['Title', 'Priority', 'Completed', 'Created Date'];
    const csvContent = [
      headers.join(','),
      ...todos.map(todo => [
        `"${todo.title}"`,
        todo.priority,
        todo.completed ? 'Yes' : 'No',
        new Date(todo.created_at).toLocaleDateString()
      ].join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `todos-export.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <h3>Export Options</h3>
        <button onClick={exportToCSV}>Export as CSV</button>
        <button onClick={onClose}>Cancel</button>
      </div>
    </div>
  );
};

export default ExportModal;