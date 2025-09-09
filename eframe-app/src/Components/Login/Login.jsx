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
    <div
      className="min-h-screen flex items-center justify-end relative"
      style={{
        backgroundImage: "url(/visual_analytics.jpg)",
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
      }}
    >
      {/* Overlay for better text readability */}
      <div className="absolute inset-0 bg-black bg-opacity-20"></div>

      {/* Login Panel - Right Side */}
      <div className="relative z-10 w-1/3 min-w-[400px] h-screen flex items-center justify-center">
        <div className="bg-white bg-opacity-95 backdrop-blur-sm rounded-2xl p-8 w-full max-w-md mx-8 shadow-2xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* DRIVE360 Logo */}
            <div className="text-center mb-8">
              <div className="text-3xl font-bold">
                <span className="text-orange-500">VISUAL</span>
                <span className="text-black"> ANALYTICS</span>
              </div>
            </div>

            {/* Title */}
            <h1 className="text-2xl font-bold text-gray-800 text-center mb-8">
              Admin Login
            </h1>

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
                className="w-full px-4 py-3 text-gray-700 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent placeholder-gray-400 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
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
                className="w-full px-4 py-3 text-gray-700 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent placeholder-gray-400 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
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
                className="w-full px-4 py-3 text-gray-700 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent placeholder-gray-400 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                required
              />
            </div>

            {/* Login Button */}
            <div className="flex justify-center">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full px-6 py-3 bg-white border border-gray-300 rounded-lg text-gray-800 font-semibold hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
              >
                {isLoading ? "Logging in..." : "Login"}
              </button>
            </div>

            {/* Footer Branding */}
            <div className="mt-8">
              <div className="text-sm text-gray-500 mb-2">Powered by:</div>
              <div className="flex items-center justify-between">
                <div className="flex flex-col">
                  <span className="text-sm font-bold text-black">
                    Eframe Infomedia Pvt Ltd
                  </span>
                  <a
                    href="http://www.eframe.in"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-black underline hover:text-orange-500"
                  >
                    www.eframe.in
                  </a>
                </div>
                <img
                  src="/eframe_logo.jpeg"
                  alt="eframe logo"
                  className="w-12 h-12 object-contain"
                />
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
