import React, { useState, useRef } from 'react';
import { UploadCloud, FileCheck, Sparkles, Loader2, AlertCircle } from 'lucide-react';

export default function DocumentUpload({ onUploadSuccess, onLoadSamples, isLoadingSamples }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = async (file) => {
    if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
      setStatusMessage({ type: 'error', text: 'Please select a valid PDF document.' });
      return;
    }

    setIsUploading(true);
    setStatusMessage(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setStatusMessage({
          type: 'success',
          text: `Indexed "${file.name}" (${data.chunks_indexed} clauses)`
        });
        if (onUploadSuccess) onUploadSuccess();
      } else {
        setStatusMessage({ type: 'error', text: data.detail || 'Failed to process document.' });
      }
    } catch (err) {
      setStatusMessage({ type: 'error', text: 'Network error uploading document.' });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  return (
    <div style={{ marginBottom: '16px' }}>
      <div className="section-header">
        <h3 className="section-title">Ingest Legal PDF</h3>
      </div>

      <div
        className={`upload-zone ${isDragging ? 'active' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
          accept=".pdf"
          style={{ display: 'none' }}
        />

        {isUploading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
            <Loader2 className="upload-icon" style={{ animation: 'spin 1s linear infinite' }} />
            <p className="upload-text">Extracting & Chunking Legal Clauses...</p>
          </div>
        ) : (
          <>
            <UploadCloud className="upload-icon" />
            <p className="upload-text">Drop contract or court opinion PDF here</p>
            <p className="upload-subtext">Click to browse (.pdf format)</p>
          </>
        )}
      </div>

      {statusMessage && (
        <div style={{
          marginTop: '8px',
          padding: '8px 12px',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.78rem',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          background: statusMessage.type === 'success' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
          color: statusMessage.type === 'success' ? 'var(--accent-emerald)' : '#f87171',
          border: `1px solid ${statusMessage.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
        }}>
          {statusMessage.type === 'success' ? <FileCheck size={14} /> : <AlertCircle size={14} />}
          <span>{statusMessage.text}</span>
        </div>
      )}

      <button
        className="btn-sample"
        onClick={onLoadSamples}
        disabled={isLoadingSamples || isUploading}
      >
        {isLoadingSamples ? (
          <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
        ) : (
          <Sparkles size={16} />
        )}
        <span>Load Sample Legal Documents</span>
      </button>
    </div>
  );
}
