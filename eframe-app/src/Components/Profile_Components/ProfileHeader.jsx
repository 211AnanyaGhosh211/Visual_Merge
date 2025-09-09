import React from 'react';

const ProfileHeader = ({ user }) => {
  return (
    <div className="flex flex-col items-center mb-8">
      <div className="relative">
        <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full blur opacity-30"></div>
        <img
          src={user.profilePicture || "https://placehold.co/100x100"}
          alt="Profile"
          className="relative w-32 h-32 rounded-full border-4 border-white dark:border-neutral-800 shadow-xl object-cover"
        />
        <div className="absolute bottom-0 right-0 w-8 h-8 bg-green-500 border-4 border-white dark:border-neutral-800 rounded-full"></div>
      </div>
      
      <div className="mt-6 text-center">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          {user.name}
        </h1>
        <div className="mt-2 px-4 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-full text-sm font-medium inline-block">
          {user.role}
        </div>
        <div className="mt-3 text-gray-600 dark:text-gray-400 flex items-center justify-center gap-2">
          <i className="fas fa-envelope"></i>
          {user.email}
        </div>
      </div>
    </div>
  );
};

export default ProfileHeader; 