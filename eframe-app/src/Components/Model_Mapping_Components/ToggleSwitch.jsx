import React from 'react';

const ToggleSwitch = ({ checked, onChange, label }) => {
  return (
    <div className="flex justify-between items-center">
      <span className="font-medium text-gray-700 dark:text-gray-200">{label}</span>
      <label className="switch">
        <input
          type="checkbox"
          checked={checked}
          onChange={onChange}
        />
        <span className="slider round"></span>
      </label>
    </div>
  );
};

export default ToggleSwitch; 