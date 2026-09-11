import React from 'react';
import { FileText, Bookmark } from 'lucide-react';

export default function DocumentList({ documents, isLoading }) {
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{
        fontFamily: 'var(--font-heading)',
        fontSize: '0.85rem',
        fontWeight: 700,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        color: 'var(--text-meta)',
        marginBottom: '14px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
      }}>
        <span>Active Index Registry ({documents.length})</span>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', paddingRight: '2px' }}>
        {documents.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '24px 12px',
            color: 'var(--text-meta)',
            fontSize: '0.85rem',
            border: '1px dashed var(--border-hairline)',
            borderRadius: 'var(--radius-card)',
            background: 'var(--bg-canvas)'
          }}>
            <FileText size={24} style={{ opacity: 0.3, marginBottom: '8px' }} />
            <p style={{ fontWeight: 500 }}>No documents indexed yet.</p>
            <p style={{ fontSize: '0.75rem', marginTop: '4px' }}>Upload a PDF or click "Load Sample Legal Documents".</p>
          </div>
        ) : (
          documents.map((doc, idx) => (
            <div
              key={idx}
              className="source-card"
              style={{
                marginBottom: '10px',
                padding: '12px 14px',
                background: '#ffffff',
                border: '1px solid var(--border-hairline)',
                borderRadius: 'var(--radius-card)',
                boxShadow: '0 1px 3px rgba(0,0,0,0.01)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden' }}>
                <div style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '6px',
                  background: 'var(--bg-subtle)',
                  color: 'var(--text-ink)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  textTransform: 'uppercase',
                  flexShrink: 0
                }}>
                  PDF
                </div>
                <div style={{ overflow: 'hidden' }}>
                  <p style={{
                    fontSize: '0.86rem',
                    fontWeight: 600,
                    color: 'var(--text-ink)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }} title={doc.doc_name}>
                    {doc.doc_name}
                  </p>
                  <p style={{ fontSize: '0.74rem', color: 'var(--text-meta)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                    {doc.total_pages} {doc.total_pages === 1 ? 'Page' : 'Pages'} • {doc.chunk_count} Clauses
                  </p>
                </div>
              </div>

              <div style={{
                background: '#f0fdf4',
                border: '1px solid #bbf7d0',
                padding: '3px 8px',
                borderRadius: 'var(--radius-chip)',
                fontSize: '0.68rem',
                color: '#15803d',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                flexShrink: 0
              }}>
                <span style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  background: '#22c55e'
                }} />
                Active
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
