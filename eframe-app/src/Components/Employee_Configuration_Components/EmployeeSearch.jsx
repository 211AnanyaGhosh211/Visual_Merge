import React from 'react';

const EmployeeSearch = ({ onSearch }) => {
  return (
    <div className="search-bar">
      <div className="search-icon">🔍</div>
      <input
        type="text"
        className="search-input"
        placeholder="Search employees by name or ID..."
        onChange={(e) => onSearch(e.target.value)}
      />
    </div>
  );
};

export default EmployeeSearch; 