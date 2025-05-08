import React from 'react';

const Footer = () => {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="bg-light py-3 mt-auto">
      <div className="container text-center">
        <p className="mb-0">
          &copy; {currentYear} Steambay. Wszelkie prawa zastrzeżone.
        </p>
        <p className="small text-muted mb-0">
          Projekt edukacyjny - platforma handlowa
        </p>
      </div>
    </footer>
  );
};

export default Footer; 