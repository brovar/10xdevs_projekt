import React from 'react';
import { useSearchParams } from 'react-router-dom';
import UsersManagementTab from './tabs/UsersManagementTab';

const AdminDashboardPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'users'; // Default to users tab
  
  // Define tabs
  const tabs = [
    { key: 'users', title: 'Users', component: UsersManagementTab },
    { key: 'offers', title: 'Offers' },
    { key: 'orders', title: 'Orders' },
    { key: 'logs', title: 'System Logs' }
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
          <h1>Admin Dashboard</h1>
          <p className="text-muted">Manage users, offers, orders, and view system logs.</p>
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
            Implementation of the {activeTabData.title} tab is under development.
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboardPage; 