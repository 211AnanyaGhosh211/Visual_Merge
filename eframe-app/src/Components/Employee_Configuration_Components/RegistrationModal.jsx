import React, { useState, useEffect } from 'react';

const RegistrationModal = ({ show, onClose, formData, onChange, onStartCamera, onCaptureComplete }) => {
  const [showCamera, setShowCamera] = useState(false);
  const [streamUrl, setStreamUrl] = useState('');
  const [captureProgress, setCaptureProgress] = useState(0);
  const [isCapturing, setIsCapturing] = useState(false);
  const [captureStatus, setCaptureStatus] = useState('');

  useEffect(() => {
    if (showCamera) {
      setStreamUrl('http://127.0.0.1:5000/face_capture_feed');
    } else {
      setStreamUrl('');
    }
  }, [showCamera]);

  // Poll for capture progress when capturing
  useEffect(() => {
    let interval;
    if (isCapturing) {
      interval = setInterval(async () => {
        try {
          const response = await fetch('http://127.0.0.1:5000/face_capture_progress');
          const progress = await response.json();
          setCaptureProgress(progress.percentage);
          
          if (progress.captured >= progress.target) {
            setIsCapturing(false);
            setCaptureStatus('Capture completed!');
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
  }, [isCapturing]);

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
                    setShowCamera(true);
                    setIsCapturing(true);
                    setCaptureStatus('');
                    setCaptureProgress(0);
                    
                    try {
                      const response = await fetch('http://127.0.0.1:5000/start_face_capture', {
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
                        setIsCapturing(false);
                        setShowCamera(false);
                      }
                    } catch (error) {
                      console.error('Error starting face capture:', error);
                      alert('Error starting face capture');
                      setIsCapturing(false);
                      setShowCamera(false);
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
                      const response = await fetch('http://127.0.0.1:5000/stop_face_capture', {
                        method: 'POST'
                      });
                      const data = await response.json();
                      setIsCapturing(false);
                      setCaptureStatus(data.message);
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