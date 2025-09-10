import React, { useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

const DueDateTracker = () => {
  const [selectedDate, setSelectedDate] = useState(null);

  const handleDateChange = (date) => {
    setSelectedDate(date);
  };

  return (
    <div>
      <h2>Due Date Tracker</h2>
      <DatePicker 
        selected={selectedDate} 
        onChange={handleDateChange} 
        dateFormat='dd/MM/yyyy' 
        isClearable 
        placeholderText='Select a date' 
      />
      {selectedDate && (
        <div>
          <p>Selected Date: {selectedDate.toLocaleDateString()}</p>
          {new Date() > selectedDate && <p style={{color: 'red'}}>Task is overdue!</p>}
          {new Date() < selectedDate && <p style={{color: 'green'}}>Upcoming deadline: {selectedDate.toLocaleDateString()}</p>}
        </div>
      )}
    </div>
  );
};

export default DueDateTracker;