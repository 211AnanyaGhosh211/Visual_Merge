import React from "react";
import Header from '../../components/Profile_Components/Header';
import Footer from '../../Components/Profile_Components/Footer';
import ProfileCard from '../../components/Profile_Components/ProfileCard';

/**
 * Profile Component
 * Displays user profile information including:
 * - Profile picture
 * - Basic user information (name, role, email)
 * - Contact details
 * - Department and location information
 * Supports both light and dark mode themes
 */
const Profile = () => {
  // Mock user data - In a real application, this would come from an API or context
  const user = {
    name: "John Doe",
    role: "Super Admin",
    email: "johndoe@example.com",
    phone: "+1 234 567 8901",
    department: "IT",
    location: "New York, USA",
    profilePicture: "https://placehold.co/100x100"
  };

  return (
    // Main container with gradient background
    <div className="min-h-screen bg-gradient-to-br from-gray-100 to-gray-200 dark:from-neutral-900 dark:to-neutral-800">
      {/* Header component with title and subtitle */}
      <Header title="Profile" subtitle="View and edit your profile information" />
      
      {/* Profile content container with proper spacing */}
      <div className="max-w-9xl mx-auto px-4 py-8">
        <ProfileCard user={user} />
        <Footer />
      </div>
    </div>
  );
};

export default Profile; 