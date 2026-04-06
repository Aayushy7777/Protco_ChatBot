import React, { useState, useMemo } from 'react';

const ProgressBar = ({ value }) => {
    const numValue = Number(value);
    const percentage = Math.min(Math.max(numValue, 0), 100);
    const color = percentage >= 100 ? '#3fb950' : percentage >= 50 ? '#d29922' : '#30363d';
    const emoji = percentage >= 100 ? '✅' : percentage >= 50 ? '⚙️' : '⏳';
    
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div className="progress-bar" title={`${numValue.toFixed(0)}% progress`}>
                <div 
                    className="progress-fill" 
                    style={{ 
                        width: `${percentage}%`, 
                        backgroundColor: color,
                        transition: 'width 0.3s ease'
                    }}
                ></div>
            </div>
            <span style={{ minWidth: '40px', fontSize: '12px', color: color, fontWeight: '600' }}>
                {emoji} {numValue.toFixed(0)}%
            </span>
        </div>
    );
};

const StatusBadge = ({ value }) => {
    const statusMap = {
        'Completed': { emoji: '✅', bg: '#1a3a24', text: '#3fb950', label: 'Done' },
        'In Progress': { emoji: '⚙️', bg: '#3a2d14', text: '#d29922', label: 'WIP' },
        'Not Started': { emoji: '⏳', bg: '#21262d', text: '#8b949e', label: 'Pending' },
    };
    
    const status = statusMap[value] || statusMap['Not Started'];
    
    return (
        <span 
            className="badge" 
            style={{ 
                backgroundColor: status.bg, 
                color: status.text,
                padding: '4px 10px',
                borderRadius: '20px',
                fontSize: '12px',
                fontWeight: '600',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px'
            }}
            title={value}
        >
            <span>{status.emoji}</span>
            <span>{value}</span>
        </span>
    );
};

const DataTable = ({ data, columns, title }) => {
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'ascending' });

    const sortedData = useMemo(() => {
        let sortableData = [...data];
        if (sortConfig.key) {
            sortableData.sort((a, b) => {
                const aVal = a[sortConfig.key];
                const bVal = b[sortConfig.key];
                
                // Handle numeric comparison
                const aNum = Number(aVal);
                const bNum = Number(bVal);
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return sortConfig.direction === 'ascending' ? aNum - bNum : bNum - aNum;
                }
                
                // Handle string comparison
                if (aVal < bVal) return sortConfig.direction === 'ascending' ? -1 : 1;
                if (aVal > bVal) return sortConfig.direction === 'ascending' ? 1 : -1;
                return 0;
            });
        }
        return sortableData;
    }, [data, sortConfig]);

    const requestSort = (key) => {
        let direction = 'ascending';
        if (sortConfig.key === key && sortConfig.direction === 'ascending') {
            direction = 'descending';
        }
        setSortConfig({ key, direction });
    };

    const renderCell = (item, column) => {
        const value = item[column];
        
        // Progress/Completion bars
        if ((column.toLowerCase().includes('progress') || column.toLowerCase().includes('completion')) && !isNaN(Number(value))) {
            return <ProgressBar value={value} />;
        }
        
        // Status badges
        if (column.toLowerCase().includes('status') || column.toLowerCase().includes('state')) {
            return <StatusBadge value={value} />;
        }
        
        // Date formatting
        if (column.toLowerCase().includes('date') || column.toLowerCase().includes('start') || column.toLowerCase().includes('end')) {
            try {
                const date = new Date(value);
                if (!isNaN(date.getTime())) {
                    return <span title={value}>📅 {date.toISOString().split('T')[0]}</span>;
                }
            } catch (e) {
                return value;
            }
        }
        
        // Assigned to / Person columns
        if (column.toLowerCase().includes('assigned') || column.toLowerCase().includes('to') || column.toLowerCase().includes('person') || column.toLowerCase().includes('name')) {
            return <span>👤 {value}</span>;
        }
        
        // Default rendering
        return value;
    };

    const getColumnIcon = (col) => {
        const lower = col.toLowerCase();
        if (lower.includes('progress') || lower.includes('completion')) return '📊';
        if (lower.includes('status') || lower.includes('state')) return '🏷️';
        if (lower.includes('date') || lower.includes('time')) return '📅';
        if (lower.includes('assigned') || lower.includes('person') || lower.includes('name')) return '👤';
        if (lower.includes('project')) return '📁';
        if (lower.includes('task')) return '✅';
        return '📌';
    };

    return (
        <div className="table-card">
            <div className="table-header">
                <h3>
                    📋 {title || 'Data'}
                </h3>
                <div className="table-sub">
                    📊 Total: <strong>{data.length}</strong> row{data.length !== 1 ? 's' : ''}
                </div>
            </div>
            <div className="table-scroll">
                <table>
                    <thead>
                        <tr>
                            {columns.map(col => (
                                <th 
                                    key={col} 
                                    onClick={() => requestSort(col)}
                                    style={{ cursor: 'pointer', userSelect: 'none' }}
                                    title={`Click to sort by ${col}`}
                                >
                                    <span style={{ marginRight: '4px' }}>{getColumnIcon(col)}</span>
                                    {col}
                                    <span style={{ marginLeft: '4px', opacity: 0.6 }}>
                                        {sortConfig.key === col ? (sortConfig.direction === 'ascending' ? '▲' : '▼') : ''}
                                    </span>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {sortedData.map((item, index) => (
                            <tr key={index} style={{ transition: 'background-color 0.15s ease' }}>
                                {columns.map(col => (
                                    <td key={col}>
                                        {renderCell(item, col)}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default DataTable;
