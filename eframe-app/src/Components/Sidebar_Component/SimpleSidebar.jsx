import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTheme } from '../../contexts/ThemeContext';


const SimpleSidebar = ({ children, onSidebarToggle }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const { darkMode, toggleDarkMode } = useTheme();
  const location = useLocation();

  // Update parent component when sidebar state changes
  const handleSidebarToggle = (newState) => {
    setSidebarOpen(newState);
    if (onSidebarToggle) {
      onSidebarToggle(newState);
    }
  };

  const menuItems = [
    { icon: 'fas fa-tachometer-alt', label: 'Dashboard', path: '/dashboard' },
    { icon: 'fas fa-camera', label: 'Camera Dashboard', path: '/camera-dashboard' },
    { icon: 'fas fa-users', label: 'Employee Config', path: '/dashboard/employee-config' },
    { icon: 'fas fa-cogs', label: 'Model Management', path: '/model-management' },
    { icon: 'fas fa-cube', label: 'Model Mapping', path: '/model-mapping' },
    { icon: 'fas fa-video', label: 'Camera Management', path: '/camera-management' },
    { icon: 'fas fa-bell', label: 'Notifications', path: '/notifications' },
<<<<<<< HEAD
    { icon: 'fas fa-cog', label: 'Settings', path: '/settings' },
=======
    // { icon: 'fas fa-cog', label: 'Settings', path: '/settings' },
>>>>>>> 1b3f4c59f6874b5ede756e7016d6acf220c7f29b
  ];

  const Logo = ({ collapsed }) => (
    <div className="relative z-20 flex items-center space-x-2 py-1">
      {!collapsed && (
        <img src="/eframe-logo.png" alt="EFRAME Logo" className="h-16 w-auto" />
      )}
    </div>
  );

  const isExpanded = sidebarOpen || isHovered;

  return (
    <div className="mx-auto flex w-full max-w-none flex-1 flex-col overflow-hidden bg-[#f5ce0b] md:flex-row dark:bg-[#f5ce0b] h-screen">
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-[60] lg:hidden"
          onClick={() => handleSidebarToggle(false)}
        />
      )}

      {/* Sidebar */}
      <div 
        className={`fixed transform z-[70] top-0 left-0
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'} 
          h-screen bg-[#f5ce0b] dark:bg-[#f5ce0b]
          transition-all duration-300 ease-in-out
          w-[280px] lg:w-auto`}
        onMouseEnter={() => !sidebarOpen && setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div className={`flex flex-col justify-between gap-10 h-full p-4 ${isExpanded ? 'lg:w-72' : 'lg:w-16'} transition-all duration-300`}>
          {/* Logo and Navigation */}
          <div className="flex flex-1 flex-col overflow-x-hidden overflow-y-auto">
            {/* Logo */}
            <div className="mb-8 flex items-center justify-between">
              <Logo collapsed={!isExpanded} />
              {/* Close button for mobile */}
              {sidebarOpen && (
                <button 
                  onClick={() => handleSidebarToggle(false)}
                  className="lg:hidden p-2 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-700"
                >
                  <i className="fas fa-times text-neutral-500"></i>
                </button>
              )}
            </div>

            {/* Navigation Links */}
            <div className="flex flex-col gap-2">
              {menuItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center ${!isExpanded ? 'justify-center' : 'justify-start'} gap-3 w-full py-2 px-6 rounded-lg transition-all duration-300 ${
                    location.pathname === item.path
                      ? 'bg-black text-white dark:bg-black dark:text-white'
                      : 'text-black dark:text-black hover:bg-black hover:text-white dark:hover:bg-black dark:hover:text-white'
                  }`}
                >
                  <i className={`${item.icon} h-5 w-5 shrink-0`}></i>
                  <span className={`text-sm whitespace-nowrap transition-all duration-300
                    ${isExpanded ? 'opacity-100 w-auto' : 'lg:w-0 lg:opacity-0 lg:overflow-hidden'}`}>
                    {item.label}
                  </span>
                </Link>
              ))}
            </div>
          </div>

          {/* User Profile */}
          <div className="group relative mt-auto">
            <Link to="/profile" className={`flex items-center ${!isExpanded ? 'justify-center' : 'justify-start'} w-full py-2 px-5 rounded-lg transition-colors duration-300 text-black dark:text-black hover:text-black dark:hover:text-black`}>
              <div className="w-8 h-8 flex items-center justify-center flex-shrink-0">
                <img
                  src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=40&h=40&fit=crop&crop=face"
                  className="w-8 h-8 rounded-full"
                  width={32}
                  height={32}
                  alt="Avatar" 
                />
              </div>
              <span className={`ml-2 text-sm whitespace-nowrap transition-all duration-300
                ${isExpanded ? 'opacity-100 w-auto' : 'lg:w-0 lg:opacity-0 lg:overflow-hidden'}`}>
                Super Admin
              </span>
            </Link>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className={`flex flex-1 min-h-screen transition-[margin] duration-300 ease-in-out
        ${isExpanded ? 'lg:ml-72' : 'lg:ml-16'}`}>
        {/* Mobile Header */}
        <div className="lg:hidden bg-white dark:bg-neutral-800 shadow-sm border-b border-gray-200 dark:border-neutral-700 fixed top-0 left-0 right-0 z-50">
          <div className="flex items-center justify-between px-4 py-3">
            <button 
              onClick={() => handleSidebarToggle(true)}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-700 transition-colors border-2 border-orange-400"
            >
              <i className="fas fa-bars text-gray-600 dark:text-gray-300"></i>
            </button>
            
            <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Camera Dashboard</h1>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={toggleDarkMode}
                className="p-2 rounded-lg bg-gray-100 dark:bg-neutral-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-neutral-600 transition-colors"
                aria-label="Toggle dark mode"
              >
                {darkMode ? (
                  <i className="fas fa-sun text-yellow-500 text-lg"></i>
                ) : (
                  <i className="fas fa-moon text-gray-700 text-lg"></i>
                )}
              </button>
            
              <div className="relative">
                <img
                  src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=40&h=40&fit=crop&crop=face"
                  className="w-8 h-8 rounded-full ring-2 ring-gray-700 dark:ring-gray-300"
                  alt="Avatar"
                />
                <div className="absolute -bottom-1 -right-1 w-2 h-2 bg-green-500 border-2 border-white dark:border-neutral-800 rounded-full"></div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Dashboard Content */}
        <div className="flex h-screen w-full flex-1 flex-col rounded-tl-2xl border border-neutral-200 bg-white dark:border-neutral-700 dark:bg-neutral-900 lg:pt-0 pt-16 overflow-hidden">
          <div className="flex-1 overflow-y-auto">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimpleSidebar; 