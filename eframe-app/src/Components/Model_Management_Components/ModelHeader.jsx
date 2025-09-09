import React from 'react';

const ModelHeader = () => {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-1 text-gray-800 dark:text-gray-100">
        Model Management
      </h2>
      <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
        Manage your detection models below. You can insert new models or delete existing ones.
      </p>
    </div>
  );
};

export default ModelHeader; 