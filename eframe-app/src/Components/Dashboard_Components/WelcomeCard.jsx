import React from 'react';
import ReportGenerator from './ReportGenerator';

const WelcomeCard = () => {
  return (
    <div className="bg-white dark:bg-neutral-900 rounded-2xl shadow-2xl border border-gray-100 dark:border-neutral-800 px-6 py-8 md:px-10 md:py-10 flex flex-col gap-4 mt-6">
      <h2 className="text-2xl font-bold mb-1 text-gray-800 dark:text-gray-100">
        Welcome to EFRAME Dashboard
      </h2>
      <div className="flex items-center gap-4 mb-2">
        <ReportGenerator  />
      </div>
    </div>
  );
};

export default WelcomeCard; 