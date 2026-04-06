import React from 'react';

// Map color name to CSS class name
const colorClassMap = {
    blue: 'blue',
    green: 'green',
    yellow: 'amber',
    amber: 'amber',
    red: 'red',
    purple: 'purple',
};

const KpiStrip = ({ kpis, filename }) => {
    const renderKpis = () => {
        if (kpis && kpis.length > 0) {
            return kpis.slice(0, 5).map((kpi, index) => {
                const colorClass = colorClassMap[kpi.color?.toLowerCase()] || 'blue';
                return (
                    <div key={index} className="kpi-card" style={{
                        background: 'var(--bg-card)',
                        border: '1px solid var(--border)',
                        borderRadius: '12px',
                        padding: '16px 14px',
                        minWidth: '200px'
                    }}>
                        <div className={`kpi-num ${colorClass}`} style={{
                            fontSize: '36px',
                            fontWeight: 700,
                            lineHeight: 1,
                            marginBottom: '4px'
                        }}>
                            {kpi.value}
                        </div>
                        <div className="kpi-label" style={{
                            fontSize: '12px',
                            color: 'var(--text-muted)',
                            marginBottom: '6px',
                            fontWeight: 500
                        }}>
                            {kpi.label}
                        </div>
                        <div className="kpi-detail" style={{ 
                            fontSize: '11px', 
                            color: '#64748b'
                        }}>
                            {kpi.detail || '—'}
                        </div>
                    </div>
                );
            });
        }
        
        // Default KPIs if none are provided
        const colorClasses = ['blue', 'green', 'amber', 'red', 'purple'];
        const defaultLabels = ['Total Tasks', 'Completed', 'In Progress', 'Not Started', 'Total Days'];
        const defaults = ['0', '0', '0', '0', '0'];
        
        return (
            <>
                {colorClasses.map((color, i) => (
                    <div key={i} className="kpi-card" style={{
                        background: 'var(--bg-card)',
                        border: '1px solid var(--border)',
                        borderRadius: '12px',
                        padding: '16px 14px',
                        minWidth: '200px'
                    }}>
                        <div className={`kpi-num ${color}`} style={{
                            fontSize: '36px',
                            fontWeight: 700,
                            lineHeight: 1,
                            marginBottom: '4px'
                        }}>
                            {defaults[i]}
                        </div>
                        <div className="kpi-label" style={{
                            fontSize: '12px',
                            color: 'var(--text-muted)',
                            marginBottom: '6px',
                            fontWeight: 500
                        }}>
                            {defaultLabels[i]}
                        </div>
                        <div className="kpi-detail" style={{ 
                            fontSize: '11px', 
                            color: '#64748b'
                        }}>
                            —
                        </div>
                    </div>
                ))}
            </>
        );
    };

    return (
        <div className="kpi-strip" style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(5, 1fr)',
            gap: '16px',
            padding: '16px 24px',
            background: 'var(--bg-primary)',
            borderBottom: '1px solid var(--border)',
            flexShrink: 0,
            overflowX: 'auto'
        }}>
            {renderKpis()}
        </div>
    );
};

export default KpiStrip;
