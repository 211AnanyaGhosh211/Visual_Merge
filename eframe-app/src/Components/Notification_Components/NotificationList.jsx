import React from 'react';
import NotificationItem from './NotificationItem';
import EmptyState from './EmptyState';

const NotificationList = ({ notifications }) => {
  return (
    <div className="notifications-list">
      {notifications.length === 0 ? (
        <EmptyState />
      ) : (
        notifications.map((notification, index) => (
          <NotificationItem key={index} notification={notification} />
        ))
      )}
    </div>
  );
};

export default NotificationList; 