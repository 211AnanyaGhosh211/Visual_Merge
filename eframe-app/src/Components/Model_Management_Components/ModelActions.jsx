import React from 'react';

const ModelActions = ({ onInsert, onDelete }) => {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-6">
      {/* <button
        className="flex items-center gap-2 bg-green-500 text-white px-5 py-2 rounded-lg font-semibold shadow hover:bg-green-600 transition-colors focus:outline-none focus:ring-2 focus:ring-green-400"
        onClick={onInsert}
      >
        <i className="fas fa-plus"></i> Insert
      </button>
      <button
        className="flex items-center gap-2 bg-red-500 text-white px-5 py-2 rounded-lg font-semibold shadow hover:bg-red-600 transition-colors focus:outline-none focus:ring-2 focus:ring-red-400"
        onClick={onDelete}
      >
        <i className="fas fa-trash"></i> Delete
      </button> */}
    </div>
  );
};

export default ModelActions; 