import React from 'react';
import KpiStrip from './KpiStrip';
import ChartCard from './ChartCard';
import ChatPanel from './ChatPanel';
import DataTable from './DataTable';

const Dashboard = ({ data, activeFile, chatHistory, onNewMessage, fileProfiles }) => {
    if (!data) {
        return <div className="spinner"></div>;
    }

    const { charts, kpis } = data;
    const activeProfile = fileProfiles.find(p => p.name === activeFile);

    return (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
            {/* KPI Strip Row */}
            <KpiStrip kpis={kpis} filename={activeFile} />
            
            {/* Main 2-Column Layout: Charts + Chatbot */}
            <div style={{ 
                display: 'grid', 
                gridTemplateColumns: '1fr 360px',
                gap: '16px',
                flex: 1, 
                overflow: 'hidden',
                minHeight: 0,
                padding: '16px 24px'
            }}>
                {/* Charts Section (left column) */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '12px',
                    overflow: 'auto',
                    minHeight: 0
                }}>
                    {charts && charts.map((chart, idx) => (
                        <ChartCard key={idx} chart={chart} />
                    ))}
                </div>
                
                {/* Chatbot Sidebar (right column) */}
                <div style={{ 
                    display: 'flex',
                    flexDirection: 'column',
                    minHeight: 0,
                    overflow: 'hidden'
                }}>
                    <ChatPanel 
                        chatHistory={chatHistory} 
                        onNewMessage={onNewMessage}
                        filename={activeFile}
                    />
                </div>
            </div>
            
            {/* Full-Width Data Table (bottom) */}
            {activeProfile?.columns && (
                <div style={{
                    marginTop: '0px',
                    marginBottom: '24px',
                    marginLeft: '24px',
                    marginRight: '24px',
                    display: 'flex',
                    flexDirection: 'column',
                    minHeight: '0',
                    maxHeight: '280px'
                }}>
                    <div className="chart-card" style={{ 
                        minHeight: '280px',
                        flex: 1
                    }}>
                        <div className="chart-title">
                            All tasks — {activeProfile.rows} records
                        </div>
                        <div className="chart-insight">
                            Showing all data · click a filter to drill down
                        </div>
                        <div style={{ overflow: 'auto', flex: 1, minHeight: 0 }}>
                            <DataTable 
                                title="" 
                                data={activeProfile['table_data'] || []} 
                                columns={activeProfile.columns || []}
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Dashboard;
