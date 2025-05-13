import React from 'react';
import { TabDefinition } from '../../types/viewModels.ts';

interface TabsComponentProps {
  tabs: TabDefinition[];
  activeTabKey: string;
  onTabSelect: (tabKey: string) => void;
}

const TabsComponent: React.FC<TabsComponentProps> = ({ 
  tabs, 
  activeTabKey, 
  onTabSelect 
}) => {
  // Find the active tab component
  const activeTab = tabs.find(tab => tab.key === activeTabKey);
  
  return (
    <div className="admin-tabs">
      <ul className="nav nav-tabs mb-4">
        {tabs.map(tab => (
          <li className="nav-item" key={tab.key}>
            <button 
              className={`nav-link ${activeTabKey === tab.key ? 'active' : ''}`} 
              onClick={() => onTabSelect(tab.key)}
              aria-current={activeTabKey === tab.key ? 'page' : undefined}
            >
              {tab.title}
            </button>
          </li>
        ))}
      </ul>
      
      <div className="tab-content">
        {activeTab && (
          <div className="tab-pane fade show active">
            <activeTab.component />
          </div>
        )}
      </div>
    </div>
  );
};

export default TabsComponent; 