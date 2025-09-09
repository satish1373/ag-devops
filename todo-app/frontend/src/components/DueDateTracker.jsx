import React, { useState, useEffect } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

const DueDateTracker = () => {
  const [dueDate, setDueDate] = useState(new Date());
  const [isOverdue, setIsOverdue] = useState(false);

  useEffect(() => {
    const today = new Date();
    if (dueDate < today) {
      setIsOverdue(true);
      alert('Task is overdue!');
    } else {
      setIsOverdue(false);
    }
  }, [dueDate]);

  const handleDateChange = (date) => {
    setDueDate(date);
  };

  return (
    <div>
      <h2>Due Date Tracker</h2>
      <DatePicker selected={dueDate} onChange={handleDateChange} />
      {isOverdue && <p style={{ color: 'red' }}>Task is overdue!</p>}
    </div>
  );
};

export default DueDateTracker;