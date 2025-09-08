import React from 'react';

const EmptyState = () => {
  return (
    <div className="empty-state">
      <div className="empty-icon">
        <i className="fas fa-bell"></i>
      </div>
      <div className="empty-title dark:text-white">No Notifications</div>
      <div className="empty-subtitle dark:text-white">
        You're all caught up! There are no new notifications at this time.
      </div>
    </div>
  );
};

export default EmptyState; 