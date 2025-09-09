import React from 'react';

const CameraCard = ({ camera, isSelected, onClick }) => {
  return (
    <div
      className={`flex items-center bg-gray-50 dark:bg-neutral-800 p-4 rounded-xl cursor-pointer border-2 transition-all camera-item shadow-sm hover:shadow-lg hover:border-blue-400 ${
        isSelected ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30' : 'border-transparent'
      }`}
      onClick={onClick}
    >
      <i className="fas fa-video text-2xl mr-4 text-blue-500"></i>
      <div>
        <h3 className="text-md font-semibold text-gray-900 dark:text-gray-100">{camera.name}</h3>
        <p className="text-xs text-gray-500 dark:text-gray-300">({camera.id}: {camera.ip})</p>
      </div>
    </div>
  );
};

export default CameraCard; 