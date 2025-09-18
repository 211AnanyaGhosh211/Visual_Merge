import React, { useState } from 'react';

const LiveDetection = () => {
  const [liveDetectionActive, setLiveDetectionActive] = useState(false);
  const [liveStreamUrl, setLiveStreamUrl] = useState('');
  const [error, setError] = useState('');
  const [selectedCamera, setSelectedCamera] = useState('0'); // Camera number (0-10)
  const [cameraList, setCameraList] = useState({}); // Will be loaded from backend
  const [loading, setLoading] = useState(false);

  const showAlert = (message, type) => {
    alert(`${type.toUpperCase()}: ${message}`);
  };

  // Load cameras from backend on component mount
  React.useEffect(() => {
    loadCameras();
  }, []);

  // Fallback camera list in case API fails
  const fallbackCameras = {
    "0": { name: "Laptop Camera", type: "laptop", url: null, description: "Built-in laptop webcam" },
    "1": { name: "Camera 1", type: "rtsp", url: "rtsp://example.com/stream1", description: "RTSP Camera 1" },
    "2": { name: "Camera 2", type: "rtsp", url: "rtsp://example.com/stream2", description: "RTSP Camera 2" }
  };

  const loadCameras = async () => {
    setLoading(true);
    try {
      console.log("Fetching cameras from: http://127.0.0.1:5000/api/cameras");
      const response = await fetch('http://127.0.0.1:5000/api/cameras');
      console.log("Response status:", response.status);
      console.log("Response headers:", response.headers);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log("Response data:", data);
      setCameraList(data.cameras);
      console.log("Loaded cameras:", data.cameras);
      console.log("Total cameras:", data.total_cameras);
    } catch (error) {
      console.error("Error loading cameras:", error);
      console.error("Error details:", error.message);
      console.log("Using fallback camera list");
      setCameraList(fallbackCameras);
      showAlert(`Using fallback camera list. API Error: ${error.message}`, "warning");
    } finally {
      setLoading(false);
    }
  };

  const startLiveDetection = async () => {
    try {
      console.log("Starting detection with camera:", selectedCamera);
      
      const response = await fetch('http://127.0.0.1:5000/safetydetection', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          camera_id: selectedCamera
        })
      });
      
      const data = await response.json();
      console.log("API Response:", data);
      
      if (data.stream_url) {
        const fullStreamUrl = "http://127.0.0.1:5000" + data.stream_url;
        console.log("Full Stream URL:", fullStreamUrl);
        
        setLiveStreamUrl(fullStreamUrl);
        setLiveDetectionActive(true);
        showAlert(`Live detection started successfully using ${data.camera_name}`, "success");
      } else {
        console.error("No stream_url in response:", data);
        showAlert("No stream URL received from server", "error");
      }
    } catch (error) {
      console.error("Error starting live detection:", error);
      showAlert("Error starting live detection: " + error.message, "error");
    }
  };

  const stopLiveDetection = async () => {
    
    try {
      const response = await fetch('http://127.0.0.1:5000/stopdetection', {
        method: 'POST'
      });
      
      const data = await response.json();
      
      if (data.message === "Detection stopped") {
        
        setLiveStreamUrl('');
        setLiveDetectionActive(false);
        showAlert("Live detection stopped", "info");
      }
    } catch (error) {
      showAlert("Error stopping live detection: " + error.message, "error");
    }
  };

  return (
    <div className="lg:col-span-3 bg-white dark:bg-neutral-800 rounded-2xl shadow-sm border border-neutral-200 dark:border-neutral-700 overflow-hidden">
      <div className="bg-neutral-900 p-6">
        <div className="flex items-center space-x-2 text-white mb-2">
          <i className="fas fa-video"></i>
          <h2 className="text-lg font-semibold">Live Camera Detection</h2>
        </div>
        <p className="text-neutral-400 text-sm">Monitor real-time safety detection</p>
      </div>
      
      <div className="p-6">
        {/* Camera Selection */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300">
              Select Camera
            </label>
            <button
              onClick={loadCameras}
              disabled={loading || liveDetectionActive}
              className="flex items-center px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <i className={`fas fa-sync-alt mr-1 ${loading ? 'animate-spin' : ''}`}></i>
              Refresh
            </button>
          </div>
          
          {/* Simple Camera Dropdown */}
          <div className="mb-4">
            <select
              value={selectedCamera}
              onChange={(e) => setSelectedCamera(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-neutral-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-neutral-900 dark:text-neutral-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={liveDetectionActive || loading}
            >
              {loading ? (
                <option>Loading cameras...</option>
              ) : Object.keys(cameraList).length === 0 ? (
                <option>No cameras available</option>
              ) : (
                Object.keys(cameraList).map((cameraId) => (
                  <option key={cameraId} value={cameraId}>
                    {cameraList[cameraId]?.name || `Camera ${cameraId}`}
                  </option>
                ))
              )}
            </select>
          </div>
          
          {/* Camera Count and Info */}
          <div className="flex items-center justify-between text-xs text-neutral-500 dark:text-neutral-400 mb-2">
            <span>Total cameras: {Object.keys(cameraList).length}</span>
            <span>Selected: Camera {selectedCamera}</span>
          </div>
          
          {/* Camera Info Display */}
          {cameraList[selectedCamera] && (
            <div className="bg-neutral-100 dark:bg-neutral-700 rounded-lg p-3">
              <div className="flex items-center space-x-2 text-sm">
                <i className={`fas ${cameraList[selectedCamera]?.type === 'laptop' ? 'fa-laptop' : 'fa-video'} text-blue-600`}></i>
                <span className="font-medium text-neutral-700 dark:text-neutral-300">
                  {cameraList[selectedCamera]?.name || 'Unknown Camera'}
                </span>
                <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-1 rounded">
                  {cameraList[selectedCamera]?.type?.toUpperCase() || 'UNKNOWN'}
                </span>
              </div>
              {cameraList[selectedCamera]?.description && (
                <div className="mt-1 text-xs text-neutral-600 dark:text-neutral-400">
                  {cameraList[selectedCamera].description}
                </div>
              )}
              {cameraList[selectedCamera]?.type === 'rtsp' && cameraList[selectedCamera]?.url && (
                <div className="mt-1 text-xs text-neutral-600 dark:text-neutral-400">
                  <span className="font-medium">URL:</span> {cameraList[selectedCamera].url}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Control Buttons */}
        <div className="flex flex-wrap gap-4">
          <button
            onClick={startLiveDetection}
            disabled={liveDetectionActive}
            className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium ${
              liveDetectionActive
                ? 'bg-neutral-200 text-neutral-500 cursor-not-allowed'
                : 'bg-black text-white hover:bg-black'
            }`}
          >
            <i className="fas fa-play mr-2"></i>
            Start Live Detection
          </button>
          <button
            onClick={stopLiveDetection}
            disabled={!liveDetectionActive}
            className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium ${
              !liveDetectionActive
                ? 'bg-neutral-200 text-neutral-500 cursor-not-allowed'
                : 'bg-red-600 text-white hover:bg-red-700'
            }`}
          >
            <i className="fas fa-stop mr-2"></i>
            Stop Detection
          </button>
        </div>

        <div className="mt-6 w-3/4 mx-auto aspect-video bg-neutral-900 rounded-xl flex items-center justify-center">
          {liveDetectionActive && liveStreamUrl ? (
            <div className="w-full h-full relative">
              <img
                src={liveStreamUrl}
                alt="Live Stream"
                className="w-full h-full object-contain rounded-xl"
                onLoad={() => {
                  console.log("Stream loaded successfully");
                  setError('');
                }}
                onError={(e) => {
                  console.error("Stream load error:", e);
                  setError('Failed to load video stream');
                }}
              />
              {error && (
                <div className="absolute inset-0 flex items-center justify-center bg-red-900 bg-opacity-75 rounded-xl">
                  <div className="text-center text-red-200">
                    <i className="fas fa-exclamation-triangle text-2xl mb-2"></i>
                    <p className="text-sm">{error}</p>
                    <p className="text-xs mt-1">Check console for details</p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-neutral-400">
              <i className="fas fa-video text-4xl mb-4"></i>
              <p>Live stream will appear here</p>
              <p className="text-sm mt-2">Start detection to begin monitoring</p>
              {liveDetectionActive && !liveStreamUrl && (
                <p className="text-yellow-400 text-xs mt-2">Waiting for stream URL...</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LiveDetection; 