import React from 'react';

const EmployeeTable = ({ employees, onDelete, onAddFirst }) => {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white dark:bg-neutral-900 rounded-lg overflow-hidden">
        <thead className="bg-gray-50 dark:bg-neutral-800">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Employee ID
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Employee Name
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 dark:divide-neutral-700">
          {employees.length === 0 ? (
            <tr>
              <td colSpan="3" className="px-6 py-4 text-center text-gray-500 dark:text-gray-400">
                No employees found. 
                <button
                  onClick={onAddFirst}
                  className="ml-2 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  Add your first employee
                </button>
              </td>
            </tr>
          ) : (
            employees.map((employee) => (
              <tr key={employee.EmployeeID} className="hover:bg-gray-50 dark:hover:bg-neutral-800">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                  {employee.EmployeeID}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                  {employee.EmployeeName}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  <button
                    onClick={() => onDelete(employee.EmployeeID)}
                    className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default EmployeeTable; 