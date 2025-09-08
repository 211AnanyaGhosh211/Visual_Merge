import React from 'react';
import { FaTrash, FaTimes } from 'react-icons/fa';

const DeleteCameraModal = ({ show, onClose, cameraID, onChange, onSubmit }) => {
  if (!show) return null;

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50 transition-all">
      <div className="bg-white p-6 rounded-xl shadow-2xl w-full max-w-md relative animate-fadeIn">
        <button onClick={onClose} className="absolute top-3 right-3 text-gray-400 hover:text-gray-700 text-xl">
          <FaTimes />
        </button>
        <h2 className="text-lg mb-4 font-bold flex items-center gap-2">
          <FaTrash className="text-red-500" /> Delete Camera
        </h2>
        <form onSubmit={onSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700">Camera ID</label>
            <input
              type="text"
              value={cameraID}
              onChange={onChange}
              required
              className="mt-1 block w-full border border-gray-300 rounded-md p-2"
            />
          </div>
          <div className="flex justify-end">
            <button
              type="button"
              onClick={onClose}
              className="bg-gray-300 text-black px-4 py-2 rounded-lg mr-2"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg transition"
            >
              Delete
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default DeleteCameraModal; 