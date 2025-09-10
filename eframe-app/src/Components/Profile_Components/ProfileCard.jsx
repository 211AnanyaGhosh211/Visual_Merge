// import React from 'react';
// import ProfileHeader from './ProfileHeader';
// import ProfileDetails from './ProfileDetails';

// const ProfileCard = ({ user }) => {
//   return (
//     <div className="w-full max-w-xl bg-white dark:bg-neutral-800 p-8 rounded-2xl shadow-2xl border border-gray-100 mt-8">
//       <ProfileHeader user={user} />
//       <hr className="my-6" />
//       <ProfileDetails user={user} />
//     </div>
//   );
// };

// export default ProfileCard;

// src/components/Profile_Components/ProfileCard.jsx
import React, { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";
import ProfileHeader from "./ProfileHeader";
import ProfileDetails from "./ProfileDetails";
import ChangePasswordModal from "./ChangePasswordModal";

const ProfileCard = ({ user }) => {
  const { logout } = useAuth();
  const [isChangePasswordModalOpen, setIsChangePasswordModalOpen] =
    useState(false);

  const handleLogout = () => {
    logout();
  };

  const handleChangePassword = () => {
    setIsChangePasswordModalOpen(true);
  };

  return (
    <div className="w-full bg-white dark:bg-neutral-900 p-8 rounded-3xl shadow-xl border border-gray-100 dark:border-neutral-700 backdrop-blur-sm">
      <div className="relative">
        {/* Decorative background elements */}
        <div className="absolute -top-4 -left-4 w-24 h-24 bg-blue-500/10 rounded-full blur-2xl"></div>
        <div className="absolute -bottom-4 -right-4 w-32 h-32 bg-purple-500/10 rounded-full blur-2xl"></div>

        <ProfileHeader user={user} />
        <hr className="my-8 border-gray-200 dark:border-neutral-700" />
        <ProfileDetails user={user} />

        <div className="mt-10 flex flex-wrap gap-4 justify-center">
          <button className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all duration-300 shadow-lg hover:shadow-blue-500/25 flex items-center gap-2">
            <i className="fas fa-edit"></i>
            Edit Profile
          </button>
          <button
            onClick={handleChangePassword}
            className="px-6 py-3 bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-200 rounded-xl hover:bg-gray-200 dark:hover:bg-neutral-700 transition-all duration-300 shadow-lg hover:shadow-gray-500/25 flex items-center gap-2"
          >
            <i className="fas fa-key"></i>
            Change Password
          </button>
          <button className="px-6 py-3 bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-200 rounded-xl hover:bg-gray-200 dark:hover:bg-neutral-700 transition-all duration-300 shadow-lg hover:shadow-gray-500/25 flex items-center gap-2">
            <i className="fas fa-history"></i>
            View Activity Log
          </button>
          <button
            onClick={handleLogout}
            className="px-8 py-3 bg-red-100 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-xl hover:bg-red-200 dark:hover:bg-red-900/30 transition-all duration-300 shadow-lg hover:shadow-red-500/25 flex items-center gap-2"
          >
            <i className="fas fa-sign-out-alt"></i>
            Logout
          </button>
        </div>
      </div>

      {/* Change Password Modal */}
      <ChangePasswordModal
        isOpen={isChangePasswordModalOpen}
        onClose={() => setIsChangePasswordModalOpen(false)}
      />
    </div>
  );
};

export default ProfileCard;
