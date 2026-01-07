import React, { useState, useEffect, useRef } from 'react';
import API_CONFIG, { API_HELPERS, REQUEST_HEADERS } from '../../config/apiConfig';

const RegistrationModal = ({ show, onClose, formData, onChange, onStartCamera, onCaptureComplete }) => {
  const [showCamera, setShowCamera] = useState(false);
  const [streamUrl, setStreamUrl] = useState('');
  const [captureProgress, setCaptureProgress] = useState(0);
  const [isCapturing, setIsCapturing] = useState(false);
  const [captureStatus, setCaptureStatus] = useState('');
  const [showLightingWarning, setShowLightingWarning] = useState(false);
  const [captureStartTime, setCaptureStartTime] = useState(null);
  const [lastProgressTime, setLastProgressTime] = useState(null);
  const [lastProgressValue, setLastProgressValue] = useState(0);
  
  // Use refs to track values that need to be compared in the interval
  const lastProgressTimeRef = useRef(null);
  const lastProgressValueRef = useRef(0);

  useEffect(() => {
    if (!showCamera) {
      setStreamUrl('');
    }
  }, [showCamera]);

  // Poll for capture progress when capturing
  useEffect(() => {
    let interval;
    if (isCapturing) {
      interval = setInterval(async () => {
        try {
          const response = await fetch(API_CONFIG.EMPLOYEE_CONFIGURATION.FACE_CAPTURE_PROGRESS);
          const progress = await response.json();
          const currentTime = Date.now();
          
          // Check if progress has increased using refs for reliable comparison
          if (progress.percentage > lastProgressValueRef.current) {
            // Progress is increasing, hide warning and update tracking
            console.log('Progress increased:', lastProgressValueRef.current, '->', progress.percentage);
            setShowLightingWarning(false);
            lastProgressTimeRef.current = currentTime;
            lastProgressValueRef.current = progress.percentage;
            setLastProgressTime(currentTime);
            setLastProgressValue(progress.percentage);
          } else if (progress.percentage === lastProgressValueRef.current) {
            // Progress is stuck at the same value
            if (lastProgressTimeRef.current) {
              const timeStuck = currentTime - lastProgressTimeRef.current;
              console.log('Progress stuck at', progress.percentage, 'for', timeStuck, 'ms');
              // Check if 10 seconds have passed since progress was last updated
              if (timeStuck >= 10000) {
                console.log('Showing lighting warning - progress stuck for 10+ seconds');
                setShowLightingWarning(true);
              }
            } else {
              // First time we see this progress value, set the time and value
              console.log('First time seeing progress:', progress.percentage);
              lastProgressTimeRef.current = currentTime;
              lastProgressValueRef.current = progress.percentage;
              setLastProgressTime(currentTime);
              setLastProgressValue(progress.percentage);
            }
          } else {
            // Progress decreased or first update, reset tracking
            console.log('Progress decreased or first update:', lastProgressValueRef.current, '->', progress.percentage);
            lastProgressTimeRef.current = currentTime;
            lastProgressValueRef.current = progress.percentage;
            setLastProgressTime(currentTime);
            setLastProgressValue(progress.percentage);
          }
          
          setCaptureProgress(progress.percentage);
          
          if (progress.captured >= progress.target) {
            setIsCapturing(false);
            setCaptureStatus('Capture completed!');
            setShowLightingWarning(false);
            clearInterval(interval);
            // Call the completion handler after a short delay
            setTimeout(() => {
              if (onCaptureComplete) {
                onCaptureComplete();
              }
            }, 2000);
          }
        } catch (error) {
          console.error('Error fetching progress:', error);
        }
      }, 1000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isCapturing, captureStartTime]);

  if (!show) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2 className="text-xl font-bold mb-4">Register Employee</h2>
        <form>
          <div className="mb-4">
            <label htmlFor="employeeName" className="block text-sm font-medium">Employee Name</label>
            <input
              type="text"
              id="employeeName"
              name="employeeName"
              value={formData.employeeName}
              onChange={onChange}
              className="border rounded w-full p-2"
              placeholder="Enter employee name"
              required
            />
          </div>
          <div className="mb-4">
            <label htmlFor="employeeId" className="block text-sm font-medium">Employee ID</label>
            <input
              type="text"
              id="employeeId"
              name="employeeId"
              value={formData.employeeId}
              onChange={onChange}
              className="border rounded w-full p-2"
              placeholder="Enter employee ID"
              required
            />
          </div>

          {showCamera && (
            <div className="mb-4">
              <div className="w-3/4 mx-auto aspect-video bg-neutral-900 rounded-xl flex items-center justify-center relative">
                {streamUrl ? (
                  <>
                    <img
                      src={streamUrl}
                      alt="Camera Feed"
                      className="w-full h-full object-contain rounded-xl"
                      onError={(e) => console.error('Camera feed error:', e)}
                    />
                    {isCapturing && (
                      <div className="absolute top-4 left-4 bg-black bg-opacity-75 text-white p-3 rounded-lg">
                        <div className="text-sm font-medium mb-2">Capture Progress</div>
                        <div className="w-48 bg-gray-700 rounded-full h-2 mb-2">
                          <div 
                            className="bg-green-500 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${captureProgress}%` }}
                          ></div>
                        </div>
                        <div className="text-xs">{Math.round(captureProgress)}% Complete</div>
                      </div>
                    )}
                    {captureStatus && (
                      <div className="absolute top-4 right-4 bg-green-600 text-white p-3 rounded-lg">
                        <div className="text-sm font-medium">{captureStatus}</div>
                      </div>
                    )}
                    {showLightingWarning && (
                      <div className="absolute bottom-4 left-4 right-4 bg-yellow-600 text-white p-3 rounded-lg">
                        <div className="text-sm font-medium">⚠️ Lighting Warning</div>
                        <div className="text-xs mt-1">The lighting is insufficient to clearly capture the face. Please adjust the camera angle accordingly.</div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center text-neutral-400">
                    <i className="fas fa-camera text-4xl mb-4"></i>
                    <p>Camera feed will appear here</p>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="modal-actions" style={{ display: 'flex', justifyContent: 'space-between', gap: '10px' }}>
            <div>
              {!isCapturing ? (
                <button
                  type="button"
                  onClick={async () => {
                    try {
                      // First, start the face capture on the backend
                      const response = await fetch(API_CONFIG.EMPLOYEE_CONFIGURATION.START_FACE_CAPTURE, {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                          employeeName: formData.employeeName,
                          employeeId: formData.employeeId
                        })
                      });
                      
                      const data = await response.json();
                      if (data.status === 'error') {
                        alert(data.message);
                        return;
                      }
                      
                      // If successful, set up the UI states
                      setShowCamera(true);
                      setIsCapturing(true);
                      setCaptureStatus('');
                      setCaptureProgress(0);
                      setShowLightingWarning(false);
                      setCaptureStartTime(Date.now());
                      setLastProgressTime(null);
                      setLastProgressValue(0);
                      lastProgressTimeRef.current = null;
                      lastProgressValueRef.current = 0;
                      
                      // Add a small delay to ensure the camera stream is ready
                      setTimeout(() => {
                        setStreamUrl(API_CONFIG.EMPLOYEE_CONFIGURATION.FACE_CAPTURE_FEED);
                      }, 500);
                      
                    } catch (error) {
                      console.error('Error starting face capture:', error);
                      alert('Error starting face capture');
                    }
                  }}
                  className="btn btn-primary"
                  disabled={!formData.employeeName || !formData.employeeId}
                >
                  {showCamera ? 'Restart Capture' : 'Start Face Capture'}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={async () => {
                    try {
                      const response = await fetch(API_CONFIG.EMPLOYEE_CONFIGURATION.STOP_FACE_CAPTURE, {
                        method: 'POST'
                      });
                      const data = await response.json();
                      setIsCapturing(false);
                      setCaptureStatus(data.message);
                      setShowLightingWarning(false);
                      setCaptureStartTime(null);
                      setLastProgressTime(null);
                      setLastProgressValue(0);
                      lastProgressTimeRef.current = null;
                      lastProgressValueRef.current = 0;
                    } catch (error) {
                      console.error('Error stopping face capture:', error);
                    }
                  }}
                  className="btn btn-warning"
                >
                  Stop Capture
                </button>
              )}
            </div>
            <div>
              <button
                type="button"
                onClick={onClose}
                className="btn btn-danger"
              >
                Cancel
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RegistrationModal; 