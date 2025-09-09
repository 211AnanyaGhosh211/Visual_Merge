import React, { useState, useEffect } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { useNavigate } from 'react-router-dom';
import Header from '../../components/Settings_Components/Header';
import Footer from '../../Components/Settings_Components/Footer';
import SettingsCard from '../../components/Settings_Components/SettingsCard';

const Settings = () => {
  console.log('Settings component rendering'); // Debug log

  // Access dark mode state and toggle function from ThemeContext
  const { darkMode, toggleDarkMode } = useTheme();
  const navigate = useNavigate();

  const [settings, setSettings] = useState({
    notifications: true,
    darkMode: darkMode,
    autoUpdates: true
  });

  useEffect(() => {
    console.log('Settings mounted, current settings:', settings); // Debug log
  }, []);

  const handleSettingChange = (setting) => {
    console.log('Setting changed:', setting); // Debug log
    setSettings(prev => {
      const newSettings = {
        ...prev,
        [setting]: !prev[setting]
      };

      // Handle dark mode toggle
      if (setting === 'darkMode') {
        toggleDarkMode();
      }

      // Here you would typically make an API call to save the settings
      console.log('New settings:', newSettings); // Debug log
      
      return newSettings;
    });
  };

  return (
    // Main background with gradient and dark mode support
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-neutral-900 dark:to-neutral-800">
      {/* Desktop-only yellow header bar for Settings page */}
      <Header title="Settings" subtitle="Manage your settings" />

      {/* Main content area for settings */}
      <main className="p-4 lg:p-8 max-w-9xl mx-auto">
        <SettingsCard settings={settings} onSettingChange={handleSettingChange} />

        {/* Footer with copyright and developer info */}
        <Footer />
      </main>
    </div>
  );
};

export default Settings; 