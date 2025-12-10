import React from 'react';

interface TopNavProps {
    activeTab: string;
    onTabChange: (tab: string) => void;
}

const TopNav: React.FC<TopNavProps> = ({ activeTab, onTabChange }) => {
    const tabs = [
        { id: 'dashboard', label: 'Dashboard' },
        { id: 'infrastructure', label: 'Infrastructure' },
        { id: 'incidents', label: 'Incidents' },
    ];

    return (
        <nav style={{
            background: 'rgba(11, 26, 38, 0.95)',
            backdropFilter: 'blur(10px)',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            padding: '0 2rem',
            position: 'sticky',
            top: 0,
            zIndex: 100,
        }}>
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                maxWidth: '1600px',
                margin: '0 auto',
                height: '64px',
            }}>
                {/* Logo */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '8px',
                        background: 'linear-gradient(135deg, #FF5A00, #FF7A33)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 700,
                        fontSize: '18px',
                        color: 'white',
                    }}>
                        CS
                    </div>
                    <div>
                        <div style={{ fontWeight: 600, color: '#F8FAFC', fontSize: '16px' }}>
                            Pipeline Health Monitor
                        </div>
                        <div style={{ fontSize: '12px', color: '#94A3B8' }}>
                            AI/ML Infrastructure
                        </div>
                    </div>
                </div>

                {/* Tabs */}
                <div style={{ display: 'flex', gap: '4px' }}>
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => onTabChange(tab.id)}
                            style={{
                                padding: '8px 16px',
                                background: activeTab === tab.id ? 'rgba(255, 90, 0, 0.15)' : 'transparent',
                                border: 'none',
                                borderRadius: '6px',
                                color: activeTab === tab.id ? '#FF5A00' : '#CBD5E1',
                                fontSize: '14px',
                                fontWeight: 500,
                                cursor: 'pointer',
                                transition: 'all 0.15s ease',
                            }}
                            onMouseEnter={(e) => {
                                if (activeTab !== tab.id) {
                                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                                }
                            }}
                            onMouseLeave={(e) => {
                                if (activeTab !== tab.id) {
                                    e.currentTarget.style.background = 'transparent';
                                }
                            }}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Status indicator */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '6px 12px',
                        background: 'rgba(16, 185, 129, 0.15)',
                        borderRadius: '20px',
                    }}>
                        <div className="status-dot healthy" />
                        <span style={{ fontSize: '13px', color: '#34D399' }}>System Operational</span>
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default TopNav;
