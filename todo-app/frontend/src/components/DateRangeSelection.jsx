import React, { useState } from 'react';
import { DateRangePicker } from 'react-date-range';
import 'react-date-range/dist/styles.css'; 
import 'react-date-range/dist/theme/default.css'; 

const DateRangeSelection = ({ onDateRangeChange }) => {
    const [state, setState] = useState([
        {
            startDate: new Date(),
            endDate: null,
            key: 'selection'
        }
    ]);

    const handleSelect = ranges => {
        setState([ranges.selection]);
        onDateRangeChange(ranges.selection);
    };

    return (
        <div>
            <DateRangePicker
                ranges={state}
                onChange={handleSelect}
                color="#3d91ff"
                rangeColors={["#3d91ff", "#3d91ff", "#3d91ff"]}
            />
        </div>
    );
};

export default DateRangeSelection;