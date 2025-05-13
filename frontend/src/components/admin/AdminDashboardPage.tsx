import React, { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import TabsComponent from './TabsComponent.tsx';
import { TabDefinition } from '../../types/viewModels.ts';

// Import tab components (we'll create placeholder components for now)
import UsersManagementTab from './tabs/UsersManagementTab.tsx';
import OffersManagementTab from './tabs/OffersManagementTab.tsx'; 
import OrdersManagementTab from './tabs/OrdersManagementTab.tsx';
import LogsViewerTab from './tabs/LogsViewerTab.tsx';

const AdminDashboardPage: React.FC = () => {
  // Use search params to manage the active tab
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'users'; // Default to users tab
  
  // Define available tabs
  const tabs: TabDefinition[] = [
    { key: 'users', title: 'Użytkownicy', component: UsersManagementTab },
    { key: 'offers', title: 'Oferty', component: OffersManagementTab },
    { key: 'orders', title: 'Zamówienia', component: OrdersManagementTab },
    { key: 'logs', title: 'Logi systemowe', component: LogsViewerTab }
  ];
  
  // Handle tab selection
  const handleTabSelect = (tabKey: string) => {
    setSearchParams({ tab: tabKey });
  };
  
  // Validate tab param on initial load
  useEffect(() => {
    const isValidTab = tabs.some(tab => tab.key === activeTab);
    if (!isValidTab) {
      // If invalid tab is specified, default to users
      setSearchParams({ tab: 'users' });
    }
  }, []);
  
  return (
    <div className="container py-4">
      <div className="row mb-4">
        <div className="col">
          <h1>Panel Administratora</h1>
          <p className="text-muted">Zarządzaj użytkownikami, ofertami, zamówieniami i przeglądaj logi systemowe.</p>
        </div>
      </div>
      
      <TabsComponent 
        tabs={tabs} 
        activeTabKey={activeTab} 
        onTabSelect={handleTabSelect} 
      />
    </div>
  );
};

export default AdminDashboardPage; 