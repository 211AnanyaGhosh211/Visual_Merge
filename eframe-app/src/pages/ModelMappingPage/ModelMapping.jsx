import React, { useState } from 'react';
import Header from '../../Components/Model_Mapping_Components/Header';
import Footer from '../../Components/Model_Mapping_Components/Footer';
import CameraList from '../../components/Model_Mapping_Components/CameraList';
import ModelSelection from '../../components/Model_Mapping_Components/ModelSelection';

const ModelMapping = () => {
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [selectedModels, setSelectedModels] = useState({
    ppeDetection: false,
    fireHazard: false,
    faceRecognition: false
  });

  const cameras = [
    { id: 1, name: 'Camera 1' },
    { id: 2, name: 'Camera 2' },
    { id: 3, name: 'Camera 3' },
    { id: 4, name: 'Camera 4' },
    { id: 5, name: 'Camera 5' },
    { id: 6, name: 'Camera 6' }
  ];

  const handleModelToggle = (model) => {
    setSelectedModels(prev => ({
      ...prev,
      [model]: !prev[model]
    }));
  };

  const handleMap = () => {
    if (!selectedCamera) {
      alert('Please select a camera first');
      return;
    }

    const selectedModelCount = Object.values(selectedModels).filter(Boolean).length;
    if (selectedModelCount === 0) {
      alert('Please select at least one model');
      return;
    }

    // Here you would typically make an API call to map the camera with the selected models
    console.log('Mapping camera', selectedCamera, 'with models:', selectedModels);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-neutral-800">
      <Header />
      <main className="px-4 py-8">
        <div className="flex flex-col lg:flex-row gap-6 max-w-full mx-auto">
          <CameraList
            cameras={cameras}
            selectedCamera={selectedCamera}
            onCameraSelect={setSelectedCamera}
          />
          <ModelSelection
            selectedModels={selectedModels}
            onModelToggle={handleModelToggle}
            onMap={handleMap}
          />
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default ModelMapping; 