import React, { useState, useEffect } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { useNavigate } from 'react-router-dom';
import Header from '../../components/Model_Management_Components/Header';
import Footer from '../../Components/Model_Management_Components/Footer';
import ModelHeader from '../../components/Model_Management_Components/ModelHeader';
import ModelActions from '../../components/Model_Management_Components/ModelActions';
import ModelTable from '../../components/Model_Management_Components/ModelTable';

/**
 * ModelManagement Component
 * Manages detection models for the system
 * Provides functionality to add and remove models
 * Displays model information in a table format
 */
const ModelManagement = () => {
  // State management for models list
  const [models, setModels] = useState([]);
  
  // Theme and navigation hooks
  const { darkMode, toggleDarkMode } = useTheme();
  const navigate = useNavigate();

  // Fetch models data on component mount
  useEffect(() => {
    fetchModels();
  }, []);

  /**
   * Fetches models data from the API
   */
  const fetchModels = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/api/models');
      const data = await response.json();
      console.log('Received models data:', data); // Debug log
      setModels(data);
    } catch (error) {
      console.error('Error fetching models:', error);
    }
  };

  /**
   * Adds a new model to the list
   * TODO: Implement API call to add model
   */
  const insertModel = () => {
    // This will need to be updated to make an API call
    console.log('Insert model functionality to be implemented');
  };

  /**
   * Removes a model from the list
   * TODO: Implement API call to delete model
   */
  const deleteModel = () => {
    // This will need to be updated to make an API call
    console.log('Delete model functionality to be implemented');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-neutral-900 dark:to-neutral-800">
      <Header title="Model Management" subtitle="Manage your detection models" />
      
      <main className="p-4 lg:p-8">
        <div className="bg-white dark:bg-neutral-900 rounded-2xl shadow-2xl border border-gray-100 dark:border-neutral-800 px-6 py-8 md:px-10 md:py-10 flex flex-col gap-6 max-w-full mx-auto">
          <div>
            <ModelHeader />
            <ModelActions onInsert={insertModel} onDelete={deleteModel} />
            <hr className="border-gray-200 dark:border-neutral-700 mb-6" />
            <ModelTable models={models} />
          </div>
          <Footer />
        </div>
      </main>
    </div>
  );
};

export default ModelManagement; 