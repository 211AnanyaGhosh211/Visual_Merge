import React, { createContext, useContext, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

// Internal component that can use useNavigate
function AuthProviderInternal({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Check for existing authentication on app load
  useEffect(() => {
    const checkAuth = () => {
      const savedAuth = localStorage.getItem("isAuthenticated");
      const savedUser = localStorage.getItem("user");

      if (savedAuth === "true" && savedUser) {
        setIsAuthenticated(true);
        setUser(JSON.parse(savedUser));
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = (userData) => {
    // User data comes from API response
    const user = {
      ...userData,
      loginTime: new Date().toISOString(),
    };

    setIsAuthenticated(true);
    setUser(user);

    // Save to localStorage for persistence
    localStorage.setItem("isAuthenticated", "true");
    localStorage.setItem("user", JSON.stringify(user));

    // Navigate to dashboard after successful login
    navigate("/dashboard");
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUser(null);

    // Clear localStorage
    localStorage.removeItem("isAuthenticated");
    localStorage.removeItem("user");

    // Navigate to dashboard (which will redirect to login due to ProtectedRoute)
    navigate("/dashboard");
  };

  const value = {
    isAuthenticated,
    user,
    login,
    logout,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Wrapper component that provides the context
export const AuthProvider = ({ children }) => {
  return <AuthProviderInternal>{children}</AuthProviderInternal>;
};
