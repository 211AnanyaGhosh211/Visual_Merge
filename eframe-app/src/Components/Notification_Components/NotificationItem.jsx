import React from 'react';

const NotificationItem = ({ notification }) => {
  return (
    <div className="notification">
      <div className="notification-header dark:text-white">
        <strong>{notification.Exception_Type}</strong>
        <span className="notification-time">{notification.time_ago}</span>
      </div>
      <div className="notification-content">
        <p>Employee: {notification.Username}</p>
        {notification.image_url && (
          <div className="incident-image mt-2">
            <img 
              src={notification.image_url} 
              alt="Incident capture" 
              className="rounded-lg max-w-full h-auto"
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default NotificationItem; 