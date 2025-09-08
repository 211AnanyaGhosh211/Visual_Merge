import React, { useState, useEffect } from 'react';
import './EmployeeConfig.css';
import { useTheme } from '../../contexts/ThemeContext';
import { useNavigate } from 'react-router-dom';
import Header from '../../Components/Employee_Configuration_Components/Header';
import Footer from '../../Components/Employee_Configuration_Components/Footer';
import EmployeeStats from '../../Components/Employee_Configuration_Components/EmployeeStats';
import EmployeeSearch from '../../Components/Employee_Configuration_Components/EmployeeSearch';
import EmployeeActions from '../../Components/Employee_Configuration_Components/EmployeeActions';
import EmployeeTable from '../../Components/Employee_Configuration_Components/EmployeeTable';
import RegistrationModal from '../../Components/Employee_Configuration_Components/RegistrationModal';
import DeleteModal from '../../Components/Employee_Configuration_Components/DeleteModal';
import FloatingActionButton from '../../Components/Employee_Configuration_Components/FloatingActionButton';

/**
 * EmployeeConfig Component
 * Manages employee registration, deletion, and displays employee information
 * Includes features for face capture registration and employee management
 * Uses a reusable Header component for consistent navigation
 */
const EmployeeConfig = () => {
  // State management for modals and employee data
  const [showRegistrationModal, setShowRegistrationModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [employees, setEmployees] = useState([]);
  const [formData, setFormData] = useState({
    employeeName: '',
    employeeId: '',
    deleteEmpID: ''
  });

  // Theme and navigation hooks
  const { darkMode, toggleDarkMode } = useTheme();
  const navigate = useNavigate();

  // Fetch employees data on component mount
  useEffect(() => {
    fetchEmployees();
  }, []);

  /**
   * Fetches employee data from the API
   * Updates the employees state with the fetched data
   */
  const fetchEmployees = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/api/employees');
      const data = await response.json();
      console.log('Received employee data:', data);
      setEmployees(data);
    } catch (error) {
      console.error('Error fetching employees:', error);
    }
  };

  /**
   * Handles input changes in form fields
   * Updates formData state with new values
   */
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  /**
   * Initiates the face capture process for employee registration
   * Validates input and sends data to the backend
   */
  const startCamera = async () => {
    const { employeeId, employeeName } = formData;
    
    if (!employeeId || !employeeName) {
      alert('Please enter both Employee ID and Employee Name before starting the camera.');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('employeeName', employeeName);
      formData.append('employeeId', employeeId);

      const response = await fetch('http://127.0.0.1:5000/capture_faces', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (data.status === 'error') {
        alert(data.message);
      } else {
        // Don't close the modal or fetch employees yet
        // Let the user see the camera feed and capture process
        alert(data.message);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('An error occurred while processing your request.');
    }
  };

  /**
   * Handles completion of face capture and employee registration
   */
  const handleFaceCaptureComplete = async () => {
    try {
      // Add the employee to the database
      const formDataToSend = new FormData();
      formDataToSend.append('employeeName', formData.employeeName);
      formDataToSend.append('employeeId', formData.employeeId);

      const response = await fetch('http://127.0.0.1:5000/capture_faces', {
        method: 'POST',
        body: formDataToSend
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        alert('Employee registered successfully!');
        setShowRegistrationModal(false);
        fetchEmployees();
        // Reset form
        setFormData({
          employeeName: '',
          employeeId: '',
          deleteEmpID: ''
        });
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error('Error registering employee:', error);
      alert('An error occurred while registering the employee.');
    }
  };

  /**
   * Handles employee deletion
   * Sends delete request to the backend and updates the employee list
   */
  const handleDeleteEmployee = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch('http://127.0.0.1:5000/api/del_employee', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          employee_id: formData.deleteEmpID
        }),
      });
      
      const data = await response.json();
      alert("Records Deleted Successfully");
      setShowDeleteModal(false);
      fetchEmployees();
    } catch (error) {
      console.error('Error:', error);
      alert('An error occurred while deleting the employee.');
    }
  };

  const handleSearch = (searchTerm) => {
    // Implement search functionality
    console.log('Searching for:', searchTerm);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-neutral-900 dark:to-neutral-800">
      <Header title="Employee Configurations" subtitle="Manage your employee database" />

      <main className="p-4 lg:p-8 space-y-6 lg:space-y-8 max-w-9xl mx-auto">
        <div className="dashboard-card">
          <div className="content">
            <EmployeeStats totalEmployees={employees.length} />
            <EmployeeSearch onSearch={handleSearch} />
            <EmployeeActions
              onAdd={() => setShowRegistrationModal(true)}
              onDelete={() => setShowDeleteModal(true)}
            />
            <EmployeeTable
              employees={employees}
              onDelete={(id) => {
                setFormData(prev => ({ ...prev, deleteEmpID: id }));
                setShowDeleteModal(true);
              }}
              onAddFirst={() => setShowRegistrationModal(true)}
            />
          </div>
          <Footer />
        </div>
      </main>

      <RegistrationModal
        show={showRegistrationModal}
        onClose={() => setShowRegistrationModal(false)}
        formData={formData}
        onChange={handleInputChange}
        onStartCamera={startCamera}
        onCaptureComplete={handleFaceCaptureComplete}
      />

      <DeleteModal
        show={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        employeeId={formData.deleteEmpID}
        onChange={handleInputChange}
        onSubmit={handleDeleteEmployee}
      />

      <FloatingActionButton onClick={() => setShowRegistrationModal(true)} />
    </div>
  );
};

export default EmployeeConfig; 