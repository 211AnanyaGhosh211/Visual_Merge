import React from 'react';

const SettingOption = ({ label, checked, onChange }) => {
  return (
    <div className="flex items-center justify-between bg-gray-50 dark:bg-neutral-800 p-4 rounded-lg shadow-sm">
      <span className="font-medium text-gray-700 dark:text-gray-200">{label}</span>
      <input 
        type="checkbox" 
        checked={checked}
        onChange={onChange}
        className="form-checkbox h-5 w-5 text-yellow-500 rounded focus:ring-yellow-400" 
      />
    </div>
  );
};

export default SettingOption; 