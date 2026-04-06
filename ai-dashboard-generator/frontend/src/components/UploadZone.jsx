import React, { useState, useCallback } from 'react';
import { uploadFiles } from '../api';

const UploadZone = ({ onUploadSuccess }) => {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [isDragging, setIsDragging] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);

    const validateFiles = (files) => {
        const validExtensions = ['.csv', '.xlsx', '.xls'];
        const errors = [];
        
        for (let file of files) {
            const extension = '.' + file.name.split('.').pop().toLowerCase();
            if (!validExtensions.includes(extension)) {
                errors.push(`❌ "${file.name}" is not a valid format. Only CSV and Excel files are accepted.`);
            }
            if (file.size > 50 * 1024 * 1024) {
                errors.push(`❌ "${file.name}" is too large (max 50MB).`);
            }
        }
        return errors;
    };

    const handleFiles = useCallback(async (acceptedFiles) => {
        const validationErrors = validateFiles(acceptedFiles);
        if (validationErrors.length > 0) {
            setError(validationErrors.join('\n'));
            return;
        }

        setIsLoading(true);
        setUploadProgress(0);
        setError('');

        try {
            console.log(`📁 Uploading ${acceptedFiles.length} file(s)...`);
            setUploadProgress(30);
            
            const result = await uploadFiles(Array.from(acceptedFiles));
            setUploadProgress(70);
            
            if (result.success && result.files.length > 0) {
                console.log(`✅ Successfully uploaded ${result.files.length} file(s)`, result.files);
                setUploadProgress(100);
                setTimeout(() => {
                    onUploadSuccess(result.files);
                }, 300);
            } else {
                const errorMsg = result.errors.length > 0 
                    ? result.errors.map(e => `❌ ${e}`).join('\n')
                    : '❌ Upload failed. Please try again.';
                setError(errorMsg);
                setUploadProgress(0);
                console.error('Upload failed:', result.errors);
            }
        } catch (err) {
            const errorMsg = err.message || 'An error occurred during upload. Make sure the backend is running.';
            setError(`❌ ${errorMsg}`);
            setUploadProgress(0);
            console.error('Upload error:', err);
        } finally {
            setIsLoading(false);
        }
    }, [onUploadSuccess]);

    const onDragEnter = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    };

    const onDragLeave = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    };

    const onDragOver = (e) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const onDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFiles(e.dataTransfer.files);
        }
    };

    const onClick = () => {
        if (!isLoading) {
            document.getElementById('fileInput').click();
        }
    };

    return (
        <div className="upload-container">
            <div 
                className={`drop-zone ${isDragging ? 'dragging' : ''} ${isLoading ? 'uploading' : ''}`}
                onDragEnter={onDragEnter}
                onDragLeave={onDragLeave}
                onDragOver={onDragOver}
                onDrop={onDrop}
                onClick={onClick}
            >
                <input 
                    type="file" 
                    id="fileInput"
                    multiple
                    accept=".csv,.xlsx,.xls"
                    style={{ display: 'none' }}
                    onChange={(e) => handleFiles(e.target.files)}
                    disabled={isLoading}
                />
                {isLoading ? (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
                        <div className="spinner-large"></div>
                        <p style={{ color: '#58a6ff', fontWeight: '600' }}>📤 Uploading... {uploadProgress}%</p>
                        <div style={{ width: '80%', display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <div className="progress-bar-large" style={{ flex: 1 }}>
                                <div className="progress-fill-large" style={{ width: `${uploadProgress}%` }}></div>
                            </div>
                            <span style={{ minWidth: '40px', fontSize: '12px', color: '#58a6ff', fontWeight: '600' }}>
                                {uploadProgress}%
                            </span>
                        </div>
                    </div>
                ) : (
                    <>
                        <svg className="upload-icon" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="17 8 12 3 7 8"></polyline>
                            <line x1="12" y1="3" x2="12" y2="15"></line>
                        </svg>
                        <h4>📊 Drop files here to upload</h4>
                        <p style={{ marginTop: '8px', fontSize: '13px', color: '#8b949e' }}>
                            Supports CSV and Excel files (max 50MB)
                        </p>
                        <p style={{ marginTop: '4px', fontSize: '12px', color: '#8b949e' }}>
                            or click to browse
                        </p>
                    </>
                )}
            </div>
            {error && (
                <div className="error-message" style={{ 
                    marginTop: '12px', 
                    padding: '12px', 
                    background: '#21262d', 
                    border: '1px solid #f85149',
                    borderRadius: '8px',
                    color: '#f85149',
                    fontSize: '12px',
                    whiteSpace: 'pre-wrap',
                    lineHeight: '1.6'
                }}>
                    {error}
                </div>
            )}
        </div>
    );
};

export default UploadZone;
