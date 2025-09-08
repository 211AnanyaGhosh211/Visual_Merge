import React from 'react';
import CameraCard from './CameraCard';

const CameraList = ({ cameras, selectedCamera, onCameraSelect }) => {
  return (
    <div className="w-full lg:w-3/4 bg-white dark:bg-neutral-900 p-6 rounded-2xl shadow-xl border border-gray-100 dark:border-neutral-700 transition-all">
      <h2 className="text-xl font-semibold mb-2 text-gray-800 dark:text-gray-100">Camera Name</h2>
      <p className="text-sm text-gray-600 dark:text-gray-300 mb-6">
        Select a camera and the necessary models and then click on 'MAP' to map the camera with the model(s).
      </p>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-2 gap-5">
        {cameras.map((camera) => (
          <CameraCard
            key={camera.id}
            camera={camera}
            isSelected={selectedCamera === camera.id}
            onClick={() => onCameraSelect(camera.id)}
          />
        ))}
      </div>
    </div>
  );
};

export default CameraList; 