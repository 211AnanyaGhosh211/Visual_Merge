import React from 'react';
import ToggleSwitch from './ToggleSwitch';

const ModelSelection = ({ selectedModels, onModelToggle, onMap }) => {
  return (
    <div className="w-full lg:w-1/4 bg-white dark:bg-neutral-900 p-6 rounded-2xl shadow-xl border border-gray-100 dark:border-neutral-700 transition-all">
      <h2 className="text-xl font-semibold mb-2 text-gray-800 dark:text-gray-100">Model Name</h2>
      <p className="text-sm text-gray-600 dark:text-gray-300 mb-6">
        Select the models you want to map with the camera.
      </p>
      
      <div className="space-y-4">
        <ToggleSwitch
          label="PPE Detection"
          checked={selectedModels.ppeDetection}
          onChange={() => onModelToggle('ppeDetection')}
        />
        <ToggleSwitch
          label="Fire Hazard"
          checked={selectedModels.fireHazard}
          onChange={() => onModelToggle('fireHazard')}
        />
        <ToggleSwitch
          label="Face Recognition"
          checked={selectedModels.faceRecognition}
          onChange={() => onModelToggle('faceRecognition')}
        />
      </div>
      
      <button
        onClick={onMap}
        className="w-full mt-6 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
      >
        MAP
      </button>
    </div>
  );
};

export default ModelSelection; 