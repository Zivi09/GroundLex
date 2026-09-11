import React from 'react';
import { FileText, X, Bookmark, ExternalLink } from 'lucide-react';

export default function ChunkViewerModal({ citation, onClose }) {
  if (!citation) return null;

  const docName = citation.doc_name || 'Legal Document';
  const pageNum = citation.page_number || 1;
  const score = citation.score ? (citation.score * 100).toFixed(1) + '%' : 'High';

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(20, 22, 27, 0.4)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px'
    }} onClick={onClose}>
      <div style={{
        background: '#ffffff',
        border: '1px solid var(--border-hairline)',
        borderRadius: '20px',
        maxWidth: '620px',
        width: '100%',
        boxShadow: '0 20px 40px rgba(0,0,0,0.12)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        maxHeight: '85vh'
      }} onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div style={{
          padding: '18px 24px',
          borderBottom: '1px solid var(--border-hairline)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'var(--bg-canvas)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              background: 'var(--brand-rose-tint)',
              color: 'var(--brand-rose)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <FileText size={16} />
            </div>
            <div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-ink)', fontFamily: 'var(--font-heading)' }}>
                {docName}
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-meta)', fontFamily: 'var(--font-mono)' }}>
                Cited Context • Page {pageNum} • Relevance {score}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-meta)',
              padding: '4px',
              borderRadius: '6px'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '24px', overflowY: 'auto', flex: 1, fontSize: '0.92rem', lineHeight: 1.7, color: 'var(--text-ink)' }}>
          <div style={{
            background: 'var(--bg-canvas)',
            border: '1px solid var(--border-hairline)',
            borderRadius: '12px',
            padding: '16px 20px',
            fontFamily: 'var(--font-body)',
            whiteSpace: 'pre-wrap'
          }}>
            {citation.snippet || citation.text || 'No chunk text available.'}
          </div>
        </div>

        {/* Modal Footer */}
        <div style={{
          padding: '14px 24px',
          borderTop: '1px solid var(--border-hairline)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: '#ffffff'
        }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-meta)', fontFamily: 'var(--font-mono)' }}>
            Strict Grounded Context Clause
          </span>
          <button
            onClick={onClose}
            style={{
              background: 'var(--brand-rose)',
              color: '#ffffff',
              border: 'none',
              padding: '6px 16px',
              borderRadius: 'var(--radius-chip)',
              fontSize: '0.82rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Close Viewer
          </button>
        </div>
      </div>
    </div>
  );
}
