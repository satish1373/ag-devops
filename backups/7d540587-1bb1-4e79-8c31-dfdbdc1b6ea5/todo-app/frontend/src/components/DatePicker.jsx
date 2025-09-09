import React, { useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

const DueDateComponent = () => {
  const [selectedDate, setSelectedDate] = useState(null);

  const handleDateChange = (date) => {
    setSelectedDate(date);
  };

  const isPastDue = () => {
    const today = new Date();
    return selectedDate && selectedDate < today;
  };

  return (
    <div>
      <h2>Due Date</h2>
      <DatePicker 
        selected={selectedDate} 
        onChange={handleDateChange} 
        dateFormat="MM/dd/yyyy"
        isClearable
        placeholderText="Select a date"
      />
      {isPastDue() && <div style={{ color: 'red' }}>Task is overdue!</div>}
    </div>
  );
};

export default DueDateComponent;