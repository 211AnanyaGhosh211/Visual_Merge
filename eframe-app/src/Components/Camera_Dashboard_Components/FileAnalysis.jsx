import React, { useState, useRef, useEffect } from 'react';

const FileAnalysis = () => {
  const [fileProcessingActive, setFileProcessingActive] = useState(false);
  const [uploadStreamUrl, setUploadStreamUrl] = useState('');
  const [downloadUrl, setDownloadUrl] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [detectionType, setDetectionType] = useState('general');
  const [selectedClasses, setSelectedClasses] = useState(['helmet', 'shoes', 'pvc_suit']);
  const [showClassDropdown, setShowClassDropdown] = useState(false);
  const fileInputRef = useRef(null);
  const dropdownRef = useRef(null);

  // Available PPE classes based on your backend code
  const availableClasses = [
    { id: 'helmet', name: 'Helmet', description: 'Safety helmet/hardhat' },
    { id: 'safety_vest', name: 'Safety Vest', description: 'High visibility vest' },
    { id: 'pvc_suit', name: 'PVC Suit', description: 'Protective suit' },
    { id: 'shoes', name: 'Safety Shoes', description: 'Safety footwear' },
    { id: 'goggles', name: 'Safety Goggles', description: 'Eye protection' }
  ];

  const showAlert = (message, type) => {
    alert(`${type.toUpperCase()}: ${message}`);
  };

  // Complete reset function
  const resetAllStates = () => {
    setFileProcessingActive(false);
    setUploadStreamUrl('');
    setDownloadUrl('');
    setIsUploading(false);
    // Clear the file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Handle class selection
  const handleClassToggle = (classId) => {
    setSelectedClasses(prev => {
      if (prev.includes(classId)) {
        return prev.filter(id => id !== classId);
      } else {
        return [...prev, classId];
      }
    });
  };

  // Handle select all classes
  const handleSelectAll = () => {
    setSelectedClasses(availableClasses.map(cls => cls.id));
  };

  // Handle deselect all classes
  const handleDeselectAll = () => {
    setSelectedClasses([]);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowClassDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Reset processing state when detection type changes
  const handleDetectionTypeChange = (newType) => {
    setDetectionType(newType);
    // Reset all processing-related states
    resetAllStates();
    const typeNames = {
      'general': 'General',
      'zone': 'Zone-based',
      'class': 'Class-based'
    };
    showAlert(`Switched to ${typeNames[newType] || 'Unknown'} detection`, "info");
  };

  const handleFileUpload = async (file) => {
    if (!file) return;
    
    // Prevent upload if already processing
    if (isUploading) {
      showAlert("Please wait for current processing to complete", "warning");
      return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('classes', JSON.stringify(selectedClasses));
    
    console.log('DEBUG: Selected classes:', selectedClasses);
    console.log('DEBUG: Detection type:', detectionType);
    
    try {
      setIsUploading(true);
      showAlert("Processing your file...", "info");
      
      // Choose API endpoint based on detection type
      const apiEndpoint = detectionType === 'general' ? 'demo2' : detectionType === 'zone' ? 'demo3' : 'demo4';
      console.log('DEBUG: Using API endpoint:', apiEndpoint);
      
      const response = await fetch(`http://127.0.0.1:5000/${apiEndpoint}`, {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      console.log('API Response:', data);
      console.log('DEBUG: Response status:', response.status);
      
      if (data.status === "success") {
        const baseUrl = "http://127.0.0.1:5000";
        const videoUrl = data.video_feed_url.startsWith('http') ? data.video_feed_url : baseUrl + data.video_feed_url;
        const downloadUrl = data.download_url && data.download_url.startsWith('http') ? data.download_url : (data.download_url ? baseUrl + data.download_url : '');
        console.log('DEBUG: Video URL:', videoUrl);
        console.log('DEBUG: Download URL:', downloadUrl);
        setUploadStreamUrl(videoUrl);
        setDownloadUrl(downloadUrl);
        setFileProcessingActive(true);
        showAlert("File processing started successfully", "success");
      } else {
        showAlert(data.error || "File processing failed", "error");
        resetAllStates();
      }
    } catch (error) {
      showAlert("Error processing file: " + error.message, "error");
      resetAllStates();
    } finally {
      setIsUploading(false);
    }
  };

  const handleDownload = () => {
    if (downloadUrl) {
      window.location.href = downloadUrl;
    }
  };

  const stopFileProcessing = () => {
    resetAllStates();
    showAlert("File processing stopped", "info");
  };

  return (
    <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-sm border border-neutral-200 dark:border-neutral-700 overflow-hidden">
      <div className="bg-neutral-900 p-6">
        <div className="flex items-center space-x-2 text-white mb-2">
          <i className="fas fa-upload"></i>
          <h2 className="text-lg font-semibold">File Analysis</h2>
        </div>
        <p className="text-neutral-400 text-sm">Upload and analyze video or image files</p>
      </div>
      
      <div className="p-6">
        <div className="flex flex-wrap gap-4 items-center mb-4">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Detection Type
            </label>
            <select 
              value={detectionType}
              onChange={(e) => handleDetectionTypeChange(e.target.value)}
              disabled={isUploading}
              className="w-full px-3 py-2 border border-neutral-200 dark:border-neutral-600 rounded-lg
                bg-white dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="general">General Detection (demo2)</option>
              <option value="zone">Zone-based Detection (demo3)</option>
              <option value="class">Class-based Detection (demo4)</option>
            </select>
          </div>
          
          {detectionType === 'class' && (
            <div className="flex-1 min-w-[250px]">
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                PPE Classes to Detect
              </label>
            <div className="relative" ref={dropdownRef}>
              <button
                type="button"
                onClick={() => setShowClassDropdown(!showClassDropdown)}
                disabled={isUploading}
                className="w-full px-3 py-2 border border-neutral-200 dark:border-neutral-600 rounded-lg
                  bg-white dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                  disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-between"
              >
                <span className="truncate">
                  {selectedClasses.length === 0 
                    ? 'Select PPE classes...' 
                    : selectedClasses.length === availableClasses.length
                    ? 'All classes selected'
                    : `${selectedClasses.length} class${selectedClasses.length > 1 ? 'es' : ''} selected`
                  }
                </span>
                <i className={`fas fa-chevron-${showClassDropdown ? 'up' : 'down'} text-xs`}></i>
              </button>
              
              {showClassDropdown && (
                <div className="absolute z-10 w-full mt-1 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-600 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                  <div className="p-2 border-b border-neutral-200 dark:border-neutral-600">
                    <div className="flex gap-2">
                      <button
                        onClick={handleSelectAll}
                        className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-800"
                      >
                        Select All
                      </button>
                      <button
                        onClick={handleDeselectAll}
                        className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
                      >
                        Clear All
                      </button>
                    </div>
                  </div>
                  {availableClasses.map((cls) => (
                    <label
                      key={cls.id}
                      className="flex items-center p-3 hover:bg-neutral-50 dark:hover:bg-neutral-700 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selectedClasses.includes(cls.id)}
                        onChange={() => handleClassToggle(cls.id)}
                        className="w-4 h-4 text-blue-600 bg-neutral-100 border-neutral-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-neutral-800 focus:ring-2 dark:bg-neutral-700 dark:border-neutral-600"
                      />
                      <div className="ml-3 flex-1">
                        <div className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                          {cls.name}
                        </div>
                        <div className="text-xs text-neutral-500 dark:text-neutral-400">
                          {cls.description}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              )}
            </div>
            </div>
          )}
          
          {fileProcessingActive && (
            <div className="flex items-center gap-2 px-3 py-2 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-lg text-sm">
              <i className="fas fa-circle text-green-500 animate-pulse"></i>
              <span>Processing with {detectionType === 'general' ? 'General' : detectionType === 'zone' ? 'Zone-based' : 'Class-based'} Detection</span>
            </div>
          )}
        </div>
        
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex-1 min-w-[300px]">
            <input 
              ref={fileInputRef}
              type="file" 
              accept="video/*,image/*" 
              onChange={(e) => handleFileUpload(e.target.files[0])}
              className="w-full text-sm text-neutral-500 dark:text-neutral-400
                file:mr-4 file:py-2 file:px-4 
                file:rounded-lg file:border-0 
                file:text-sm file:font-medium
                file:bg-neutral-100 file:text-neutral-700
                file:dark:bg-neutral-700 file:dark:text-neutral-100
                hover:file:bg-neutral-200
                dark:hover:file:bg-neutral-600
                file:cursor-pointer
                border border-neutral-200 dark:border-neutral-600 rounded-lg
                focus:outline-none"
            />
          </div>
          <button 
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-neutral-100 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-100 hover:bg-neutral-200 dark:hover:bg-neutral-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <i className={`${isUploading ? 'fas fa-spinner fa-spin' : 'fas fa-upload'}`}></i>
            {isUploading ? 'Processing...' : 'Upload File'}
          </button>
        </div>

        <div className="mt-6 aspect-video bg-neutral-900 rounded-xl flex items-center justify-center max-w-7xl mx-auto">
          {uploadStreamUrl ? (
            <>
              {uploadStreamUrl.match(/\.(jpg|jpeg|png|gif|mp4)$/i) ? (
                <img src={uploadStreamUrl} alt="Processed image" className="w-full h-full object-cover rounded-xl" />
              ) : (
                <video 
                  src={uploadStreamUrl} 
                  controls 
                  className="w-full h-full object-cover rounded-xl"
                  autoPlay
                  loop
                  muted
                  playsInline
                  onError={(e) => {
                    console.error('Video Error:', e);
                    console.error('Video Error Details:', {
                      error: e.target.error,
                      networkState: e.target.networkState,
                      readyState: e.target.readyState,
                      src: e.target.src
                    });
                    showAlert(`Video Error: ${e.target.error?.message || 'Connection reset. Try again.'}`, "error");
                  }}
                  onLoadStart={() => console.log('DEBUG: Video load started')}
                  onCanPlay={() => console.log('DEBUG: Video can play')}
                  onLoad={() => console.log('DEBUG: Video loaded')}
                  onLoadedData={() => console.log('DEBUG: Video data loaded')}
                  onLoadedMetadata={() => console.log('DEBUG: Video metadata loaded')}
                  onPlay={() => console.log('DEBUG: Video started playing')}
                  onPause={() => console.log('DEBUG: Video paused')}
                />
              )}
            </>
          ) : (
            <div className="text-center text-neutral-400">
              <i className="fas fa-file-video text-4xl mb-4"></i>
              <p>Processed video will appear here</p>
              <p className="text-sm mt-2">Upload a file to start analysis</p>
            </div>
          )}
        </div>

        {(fileProcessingActive || uploadStreamUrl || downloadUrl) && (
          <div className="flex flex-wrap gap-4 mt-6">
            {downloadUrl && (
              <button 
                onClick={handleDownload}
                className="flex items-center px-4 py-2 rounded-lg text-sm font-medium bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-800"
              >
                <i className="fas fa-download mr-2"></i>
                Download Result
              </button>
            )}
            {fileProcessingActive && (
              <button 
                onClick={stopFileProcessing}
                className="flex items-center px-4 py-2 rounded-lg text-sm font-medium bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-800"
              >
                <i className="fas fa-stop mr-2"></i>
                Stop Processing
              </button>
            )}
            <button 
              onClick={() => {
                resetAllStates();
                showAlert("All states cleared", "info");
              }}
              className="flex items-center px-4 py-2 rounded-lg text-sm font-medium bg-neutral-100 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-100 hover:bg-neutral-200 dark:hover:bg-neutral-600"
            >
              <i className="fas fa-times mr-2"></i>
              Clear All
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileAnalysis; 