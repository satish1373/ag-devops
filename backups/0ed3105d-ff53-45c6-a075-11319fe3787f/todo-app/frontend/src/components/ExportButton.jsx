import React from 'react';

const ExportButton = ({ todos }) => {
  const exportToCSV = () => {
    if (!todos || todos.length === 0) {
      alert('No todos to export!');
      return;
    }

    const headers = ['Title', 'Priority', 'Completed', 'Created'];
    const csvContent = [
      headers.join(','),
      ...todos.map(todo => [
        `"${(todo.title || '').replace(/"/g, '""')}"`,
        todo.priority || 'medium',
        todo.completed ? 'Yes' : 'No',
        new Date(todo.created_at).toLocaleDateString()
      ].join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `todos-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  return (
    <button onClick={exportToCSV} className="export-btn">
      Export CSV ({todos?.length || 0} todos)
    </button>
  );
};

export default ExportButton;