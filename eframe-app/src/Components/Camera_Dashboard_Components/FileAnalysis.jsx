import React, { useState } from 'react';

const FileAnalysis = () => {
  const [fileProcessingActive, setFileProcessingActive] = useState(false);
  const [uploadStreamUrl, setUploadStreamUrl] = useState('');
  const [downloadUrl, setDownloadUrl] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  const showAlert = (message, type) => {
    alert(`${type.toUpperCase()}: ${message}`);
  };

  const handleFileUpload = async (file) => {
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      setIsUploading(true);
      showAlert("Processing your file...", "info");
      
      const response = await fetch('http://127.0.0.1:5000/demo2', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      console.log('API Response:', data);
      
      if (data.status === "success") {
        const baseUrl = "http://127.0.0.1:5000";
        const videoUrl = data.video_feed_url.startsWith('http') ? data.video_feed_url : baseUrl + data.video_feed_url;
        const downloadUrl = data.download_url && data.download_url.startsWith('http') ? data.download_url : (data.download_url ? baseUrl + data.download_url : '');
        setUploadStreamUrl(videoUrl);
        setDownloadUrl(downloadUrl);
        setFileProcessingActive(true);
        showAlert("File processing started successfully", "success");
      } else {
        showAlert(data.error || "File processing failed", "error");
      }
    } catch (error) {
      showAlert("Error processing file: " + error.message, "error");
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
    setUploadStreamUrl('');
    setFileProcessingActive(false);
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
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex-1 min-w-[300px]">
            <input 
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
            onClick={() => document.querySelector('input[type="file"]').click()}
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
              {console.log('Current uploadStreamUrl:', uploadStreamUrl)}
              {uploadStreamUrl.match(/\.(jpg|jpeg|png|gif|mp4)$/i) ? (
                <img src={uploadStreamUrl} alt="Processed image" className="w-full h-full object-cover rounded-xl" />
              ) : (
                <video 
                  src={uploadStreamUrl} 
                  controls 
                  className="w-full h-full object-cover rounded-xl"
                  autoPlay
                  loop
                  onError={(e) => console.error('Video Error:', e)}
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

        {fileProcessingActive && (
          <div className="flex flex-wrap gap-4 mt-6">
            <button 
              onClick={handleDownload}
              className="flex items-center px-4 py-2 rounded-lg text-sm font-medium bg-neutral-100 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-100 hover:bg-neutral-200 dark:hover:bg-neutral-600"
            >
              <i className="fas fa-download mr-2"></i>
              Download Result
            </button>
            <button 
              onClick={stopFileProcessing}
              className="flex items-center px-4 py-2 rounded-lg text-sm font-medium bg-neutral-100 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-100 hover:bg-neutral-200 dark:hover:bg-neutral-600"
            >
              <i className="fas fa-stop mr-2"></i>
              Stop Processing
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileAnalysis; 