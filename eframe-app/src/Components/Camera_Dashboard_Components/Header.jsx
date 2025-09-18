import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { useNavigate } from 'react-router-dom';

const Header = ({ title = "Camera Dashboard", subtitle = "Monitor your security systems" }) => {
  const { darkMode, toggleDarkMode } = useTheme();
  const navigate = useNavigate();

  return (
    <div className="bg-[#f5ce0b] dark:bg-[#f5ce0b] shadow-lg border-b border-gray-200 dark:border-neutral-700 sticky top-0 z-30 rounded-none">
      <div className="hidden lg:flex items-center justify-between px-4 lg:px-8 py-4">
        <div className="flex items-center space-x-4">
          <div>
            <h1 className="text-2xl font-bold text-black dark:text-black">{title}</h1>
            <p className="text-sm text-black dark:text-black">{subtitle}</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <label className="inline-flex items-center cursor-pointer">
            <input 
              type="checkbox" 
              checked={darkMode}
              onChange={toggleDarkMode}
              className="sr-only peer"
            />
            <div className="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-black dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-black dark:peer-checked:bg-black"></div>
            <span className="ms-3 text-sm font-medium text-black dark:text-black">
              {darkMode ? 'Light Mode' : 'Dark Mode'}
            </span>
          </label>
          
          <div className="flex items-center space-x-3">
            <span className="hidden sm:block text-sm font-medium text-black dark:text-black">Super Admin</span>
            <div className="relative">
              <button onClick={() => navigate('/profile')} className="focus:outline-none">
                <img 
                  alt="User profile" 
                  className="w-10 h-10 rounded-full border-2 border-blue-200 dark:border-blue-500 hover:border-blue-400 dark:hover:border-blue-400 transition-colors cursor-pointer" 
                  src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=40&h=40&fit=crop&crop=face"
                />
                <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 border-2 border-white dark:border-neutral-800 rounded-full"></div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Header; 