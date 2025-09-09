import React from 'react';

const EmployeeActions = ({ onAdd, onDelete }) => {
  return (
    <div className="action-bar">
      <button
        className="btn btn-primary"
        style={{
          background: "linear-gradient(189deg, #000000 0%, #090909 100%)",
          boxShadow: "3px 1px 11px rgba(168, 168, 168, 0.3)"
        }}
        onClick={onAdd}
      >
        <span>👤</span> Add New Employee
      </button>
      <button
        className="btn btn-danger"
        style={{
          background: "linear-gradient(189deg, #000000 0%, #090909 100%)",
          boxShadow: "3px 1px 11px rgba(168, 168, 168, 0.3)"
        }}
        onClick={onDelete}
      >
        <span>🗑️</span> Delete Employee
      </button>
    </div>
  );
};

export default EmployeeActions; 