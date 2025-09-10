import React, { useState, useEffect } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

const NotificationSystem = () => {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [isOverdue, setIsOverdue] = useState(false);

  useEffect(() => {
    const today = new Date();
    if (selectedDate < today) {
      setIsOverdue(true);
    } else {
      setIsOverdue(false);
    }
  }, [selectedDate]);

  const handleDateChange = (date) => {
    setSelectedDate(date);
  };

  return (
    <div>
      <DatePicker selected={selectedDate} onChange={handleDateChange} />
      {isOverdue && (
        <div role="alert">
          <p>Task is overdue!</p>
        </div>
      )}
    </div>
  );
};

export default NotificationSystem;