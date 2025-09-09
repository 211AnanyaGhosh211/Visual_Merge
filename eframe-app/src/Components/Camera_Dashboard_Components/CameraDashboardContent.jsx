import React from 'react';
import Header from '../../components/dashboard/Header';
import Stats from '../../components/dashboard/Stats';
import LiveDetection from '../../components/dashboard/LiveDetection';
import FileAnalysis from '../../components/dashboard/FileAnalysis';
import Footer from '../../Components/dashboard/Footer';

const CameraDashboardContent = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-neutral-900 dark:to-neutral-800">
      <Header />
      
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

export default CameraDashboardContent; 