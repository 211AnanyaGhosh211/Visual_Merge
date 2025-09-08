import React, { useState } from 'react';
import Header from '../../components/Camera_Dashboard_Components/Header';
import Stats from '../../Components/Camera_Dashboard_Components/Stats';
import LiveDetection from '../../Components/Camera_Dashboard_Components/LiveDetection';
import FileAnalysis from '../../Components/Camera_Dashboard_Components/FileAnalysis';
import Footer from '../../Components/Camera_Dashboard_Components/Footer';

const CameraDashboard = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-neutral-900 dark:to-neutral-800">
      <Header sidebarOpen={sidebarOpen} onSidebarToggle={setSidebarOpen} />
      
      <main className="p-4 lg:p-8 space-y-6 lg:space-y-8 max-w-9xl mx-auto">
        <Stats />
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <LiveDetection />
        </div>

        <FileAnalysis />
        <Footer />
      </main>
    </div>
  );
};

export default CameraDashboard; 