import React, { useState } from 'react';

const LiveDetection = () => {
  const [liveDetectionActive, setLiveDetectionActive] = useState(false);
  const [liveStreamUrl, setLiveStreamUrl] = useState('');
  const [error, setError] = useState('');

  const showAlert = (message, type) => {
    alert(`${type.toUpperCase()}: ${message}`);
  };

  const startLiveDetection = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/safetydetection');
      
      const data = await response.json();
      console.log("working",data);
      if (data.stream_url) {
        
        setLiveStreamUrl("http://127.0.0.1:5000" + data.stream_url);
        setLiveDetectionActive(true);
        showAlert("Live detection started successfully", "success");
      }
    } catch (error) {
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
            <img
              src={liveStreamUrl}
              alt="Live Stream"
              className="w-full h-full object-contain rounded-xl"
              onError={(e) => setError('Failed to load video stream')}
            />
          ) : (
            <div className="text-center text-neutral-400">
              <i className="fas fa-video text-4xl mb-4"></i>
              <p>Live stream will appear here</p>
              <p className="text-sm mt-2">Start detection to begin monitoring</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LiveDetection; 