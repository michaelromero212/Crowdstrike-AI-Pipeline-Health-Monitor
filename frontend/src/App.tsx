import React, { useState } from 'react';
import TopNav from './components/TopNav';
import Dashboard from './pages/Dashboard';
import Infrastructure from './pages/Infrastructure';
import Incidents from './pages/Incidents';

const App: React.FC = () => {
    const [activeTab, setActiveTab] = useState('dashboard');

    const renderPage = () => {
        switch (activeTab) {
            case 'dashboard':
                return <Dashboard />;
            case 'infrastructure':
                return <Infrastructure />;
            case 'incidents':
                return <Incidents />;
            default:
                return <Dashboard />;
        }
    };

    return (
        <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
            <TopNav activeTab={activeTab} onTabChange={setActiveTab} />
            <main style={{ flex: 1 }}>
                {renderPage()}
            </main>
            <footer style={{
                padding: '16px 24px',
                borderTop: '1px solid rgba(255, 255, 255, 0.05)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: '12px',
                color: '#64748B'
            }}>
                <span>CrowdStrike AI Pipeline Health Monitor v0.1.0</span>
                <span>Demo Application for Interview Presentation</span>
            </footer>
        </div>
    );
};

export default App;
