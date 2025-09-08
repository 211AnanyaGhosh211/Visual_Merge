import React from 'react';

const Footer = () => {
  console.log('Footer rendering'); // Debug log
  return (
    <div className="text-center mt-8 text-sm text-gray-600 dark:text-gray-400">
      <p>
        Copyright ©2025 &amp; Developed by
        <a className="text-black hover:text-orange-400 font-bold dark:text-white" href="https://www.eframe.in/" target="_blank" rel="noopener noreferrer">
          {' '}Eframe Infomedia Pvt. Ltd.
        </a>
      </p>
    </div>
  );
};

export default Footer; 