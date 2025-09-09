import React from 'react';
import SettingOption from './SettingOption';

const SettingsList = ({ settings, onSettingChange }) => {
  return (
    <div className="space-y-4">
      <SettingOption
        label="Enable Notifications"
        checked={settings.notifications}
        onChange={() => onSettingChange('notifications')}
      />
      <SettingOption
        label="Dark Mode"
        checked={settings.darkMode}
        onChange={() => onSettingChange('darkMode')}
      />
      <SettingOption
        label="Auto Updates"
        checked={settings.autoUpdates}
        onChange={() => onSettingChange('autoUpdates')}
      />
    </div>
  );
};

export default SettingsList; 