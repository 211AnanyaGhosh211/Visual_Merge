import React from 'react';

const NotificationHeader = ({ onRefresh, onClearAll }) => {
  return (
    <div className="notifications-header">
      <h2 className="text-lg font-semibold mb-3 dark:text-white">Recent Notifications</h2>
      <div className="flex flex-wrap gap-2">
        <button
          onClick={onRefresh}
          className="btn btn-primary text-white bg-gray-800 hover:bg-gray-900"
        >
          <i className="fas fa-sync-alt mr-2" color="white"></i>
          Refresh
        </button>
        <button 
          onClick={onClearAll}
          className="btn btn-danger"
        >
          <i className="fas fa-trash-alt mr-2"></i>
          Clear All
        </button>
      </div>
    </div>
  );
};

export default NotificationHeader; 