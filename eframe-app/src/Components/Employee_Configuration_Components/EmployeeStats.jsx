import React from 'react';

const EmployeeStats = ({ totalEmployees }) => {
  return (
    <div className="stats-grid">
      <div className="stat-card">
        <div className="stat-number">{totalEmployees}</div>
        <div className="stat-label">Total Employees</div>
      </div>
      {/* <div className="stat-card">
        <div className="stat-number">{totalEmployees}</div>
        <div className="stat-label">Active Users</div>
      </div>
      <div className="stat-card">
        <div className="stat-number">1</div>
        <div className="stat-label">Departments</div>
      </div> */}
    </div>
  );
};

export default EmployeeStats; 