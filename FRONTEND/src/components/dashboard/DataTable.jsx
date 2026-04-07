import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';

const API = 'http://localhost:8000/api';

const DataTable = ({ activeDataset }) => {
  const [rows, setRows] = useState([]);
  const [columns, setColumns] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef(null);

  const fetchData = useCallback(async (searchTerm = '') => {
    if (!activeDataset) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/files/${encodeURIComponent(activeDataset)}/filter`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filters: {}, limit: 100 }),
      });

      if (!res.ok) return;
      const data = await res.json();
      const fetchedRows = data.rows || [];
      setTotal(data.total || 0);

      if (fetchedRows.length > 0) {
        setColumns(Object.keys(fetchedRows[0]));
      }

      if (searchTerm.trim()) {
        const lower = searchTerm.toLowerCase();
        const filtered = fetchedRows.filter(row =>
          Object.values(row).some(v =>
            String(v ?? '').toLowerCase().includes(lower)
          )
        );
        setRows(filtered);
      } else {
        setRows(fetchedRows);
      }
    } catch (err) {
      console.error('DataTable fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [activeDataset]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSearch = (val) => {
    setSearch(val);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchData(val), 300);
  };

  const formatCell = (val) => {
    if (val === null || val === undefined) return '-';
    if (typeof val === 'number') {
      if (Number.isInteger(val)) return val.toLocaleString('en-IN');
      return val.toLocaleString('en-IN', { maximumFractionDigits: 2 });
    }
    return String(val);
  };

  if (!activeDataset) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.1 }}
      style={{ marginTop: 20 }}
    >
      {/* Header + Search */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <h2 style={{
            fontSize: 10,
            fontWeight: 700,
            color: 'rgba(255,255,255,0.4)',
            letterSpacing: 1.5,
            textTransform: 'uppercase',
            margin: 0,
          }}>
            Data Preview
          </h2>
          {total > 0 && (
            <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.25)' }}>
              {total.toLocaleString()} records
            </span>
          )}
        </div>

        <div style={{ position: 'relative' }}>
          <MagnifyingGlassIcon style={{
            position: 'absolute',
            left: 10,
            top: '50%',
            transform: 'translateY(-50%)',
            width: 14,
            height: 14,
            color: 'rgba(255,255,255,0.2)',
          }} />
          <input
            type="text"
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="Search..."
            style={{
              paddingLeft: 32,
              paddingRight: 12,
              paddingTop: 6,
              paddingBottom: 6,
              width: 200,
              fontSize: 12,
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: 8,
              color: 'rgba(255,255,255,0.7)',
              outline: 'none',
            }}
          />
        </div>
      </div>

      {/* Table Container */}
      <div style={{
        background: 'rgba(16,22,50,0.7)',
        border: '1px solid rgba(0,212,255,0.1)',
        borderRadius: 12,
        overflow: 'hidden',
      }}>
        <div style={{ overflowX: 'auto', maxHeight: 380, overflowY: 'auto' }}>
          {loading ? (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '48px 0',
              color: 'rgba(255,255,255,0.3)',
              fontSize: 13,
            }}>
              Loading data...
            </div>
          ) : rows.length === 0 ? (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '48px 0',
              color: 'rgba(255,255,255,0.2)',
              fontSize: 13,
            }}>
              {search ? 'No matching records' : 'No data available'}
            </div>
          ) : (
            <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{
                  background: 'rgba(255,255,255,0.04)',
                  borderBottom: '1px solid rgba(255,255,255,0.06)',
                  position: 'sticky',
                  top: 0,
                  zIndex: 10,
                }}>
                  {columns.map((col) => (
                    <th
                      key={col}
                      style={{
                        padding: '10px 16px',
                        fontSize: 10,
                        fontWeight: 700,
                        color: 'rgba(255,255,255,0.4)',
                        textTransform: 'uppercase',
                        letterSpacing: 1,
                        whiteSpace: 'nowrap',
                        background: 'rgba(16,22,50,0.95)',
                      }}
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, rowIdx) => (
                  <tr
                    key={rowIdx}
                    style={{
                      borderBottom: '1px solid rgba(255,255,255,0.03)',
                      transition: 'background 0.15s',
                    }}
                    onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
                    onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
                  >
                    {columns.map((col) => (
                      <td
                        key={col}
                        style={{
                          padding: '8px 16px',
                          fontSize: 12,
                          color: 'rgba(255,255,255,0.5)',
                          whiteSpace: 'nowrap',
                          maxWidth: 200,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                      >
                        {formatCell(row[col])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default DataTable;
