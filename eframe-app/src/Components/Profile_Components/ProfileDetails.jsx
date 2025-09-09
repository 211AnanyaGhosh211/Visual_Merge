import React from 'react';

const ProfileDetails = ({ user }) => {
  const details = [
    {
      icon: 'fas fa-phone',
      label: 'Phone',
      value: user.phone
    },
    {
      icon: 'fas fa-building',
      label: 'Department',
      value: user.department
    },
    {
      icon: 'fas fa-user-tag',
      label: 'Role',
      value: user.role
    },
    {
      icon: 'fas fa-map-marker-alt',
      label: 'Location',
      value: user.location
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      {details.map((detail, index) => (
        <div key={index} className="bg-gray-50 dark:bg-neutral-800/50 p-6 rounded-2xl hover:shadow-lg transition-all duration-300">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center">
              <i className={`${detail.icon} text-blue-600 dark:text-blue-400 text-xl`}></i>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-500 dark:text-gray-400">{detail.label}</div>
              <div className="text-lg font-semibold text-gray-900 dark:text-white mt-1">{detail.value}</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ProfileDetails; 