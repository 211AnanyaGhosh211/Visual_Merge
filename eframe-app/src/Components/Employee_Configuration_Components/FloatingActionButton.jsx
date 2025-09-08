import React from 'react';

const FloatingActionButton = ({ onClick }) => {
  return (
    <button
      className="floating-action"
      onClick={onClick}
      title="Quick Add Employee"
    >
      ➕
    </button>
  );
};

export default FloatingActionButton; 