import React from 'react';
import Header from '../../components/Dashboard_Components/Header';
import Footer from '../../components/Dashboard_Components/Footer';
import WelcomeCard from '../../Components/Dashboard_Components/WelcomeCard';
import AnalyticsDashboard from '../../Components/Dashboard_Components/AnalyticsDashboard';

/**
 * Dashboard Component
 * Main dashboard page that displays welcome message, report generation button,
 * and analytics dashboard in an iframe.
 */
const Dashboard = () => {
  /**
   * Handles the report generation action
   * Redirects to the report generation endpoint
   */
  const handleReportGen = () => {
    window.location.href = 'http://127.0.0.1:5000/report';
  };

  return (
    // Main container with gradient background
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-neutral-900 dark:to-neutral-800">
      {/* Header component with title and subtitle */}
      <Header title="Dashboard" subtitle="Welcome to your EFRAME dashboard" />
      
      {/* Main content area with padding and max width */}
      <main className="p-4 lg:p-8 max-w-9xl mx-auto">
        <WelcomeCard onReportGenerate={handleReportGen} />
        <AnalyticsDashboard />
      </main>
      <Footer />
    </div>
  );
};

export default Dashboard; 