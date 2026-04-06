import React from 'react';
import {
    ResponsiveContainer, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Bar,
    LineChart, Line, AreaChart, Area, PieChart, Pie, Cell, ScatterChart, Scatter
} from 'recharts';

const COLORS = ['#58a6ff', '#3fb950', '#bc8cff', '#d29922', '#f85149', '#2da44e', '#8250df'];

const ChartCard = ({ chart }) => {
    if (!chart || !chart.data || chart.data.length === 0) {
        return (
            <div className="chart-card">
                <div className="chart-title">No data available</div>
                <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#8b949e' }}>
                    Select a different chart or file.
                </div>
            </div>
        );
    }

    const { chart_type, title, insight, data, x_key, y_key, color } = chart;

    const renderChart = () => {
        switch (chart_type) {
            case 'bar':
                return (
                    <BarChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                        <XAxis dataKey={x_key} tick={{ fill: '#8b949e', fontSize: 11 }} />
                        <YAxis tick={{ fill: '#8b949e', fontSize: 11 }} />
                        <Tooltip contentStyle={{ backgroundColor: '#161b22', border: '1px solid #30363d' }} />
                        <Bar dataKey={y_key} fill={color || '#58a6ff'} />
                    </BarChart>
                );
            case 'horizontal_bar':
                return (
                    <BarChart data={data} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                        <XAxis type="number" tick={{ fill: '#8b949e', fontSize: 11 }} />
                        <YAxis dataKey={x_key} type="category" tick={{ fill: '#8b949e', fontSize: 11 }} width={80} />
                        <Tooltip contentStyle={{ backgroundColor: '#161b22', border: '1px solid #30363d' }} />
                        <Bar dataKey={y_key} fill={color || '#3fb950'} />
                    </BarChart>
                );
            case 'line':
                return (
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                        <XAxis dataKey={x_key} tick={{ fill: '#8b949e', fontSize: 11 }} />
                        <YAxis tick={{ fill: '#8b949e', fontSize: 11 }} />
                        <Tooltip contentStyle={{ backgroundColor: '#161b22', border: '1px solid #30363d' }} />
                        <Line type="monotone" dataKey={y_key} stroke={color || '#3fb950'} strokeWidth={2} dot={false} />
                    </LineChart>
                );
            case 'area':
                return (
                    <AreaChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                        <XAxis dataKey={x_key} tick={{ fill: '#8b949e', fontSize: 11 }} />
                        <YAxis tick={{ fill: '#8b949e', fontSize: 11 }} />
                        <Tooltip contentStyle={{ backgroundColor: '#161b22', border: '1px solid #30363d' }} />
                        <Area type="monotone" dataKey={y_key} stroke={color || '#58a6ff'} fill={color || '#58a6ff'} fillOpacity={0.15} />
                    </AreaChart>
                );
            case 'pie':
                return (
                    <PieChart>
                        <Pie data={data} dataKey={y_key} nameKey={x_key} cx="50%" cy="50%" outerRadius={60} label>
                            {data.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: '#161b22', border: '1px solid #30363d' }} />
                        <Legend wrapperStyle={{fontSize: "11px"}}/>
                    </PieChart>
                );
            case 'scatter':
                 return (
                    <ScatterChart>
                        <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                        <XAxis type="number" dataKey={x_key} name={x_key} tick={{ fill: '#8b949e', fontSize: 11 }} />
                        <YAxis type="number" dataKey={y_key} name={y_key} tick={{ fill: '#8b949e', fontSize: 11 }} />
                        <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#161b22', border: '1px solid #30363d' }} />
                        <Scatter name="Data points" data={data} fill={color || '#d29922'}/>
                    </ScatterChart>
                );
            default:
                return <p>Unsupported chart type: {chart_type}</p>;
        }
    };

    return (
        <div className="chart-card">
            <div className="chart-title">{title}</div>
            <div className="chart-insight">{insight}</div>
            <ResponsiveContainer width="100%" height={200}>
                {renderChart()}
            </ResponsiveContainer>
        </div>
    );
};

export default ChartCard;
