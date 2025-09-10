import React, { useState, useEffect } from 'react';
import AdvancedSearch from './AdvancedSearch';
import CategoryFilter from './CategoryFilter';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { differenceInDays } from 'date-fns';
// Change these imports:
//import PrioritySort from './PrioritySort'
//import DateRangeSelection from './DateRangeSelection'

// To these:
import PrioritySort from './components/PrioritySort'
import DateRangeSelection from './components/DateRangeSelection'

const App = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [category, setCategory] = useState('');
  const [priority, setPriority] = useState('');
  const [dateRange, setDateRange] = useState({ start: null, end: null });
  const [dueDate, setDueDate] = useState(null);
  const [isOverdue, setIsOverdue] = useState(false);

  useEffect(() => {
    if (dueDate) {
      const today = new Date();
      const diffDays = differenceInDays(dueDate, today);
      setIsOverdue(diffDays < 0);
    }
  }, [dueDate]);

  const handleSearch = term => {
    setSearchTerm(term);
  };

  const handleCategoryFilter = category => {
    setCategory(category);
  };

  const handlePrioritySort = priority => {
    setPriority(priority);
  };

  const handleDateRangeSelection = range => {
    setDateRange(range);
  };

  const handleDueDateChange = date => {
    setDueDate(date);
  };

  return (
    <div>
      <AdvancedSearch onSearch={handleSearch} />
      <CategoryFilter onFilter={handleCategoryFilter} />
      <PrioritySort onSort={handlePrioritySort} />
      <DateRangeSelection onSelect={handleDateRangeSelection} />
      <DatePicker selected={dueDate} onChange={handleDueDateChange} />
      {isOverdue && <div style={{ color: 'red' }}>Task is overdue!</div>}
      {/* Existing features/components go here */}
    </div>
  );
};

export default App;