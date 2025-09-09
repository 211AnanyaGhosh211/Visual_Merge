import React from 'react';
import { FaPlus, FaTrash } from 'react-icons/fa';

const CameraActions = ({ onInsert, onDelete }) => {
  return (
    <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
      <button
        onClick={onInsert}
        className="flex items-center justify-center gap-2 bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg shadow transition w-full sm:w-auto"
      >
        <FaPlus /> Insert
      </button>
      <button
        onClick={onDelete}
        className="flex items-center justify-center gap-2 bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg shadow transition w-full sm:w-auto"
      >
        <FaTrash /> Delete
      </button>
    </div>
  );
};

export default CameraActions; 