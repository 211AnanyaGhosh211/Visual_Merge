import React, { useState } from "react";
import { useAuth } from "../../contexts/AuthContext";

const Login = () => {
  const [formData, setFormData] = useState({
    adminId: "",
    username: "",
    password: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const { login } = useAuth();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    // Clear error when user starts typing
    if (error) setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    if (!formData.adminId || !formData.username || !formData.password) {
      setError("Please enter Admin ID, Username and Password");
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch("http://localhost:5000/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          adminId: formData.adminId,
          username: formData.username,
          password: formData.password,
        }),
      });

      const data = await response.json();

      if (data.success) {
        // Login successful - call the auth context login function
        login(data.user);
      } else {
        // Login failed - show error message
        setError(data.error || "Login failed");
      }
    } catch (err) {
      console.error("Login error:", err);
      setError("Network error. Please check if the backend server is running.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Background Image */}
      <div className="w-3/5 relative overflow-hidden">
        <img 
          src="/vdashboard.jpg" 
          alt="Industrial Safety Dashboard" 
          className="w-full h-screen object-cover"
        />
        {/* Overlay for better text readability */}
        <div className="absolute inset-0 bg-black bg-opacity-30"></div>
        
        {/* Welcome Text Overlay */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center text-white z-10">
            <h1 className="text-5xl font-bold mb-4">Welcome to Eframe AI</h1>
            <p className="text-2xl font-light">Camera Dashboard</p>
          </div>
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="w-2/5 bg-gradient-to-br from-orange-500 to-orange-400 flex items-center justify-center p-8">
        <div className="bg-gray-100 rounded-2xl p-8 w-full max-w-md shadow-2xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Logo */}
            <div className="text-center mb-8">
              <div className="flex items-center justify-center mb-4">
                <img 
                  src="/Eframe.ai black.png" 
                  alt="Eframe.AI logo" 
                  className="h-12 w-auto object-contain"
                  style={{ 
                    background: 'transparent',
                    mixBlendMode: 'multiply'
                  }}
                />
              </div>
              <h2 className="text-2xl font-bold text-gray-800">Admin Login</h2>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg text-center">
                {error}
              </div>
            )}

            {/* Admin ID Input */}
            <div>
              <input
                type="text"
                name="adminId"
                placeholder="Admin ID"
                value={formData.adminId}
                onChange={handleChange}
                disabled={isLoading}
                className="w-full px-4 py-3 text-gray-700 bg-transparent border-b-2 border-gray-300 focus:border-orange-500 focus:outline-none placeholder-gray-500 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
                required
              />
            </div>

            {/* Username Input */}
            <div>
              <input
                type="text"
                name="username"
                placeholder="Username"
                value={formData.username}
                onChange={handleChange}
                disabled={isLoading}
                className="w-full px-4 py-3 text-gray-700 bg-transparent border-b-2 border-gray-300 focus:border-orange-500 focus:outline-none placeholder-gray-500 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
                required
              />
            </div>

            {/* Password Input */}
            <div>
              <input
                type="password"
                name="password"
                placeholder="Password"
                value={formData.password}
                onChange={handleChange}
                disabled={isLoading}
                className="w-full px-4 py-3 text-gray-700 bg-transparent border-b-2 border-gray-300 focus:border-orange-500 focus:outline-none placeholder-gray-500 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
                required
              />
            </div>

            {/* Login Button */}
            <div className="flex justify-center">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full px-6 py-3 bg-gradient-to-r from-orange-500 to-orange-400 text-white font-semibold rounded-lg text-lg hover:from-orange-600 hover:to-orange-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Logging in...
                  </span>
                ) : (
                  "Login"
                )}
              </button>
            </div>

            {/* Footer Branding */}
            <div className="mt-8 text-center">
              <div className="text-sm text-gray-500 mb-2">Powered by:</div>
              <div className="flex items-center justify-center">
                <span className="text-sm font-bold text-gray-800">Eframe Infomedia Pvt Ltd</span>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
