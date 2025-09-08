import React from 'react';

const ModelTable = ({ models }) => {
  return (
    <div className="overflow-x-auto rounded-lg shadow">
      <table className="w-full border-collapse bg-white dark:bg-neutral-900 rounded-lg">
        <thead className="sticky top-0 z-10">
          <tr className="bg-yellow-400 text-black text-base">
            <th className="border-b border-gray-300 dark:border-neutral-700 p-3 font-bold">Model ID</th>
            <th className="border-b border-gray-300 dark:border-neutral-700 p-3 font-bold">Model Name</th>
            <th className="border-b border-gray-300 dark:border-neutral-700 p-3 font-bold">Model Use</th>
          </tr>
        </thead>
        <tbody>
          {models.map((mod, idx) => (
            <tr
              key={mod.Model_ID}
              className={
                `transition-colors ${idx % 2 === 0 ? 'bg-gray-50 dark:bg-neutral-800' : 'bg-white dark:bg-neutral-900'} hover:bg-blue-50 dark:hover:bg-blue-900/30`
              }
            >
              <td className="p-3 text-gray-800 dark:text-gray-100 text-center">{mod.Model_ID}</td>
              <td className="p-3 text-gray-800 dark:text-gray-100 text-center">{mod.Modelname}</td>
              <td className="p-3 text-gray-800 dark:text-gray-100 text-center">{mod.Model_Use}</td>
            </tr>
          ))}
          {models.length === 0 && (
            <tr>
              <td colSpan={3} className="text-center text-gray-400 dark:text-gray-500 py-4">
                No models available.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default ModelTable; 