import React, { useState, useEffect } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

const DueDateTracker = () => {
  const [selectedDate, setSelectedDate] = useState(null);
  const [isOverdue, setIsOverdue] = useState(false);

  useEffect(() => {
    if (selectedDate && new Date() > selectedDate) {
      setIsOverdue(true);
    } else {
      setIsOverdue(false);
    }
  }, [selectedDate]);

  return (
    <div>
      <h2>Due Date Tracker</h2>
      <DatePicker 
        selected={selectedDate} 
        onChange={date => setSelectedDate(date)} 
        dateFormat='dd/MM/yyyy' 
        isClearable 
        placeholderText='Select a date' 
      />
      {isOverdue && <div role="alert">Task is overdue!</div>}
    </div>
  );
};

export default DueDateTracker;