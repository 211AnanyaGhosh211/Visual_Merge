import React from 'react';

const DeleteModal = ({ show, onClose, employeeId, onChange, onSubmit }) => {
  if (!show) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2 className="text-lg mb-4">Delete Employee Record</h2>
        <form onSubmit={onSubmit}>
          <div className="mb-4">
            <label htmlFor="deleteEmpID" className="block text-sm font-medium">
              Employee ID
            </label>
            <input
              type="text"
              id="deleteEmpID"
              name="deleteEmpID"
              value={employeeId}
              onChange={onChange}
              required
              className="mt-1 block w-full border border-gray-300 rounded-md p-2"
            />
          </div>
          <div className="flex justify-end">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-primary mr-2"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-danger"
            >
              Delete
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default DeleteModal; 