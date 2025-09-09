import React, { useState, useEffect } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { useNavigate } from 'react-router-dom';
import './Notifications.css';
import Header from '../../components/Notification_Components/Header';
import Footer from '../../Components/Notification_Components/Footer';
import NotificationHeader from '../../components/Notification_Components/NotificationHeader';
import NotificationList from '../../components/Notification_Components/NotificationList';

const Notifications = () => {
  // State to hold the list of notifications
  const [notifications, setNotifications] = useState([]);
  // Access dark mode state and toggle function from ThemeContext
  const { darkMode, toggleDarkMode } = useTheme();
  const navigate = useNavigate();

  // Fetch notifications when the component mounts
  useEffect(() => {
    fetchNotifications();
  }, []);

  // Function to fetch notifications from the API
  const fetchNotifications = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/api/notifications');
      const data = await response.json();
      setNotifications(data);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  // Handler to refresh notifications
  const handleRefresh = () => {
    fetchNotifications();
  };

  // Handler to clear all notifications (currently only clears locally)
  const handleClearAll = () => {
    setNotifications([]);
    // Add API call to clear notifications here
  };

  return (
    // Main background with gradient and dark mode support
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-neutral-900 dark:to-neutral-800">
      {/* Desktop-only Notifications Header */}
      <Header title="Notifications" subtitle="Monitor your security systems" />
      {/* Main content area for notifications */}
      <main className="p-4 lg:p-8 space-y-6 lg:space-y-8 max-w-9xl mx-auto">
        <div className="dashboard-card">
          <div className="content">
            <NotificationHeader onRefresh={handleRefresh} onClearAll={handleClearAll} />
            <NotificationList notifications={notifications} />
          </div>
          {/* Footer with copyright and developer info */}
          <Footer />
        </div>
      </main>
    </div>
  );
};

export default Notifications; 