import React from 'react';
import SettingsList from './SettingsList';

const SettingsCard = ({ settings, onSettingChange }) => {
  return (
    <div className="bg-white dark:bg-neutral-900 p-6 rounded-2xl shadow-xl border border-gray-100 dark:border-neutral-700">
      <div className="content">
        <h2 className="text-lg font-semibold mb-4 dark:text-white">Settings</h2>
        <SettingsList settings={settings} onSettingChange={onSettingChange} />
      </div>
    </div>
  );
};

export default SettingsCard; 