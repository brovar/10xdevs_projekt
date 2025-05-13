import React from 'react';
import { useSearchParams } from 'react-router-dom';
import UsersManagementTab from './tabs/UsersManagementTab';

const AdminDashboardPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'users'; // Default to users tab
  
  // Define tabs
  const tabs = [
    { key: 'users', title: 'Użytkownicy', component: UsersManagementTab },
    { key: 'offers', title: 'Oferty' },
    { key: 'orders', title: 'Zamówienia' },
    { key: 'logs', title: 'Logi systemowe' }
  ];
  
  // Handle tab selection
  const handleTabSelect = (tabKey) => {
    setSearchParams({ tab: tabKey });
  };
  
  // Find the active tab
  const activeTabData = tabs.find(tab => tab.key === activeTab) || tabs[0];
  
  return (
    <div className="container py-4">
      <div className="row mb-4">
        <div className="col">
          <h1>Panel Administratora</h1>
          <p className="text-muted">Zarządzaj użytkownikami, ofertami, zamówieniami i przeglądaj logi systemowe.</p>
        </div>
      </div>
      
      {/* Simple tabs navigation */}
      <ul className="nav nav-tabs mb-4">
        {tabs.map(tab => (
          <li key={tab.key} className="nav-item">
            <button
              className={`nav-link ${activeTab === tab.key ? 'active' : ''}`}
              onClick={() => handleTabSelect(tab.key)}
              aria-current={activeTab === tab.key ? 'page' : undefined}
            >
              {tab.title}
            </button>
          </li>
        ))}
      </ul>
      
      {/* Tab content */}
      <div className="tab-content">
        {activeTabData.component ? (
          <activeTabData.component />
        ) : (
          <div className="alert alert-info">
            Implementacja zakładki {activeTabData.title} jest w trakcie rozwoju.
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboardPage; 