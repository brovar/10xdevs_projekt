import React from 'react';

const Footer = () => {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="bg-light py-3 mt-auto">
      <div className="container text-center">
        <p className="mb-0">
          &copy; {currentYear} Steambay. All rights reserved.
        </p>
        <p className="small text-muted mb-0">
          Educational project - e-commerce platform
        </p>
      </div>
    </footer>
  );
};

export default Footer; 