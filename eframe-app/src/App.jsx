import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import SimpleSidebar from './Components/Sidebar_Component/SimpleSidebar'
import CameraDashboard from './pages/Camera_Dashboard/CameraDashboard'
import EmployeeConfig from './pages/EmployeeConfigurationPage/EmployeeConfig'
import Notifications from './pages/NotificationPage/Notifications'
// import Settings from './pages/SettingsPage/Settings'
import ModelMapping from './pages/ModelMappingPage/ModelMapping'
import ModelManagement from './pages/ModelManagementPage/ModelManagement'
import Dashboard from './pages/dashboard/Dashboard'
import Profile from './pages/ProfilePage/Profile'
import CameraManagement from './pages/Camera_Management/CameraManagement'
import { ThemeProvider } from './contexts/ThemeContext'
import './App.css'

function BlankDashboard() {
  return <div className="flex items-center justify-center h-full w-full text-gray-400 text-2xl">Dashboard Page (Blank)</div>;
}

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <ThemeProvider>
      <Router>
        <SimpleSidebar onSidebarToggle={setSidebarOpen}>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/camera-dashboard" element={<CameraDashboard />} />
            <Route path="/dashboard/employee-config" element={<EmployeeConfig />} />
            <Route path="/notifications" element={<Notifications />} />
            {/* <Route path="/settings" element={<Settings />} /> */}
            <Route path="/model-mapping" element={<ModelMapping />} />
            <Route path="/model-management" element={<ModelManagement />} />
            <Route path="/camera-management" element={<CameraManagement />} />
            <Route path="/profile" element={<Profile />} />
          </Routes>
        </SimpleSidebar>
      </Router>
    </ThemeProvider>
  )
}

export default App
