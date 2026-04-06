import React from 'react';

const FileList = ({ files, activeFile, onSelectFile }) => {
    const handleUploadMore = () => {
        // This is a simple implementation. A more robust solution might involve a modal or a different view.
        window.location.reload(); 
    };

    return (
        <div className="file-list-container">
            {files.map(file => (
                <div 
                    key={file.name} 
                    className={`file-item ${file.name === activeFile ? 'active' : ''}`}
                    onClick={() => onSelectFile(file.name)}
                >
                    <div className="fname">{file.name}</div>
                    <div className="fmeta">{file.rows} rows · {file.columns.length} columns</div>
                </div>
            ))}
            <button className="upload-more-btn" onClick={handleUploadMore}>
                Upload More Files
            </button>
        </div>
    );
};

export default FileList;
