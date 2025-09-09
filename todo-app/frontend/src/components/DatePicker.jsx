import React, { useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

const DueDateComponent = () => {
  const [selectedDate, setSelectedDate] = useState(null);

  const handleDateChange = (date) => {
    setSelectedDate(date);
  };

  return (
    <div>
      <h2>Select Due Date</h2>
      <DatePicker 
        selected={selectedDate} 
        onChange={handleDateChange} 
        dateFormat='dd/MM/yyyy' 
        isClearable 
        showYearDropdown 
        scrollableMonthYearDropdown 
        aria-label="Select due date"
      />
    </div>
  );
};

export default DueDateComponent;