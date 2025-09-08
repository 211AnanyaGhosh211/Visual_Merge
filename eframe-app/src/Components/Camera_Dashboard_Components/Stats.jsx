import React from 'react';

const StatCard = ({ title, value, change, icon, changeColor }) => (
  <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-sm border border-neutral-200 dark:border-neutral-700 p-6 hover:shadow-lg transition-shadow duration-200">
    <div className="flex items-center justify-between">
      <div>
        <h3 className="text-sm font-medium text-neutral-600 dark:text-neutral-300 uppercase tracking-wider">{title}</h3>
        <div className="mt-2 flex items-baseline">
          <p className="text-3xl font-semibold text-neutral-900 dark:text-white">{value}</p>
          <span className={`ml-2 text-sm font-medium ${changeColor}`}>{change}</span>
        </div>
      </div>
      <div className="p-3 bg-neutral-100 dark:bg-neutral-700 rounded-xl">
        <i className={`fas ${icon} text-xl text-neutral-700 dark:text-neutral-200`}></i>
      </div>
    </div>
  </div>
);

const Stats = () => {
  const stats = [
    {
      title: "ACTIVE CAMERAS",
      value: "12",
      change: "+2 from last week",
      icon: "fa-camera",
      changeColor: "text-green-600"
    },
    {
      title: "DETECTIONS",
      value: "847",
      change: "+12% from yesterday",
      icon: "fa-shield-alt",
      changeColor: "text-green-600"
    },
    {
      title: "ALERTS",
      value: "23",
      change: "+3 new alerts",
      icon: "fa-exclamation-triangle",
      changeColor: "text-yellow-600"
    },
    {
      title: "UPTIME",
      value: "99.9%",
      change: "Excellent performance",
      icon: "fa-clock",
      changeColor: "text-blue-600"
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
      {stats.map((stat, index) => (
        <StatCard key={index} {...stat} />
      ))}
    </div>
  );
};

export default Stats; 