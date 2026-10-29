import React, { useState, useEffect, useCallback } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Sidebar } from '../components/navigation/Sidebar';
import { Header } from '../components/navigation/Header';
import { AppSection, SystemStatus } from '../types';
import { api } from '../services/api';

export const RootLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [currentSection, setCurrentSection] = useState<AppSection>(
    location.pathname.startsWith('/cbdc') ? 'cbdc' : 'current_money'
  );

  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    service: null,
    database: null,
    loading: true,
    lastChecked: null,
    error: null,
  });

  const checkConnectivity = useCallback(async () => {
    setSystemStatus((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const { service, database } = await api.checkFullSystem();
      setSystemStatus({
        service,
        database,
        loading: false,
        lastChecked: new Date(),
        error: null,
      });
    } catch (err) {
      setSystemStatus((prev) => ({
        ...prev,
        loading: false,
        lastChecked: new Date(),
        error: (err as Error).message,
      }));
    }
  }, []);

  useEffect(() => {
    checkConnectivity();
  }, [checkConnectivity]);

  const handleSectionChange = (section: AppSection) => {
    setCurrentSection(section);
    if (section === 'current_money') {
      navigate('/current-money/overview');
    } else {
      navigate('/cbdc/overview');
    }
  };

  return (
    <div className="flex h-screen bg-background text-warm-white overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        currentSection={currentSection}
        onSectionChange={handleSectionChange}
      />

      {/* Main Content Area */}
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header
          currentSection={currentSection}
          systemStatus={systemStatus}
          onRefreshHealth={checkConnectivity}
        />

        <main className="flex-1 overflow-y-auto p-6 bg-background">
          <Outlet context={{ systemStatus, refreshConnectivity: checkConnectivity }} />
        </main>
      </div>
    </div>
  );
};

