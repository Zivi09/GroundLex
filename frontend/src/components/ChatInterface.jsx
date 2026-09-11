import React, { useState, useRef, useEffect } from 'react';
import { ShieldAlert, Sparkles, Plus, ChevronRight, Layers, Paperclip, ArrowRight, CheckCircle2, ChevronDown, Check, Edit2, FileText, Image as ImageIcon, ExternalLink, X } from 'lucide-react';
import ChunkViewerModal from './ChunkViewerModal';

export default function ChatInterface({
  hasDocuments,
  documents = [],
  onSampleClick,
  onCitationsUpdate,
  health,
  onUploadSuccess,
  conversationId,
  conversationTitle,
  initialMessages,
  onTitleUpdate,
  onConversationChange
}) {
  const [messages, setMessages] = useState(initialMessages || []);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [attachedDoc, setAttachedDoc] = useState(null);
  const [activeTab, setActiveTab] = useState('answer');
  const [showModelMenu, setShowModelMenu] = useState(false);
  const [activeConvId, setActiveConvId] = useState(conversationId || null);
  const [selectedChunkModal, setSelectedChunkModal] = useState(null);

  const fileInputRef = useRef(null);
  const titleInputRef = useRef(null);
  const chatEndRef = useRef(null);

  // Inline Title Editing state
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [titleText, setTitleText] = useState(conversationTitle || "What are the main differences between RAG and fine-tuning for legal AI?");

  useEffect(() => {
    if (isEditingTitle && titleInputRef.current) {
      titleInputRef.current.focus();
    }
  }, [isEditingTitle]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const modelOptions = [
    { label: 'Auto (Smart LLM Router)', provider: 'auto', model_name: 'auto', desc: 'Auto-detect active API key' },
    { label: 'Groq LPU (Fastest)', provider: 'groq', model_name: 'openai/gpt-oss-120b', desc: 'Groq Ultra-Fast LPU' },
    { label: 'Sonar Pro', provider: 'openai', model_name: 'gpt-4o-mini', desc: 'OpenAI Grounded RAG' },
    { label: 'Google Gemini 2.0', provider: 'gemini', model_name: 'gemini-2.0-flash', desc: 'Google Multimodal' },
    { label: 'DeepSeek V3 / R1', provider: 'deepseek', model_name: 'deepseek-chat', desc: 'DeepSeek Reasoning' },
    { label: 'Anthropic Claude 3.5', provider: 'anthropic', model_name: 'claude-3-5-sonnet-20241022', desc: 'Precision Legal Analysis' },
    { label: 'Mistral Large', provider: 'mistral', model_name: 'mistral-large-latest', desc: 'Mistral AI Enterprise' },
    { label: 'OpenRouter Unified', provider: 'openrouter', model_name: 'deepseek/deepseek-r1', desc: '100+ AI Agents Router' },
    { label: 'Together AI LLaMA', provider: 'together', model_name: 'meta-llama/Llama-3.3-70B-Instruct-Turbo', desc: 'Together Open Models' },
    { label: 'Cohere Command R+', provider: 'cohere', model_name: 'command-r-plus', desc: 'Cohere RAG Optimized' },
    { label: 'Ollama LLaMA 3', provider: 'ollama', model_name: 'llama3', desc: 'Offline Local Zero-Key' },
  ];

  const [selectedModel, setSelectedModel] = useState(modelOptions[0]);


  const getDynamicRelatedQuestions = () => {
    if (messages.length === 0) return [];

    const lastUserMsg = [...messages].reverse().find(m => m.sender === 'user')?.text || '';
    const qLower = lastUserMsg.toLowerCase();

    if (qLower.includes('lease') || qLower.includes('rent') || qLower.includes('deposit')) {
      return [
        "What is the monthly rent payment schedule and grace period?",
        "What are the landlord and tenant maintenance obligations?",
        "What are the conditions for security deposit return?",
        "What are the remedies in the event of default?"
      ];
    } else if (qLower.includes('nda') || qLower.includes('confidential')) {
      return [
        "What is the non-disclosure term and duration?",
        "What are the exclusions from confidential information?",
        "What are the remedies for breach of confidentiality?",
        "Which jurisdiction governs this agreement?"
      ];
    } else if (qLower.includes('saas') || qLower.includes('service') || qLower.includes('license')) {
      return [
        "What is the service level agreement (SLA) uptime commitment?",
        "What are the data privacy and security compliance provisions?",
        "What is the limitation of liability cap?",
        "What are the automatic renewal and termination terms?"
      ];
    } else {
      return [
        "What are the termination penalties and notice requirements?",
        "What is the governing law and dispute resolution mechanism?",
        "Are there any indemnification obligations specified?",
        "What is the limitation of liability under this agreement?"
      ];
    }
  };

  const dynamicRelated = getDynamicRelatedQuestions();

  const handleTitleSave = async () => {
    setIsEditingTitle(false);
    if (!titleText.trim()) return;

    if (onTitleUpdate) {
      onTitleUpdate(titleText);
    }

    if (activeConvId) {
      try {
        await fetch(`/api/conversations/${activeConvId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: titleText }),
        });
      } catch (err) {
        console.error("Failed to persist renamed title:", err);
      }
    }
  };

  const handlePaperclipClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert("Only PDF documents are supported for legal ingestion.");
      return;
    }

    setIsUploading(true);
    setUploadStatus({ type: 'info', message: `Uploading & indexing "${file.name}"...` });

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (res.ok) {
        setAttachedDoc(data.filename);
        setUploadStatus({
          type: 'success',
          message: `Indexed "${data.filename}" into ChromaDB vector store (${data.chunks_indexed} clauses)!`
        });
        if (onUploadSuccess) {
          onUploadSuccess();
        }
      } else {
        setUploadStatus({
          type: 'error',
          message: `Upload failed: ${data.detail || 'Could not process PDF.'}`
        });
      }
    } catch (err) {
      setUploadStatus({
        type: 'error',
        message: 'Network error uploading legal PDF document.'
      });
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleSend = async (queryText) => {
    const query = queryText || inputQuery;
    if (!query.trim() || isLoading) return;

    const userMessage = { id: Date.now(), sender: 'user', text: query };
    setMessages(prev => [...prev, userMessage]);
    setInputQuery('');
    setIsLoading(true);

    if (!conversationId && messages.length === 0) {
      setTitleText(query);
    }

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          top_k: 5,
          provider: selectedModel.provider,
          model_name: selectedModel.model_name,
          conversation_id: activeConvId
        }),
      });

      const data = await response.json();

      if (response.ok) {
        const assistantMessage = {
          id: Date.now() + 1,
          sender: 'assistant',
          text: data.answer,
          citations: data.citations,
          refused: data.refused,
          model_name: data.model_name,
          provider: data.llm_provider
        };
        setMessages(prev => [...prev, assistantMessage]);

        if (data.conversation_id && data.conversation_id !== activeConvId) {
          setActiveConvId(data.conversation_id);
          if (onConversationChange) {
            onConversationChange(data.conversation_id);
          }
        }

        if (onCitationsUpdate && data.citations) {
          onCitationsUpdate(data.citations);
        }
      } else {
        const errorMessage = {
          id: Date.now() + 1,
          sender: 'assistant',
          text: `Error: ${data.detail || 'Failed to generate response.'}`,
          citations: [],
          error: true
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'assistant',
        text: 'Network error connecting to RAG backend.',
        citations: [],
        error: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const currentAssistantMsg = [...messages].reverse().find(m => m.sender === 'assistant');
  const activeCitations = currentAssistantMsg?.citations || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, height: '100%' }}>
      {/* Chunk Viewer Modal */}
      {selectedChunkModal && (
        <ChunkViewerModal
          citation={selectedChunkModal}
          onClose={() => setSelectedChunkModal(null)}
        />
      )}

      {/* Hidden File Input */}
      <input
        type="file"
        ref={fileInputRef}
        accept=".pdf"
        style={{ display: 'none' }}
        onChange={handleFileUpload}
      />

      {/* Upload Banner */}
      {uploadStatus && (
        <div style={{
          background: uploadStatus.type === 'error' ? '#fff1f2' : uploadStatus.type === 'success' ? '#f0fdf4' : 'var(--brand-rose-tint)',
          border: `1px solid ${uploadStatus.type === 'error' ? '#fecdd3' : uploadStatus.type === 'success' ? '#bbf7d0' : 'var(--border-active-card)'}`,
          color: uploadStatus.type === 'error' ? '#e11d48' : uploadStatus.type === 'success' ? '#15803d' : 'var(--brand-rose)',
          padding: '10px 16px',
          borderRadius: 'var(--radius-card)',
          fontSize: '0.85rem',
          marginBottom: '16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: 'var(--shadow-soft)'
        }}>
          <span>{uploadStatus.message}</span>
          <button
            onClick={() => setUploadStatus(null)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', fontWeight: 'bold' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Answer Eyebrow */}
      <div className="answer-eyebrow">
        <Sparkles size={14} className="eyebrow-icon" />
        <span>ANSWER</span>
      </div>

      {/* Editable Conversation Title Heading */}
      <div style={{ marginBottom: '20px', position: 'relative' }}>
        {isEditingTitle ? (
          <input
            ref={titleInputRef}
            type="text"
            value={titleText}
            onChange={(e) => setTitleText(e.target.value)}
            onBlur={handleTitleSave}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleTitleSave();
            }}
            style={{
              width: '100%',
              fontSize: '1.75rem',
              fontFamily: 'var(--font-heading)',
              fontWeight: 700,
              color: 'var(--text-ink)',
              border: 'none',
              borderBottom: '2px solid var(--brand-rose)',
              outline: 'none',
              background: 'transparent',
              padding: '2px 0'
            }}
          />
        ) : (
          <h1
            className="question-heading"
            onClick={() => setIsEditingTitle(true)}
            title="Click to rename conversation title"
            style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '10px' }}
          >
            <span>{titleText}</span>
            <Edit2 size={16} style={{ color: 'var(--text-meta)', opacity: 0.5 }} />
          </h1>
        )}
      </div>

      {/* Tab Strip */}
      <div className="tab-strip">
        <button
          className={`tab-btn ${activeTab === 'answer' ? 'active' : ''}`}
          onClick={() => setActiveTab('answer')}
        >
          Answer
        </button>
        <button
          className={`tab-btn ${activeTab === 'sources' ? 'active' : ''}`}
          onClick={() => setActiveTab('sources')}
        >
          Sources <span className="tab-count">{activeCitations.length}</span>
        </button>
        <button
          className={`tab-btn ${activeTab === 'images' ? 'active' : ''}`}
          onClick={() => setActiveTab('images')}
        >
          Images
        </button>
      </div>

      {/* TAB CONTENT 1: Answer View */}
      {activeTab === 'answer' && (
        <>
          {/* Horizontal Source Chip Strip (De-duplicated by Document) */}
          {activeCitations.length > 0 && (() => {
            const uniqueDocSources = [];
            const seenDocs = new Set();
            activeCitations.forEach(c => {
              if (!seenDocs.has(c.doc_name)) {
                seenDocs.add(c.doc_name);
                const pages = activeCitations
                  .filter(x => x.doc_name === c.doc_name)
                  .map(x => x.page_number)
                  .sort((a, b) => a - b);
                uniqueDocSources.push({
                  doc_name: c.doc_name,
                  pages: Array.from(new Set(pages)),
                  firstCitation: c
                });
              }
            });

            return (
              <div className="source-chip-strip">
                {uniqueDocSources.map((ds, idx) => (
                  <div
                    key={idx}
                    className="source-chip"
                    onClick={() => setSelectedChunkModal(ds.firstCitation)}
                    title={`Click to view citations from ${ds.doc_name}`}
                  >
                    <span className="chip-favicon" style={{ background: 'var(--brand-rose-tint)', color: 'var(--brand-rose)', fontSize: '0.62rem', fontWeight: 700 }}>
                      PDF
                    </span>
                    <span className="chip-domain">{ds.doc_name}</span>
                    <span className="chip-num" style={{ background: 'var(--bg-subtle)', color: 'var(--text-meta)', fontWeight: 600, padding: '2px 6px', borderRadius: '8px', fontSize: '0.72rem' }}>
                      Pages {ds.pages.join(', ')}
                    </span>
                  </div>
                ))}
              </div>
            );
          })()}

          {/* Synthesized Answer Content */}
          <div>
            {messages.length === 0 && !isLoading ? (
              <div style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-hairline)',
                borderRadius: 'var(--radius-card)',
                padding: '32px 24px',
                textAlign: 'center',
                marginBottom: '24px',
                boxShadow: 'var(--shadow-soft)'
              }}>
                <Sparkles size={28} style={{ color: 'var(--brand-rose)', marginBottom: '12px' }} />
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700, fontFamily: 'var(--font-heading)', color: 'var(--text-ink)', marginBottom: '8px' }}>
                  Grounded Legal Document Assistant
                </h2>
                <p style={{ fontSize: '0.88rem', color: 'var(--text-meta)', maxWidth: '480px', margin: '0 auto 16px auto', lineHeight: 1.5 }}>
                  Ask a question about your uploaded contracts or statutory legal PDFs. Every answer is grounded with verifiable document and page citations.
                </p>
                {!hasDocuments && (
                  <button
                    onClick={onSampleClick}
                    style={{
                      background: 'var(--brand-rose-tint)',
                      border: '1px solid var(--border-active-card)',
                      color: 'var(--brand-rose)',
                      padding: '8px 16px',
                      borderRadius: 'var(--radius-chip)',
                      fontSize: '0.82rem',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    Load Demo Legal Sample Documents
                  </button>
                )}
              </div>
            ) : (
              messages.map((msg, index) => {
                if (msg.sender === 'user') {
                  return (
                    <div key={msg.id || index} style={{
                      background: 'var(--bg-subtle)',
                      border: '1px solid var(--border-hairline)',
                      borderRadius: 'var(--radius-card)',
                      padding: '12px 18px',
                      fontSize: '0.95rem',
                      fontWeight: 600,
                      color: 'var(--text-ink)',
                      marginBottom: '16px'
                    }}>
                      💬 {msg.text}
                    </div>
                  );
                } else {
                  return (
                    <div key={msg.id || index} style={{ marginBottom: '24px' }}>
                      {msg.refused && (!msg.citations || msg.citations.length === 0) && (
                        <div style={{
                          background: 'var(--brand-rose-tint)',
                          border: '1px solid var(--border-active-card)',
                          color: 'var(--brand-rose)',
                          padding: '12px 18px',
                          borderRadius: 'var(--radius-card)',
                          fontSize: '0.88rem',
                          marginBottom: '16px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '10px'
                        }}>
                          <ShieldAlert size={18} />
                          <span>
                            <strong>Grounded Refusal:</strong> The provided legal documents do not contain explicit context to answer this query.
                          </span>
                        </div>
                      )}
                      <div className="answer-paragraph" style={{ whiteSpace: 'pre-wrap' }}>
                        {msg.text}
                        {msg.citations?.map((c, i) => (
                          <sup
                            key={i}
                            className="inline-cite"
                            onClick={() => setSelectedChunkModal(c)}
                            title={`Click to view chunk from ${c.doc_name} (Page ${c.page_number})`}
                          >
                            [{i + 1}]
                          </sup>
                        ))}
                      </div>
                    </div>
                  );
                }
              })
            )}
          </div>

          {isLoading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '16px 0', color: 'var(--text-meta)', fontSize: '0.85rem' }}>
              <Sparkles size={16} className="spin" style={{ color: 'var(--brand-rose)' }} />
              <span>Synthesizing grounded answer using {selectedModel.label}...</span>
            </div>
          )}

          {/* RELATED Block — Rendered as a clean 2-column grid */}
          {messages.length > 0 && dynamicRelated.length > 0 && (
            <div className="related-section" style={{ marginTop: '24px' }}>
              <div className="related-title-box" style={{ marginBottom: '10px' }}>
                <Layers size={14} />
                <span>RELATED FOLLOW-UP QUESTIONS</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '8px' }}>
                {dynamicRelated.map((rq, idx) => (
                  <div
                    key={idx}
                    className="related-card"
                    onClick={() => {
                      setInputQuery(rq);
                      handleSend(rq);
                    }}
                    style={{ padding: '10px 14px', borderRadius: '12px', background: '#fff', border: '1px solid var(--border-hairline)', cursor: 'pointer' }}
                  >
                    <div className="left-box" style={{ gap: '8px', overflow: 'hidden' }}>
                      <Plus size={14} className="plus-icon" style={{ flexShrink: 0 }} />
                      <span style={{ fontSize: '0.83rem', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{rq}</span>
                    </div>
                    <ChevronRight size={14} className="arrow-icon" style={{ flexShrink: 0 }} />
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* TAB CONTENT 2: Sources View */}
      {activeTab === 'sources' && (
        <div style={{ flex: 1, padding: '8px 0' }}>
          <div style={{ marginBottom: '16px' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-ink)', fontFamily: 'var(--font-heading)' }}>
              Cited Source Documents ({activeCitations.length})
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-meta)' }}>
              Grounded legal document context supporting the active response.
            </p>
          </div>

          {activeCitations.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {activeCitations.map((cit, idx) => {
                const isPdf = cit.doc_name.toLowerCase().endsWith('.pdf');
                return (
                  <div
                    key={idx}
                    className={`source-card ${idx === 0 ? 'active' : ''}`}
                    onClick={() => setSelectedChunkModal(cit)}
                    style={{ padding: '16px', borderRadius: '16px', cursor: 'pointer' }}
                  >
                    <div className="source-card-meta">
                      <div className="source-domain-wrapper">
                        <div className="source-icon-badge" style={{ background: isPdf ? 'var(--brand-rose-tint)' : '#f1f5f9', color: isPdf ? 'var(--brand-rose)' : 'var(--text-ink)' }}>
                          {isPdf ? 'PDF' : cit.doc_name.charAt(0).toUpperCase()}
                        </div>
                        <span className="source-domain-tag">
                          {isPdf ? cit.doc_name : cit.doc_name.toUpperCase()}
                        </span>
                      </div>
                      <div className="source-num-circle">{idx + 1}</div>
                    </div>

                    <div className="source-card-title" style={{ marginTop: '8px', fontSize: '0.92rem' }}>
                      {cit.doc_name} — {isPdf ? `Clause (Page ${cit.page_number})` : 'Source Citation'}
                    </div>

                    <div className="source-card-snippet" style={{ marginTop: '6px', fontSize: '0.82rem', webkitLineClamp: 3 }}>
                      {cit.snippet}
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px', fontSize: '0.75rem', color: 'var(--brand-rose)', fontWeight: 600 }}>
                      <span>Click to view full clause text</span>
                      <ExternalLink size={14} />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ padding: '32px 16px', textAlign: 'center', background: '#fff', borderRadius: '16px', border: '1px solid var(--border-hairline)' }}>
              <FileText size={28} style={{ color: 'var(--text-meta)', opacity: 0.4, marginBottom: '8px' }} />
              <p style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-ink)' }}>No citations available yet.</p>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-meta)', marginTop: '4px' }}>Ask a question about your indexed legal documents to generate grounded source citations.</p>
            </div>
          )}
        </div>
      )}

      {/* TAB CONTENT 3: Images View */}
      {activeTab === 'images' && (
        <div style={{ flex: 1, padding: '24px 0', textAlign: 'center' }}>
          <div style={{
            background: '#ffffff',
            border: '1px solid var(--border-hairline)',
            borderRadius: '20px',
            padding: '40px 24px',
            boxShadow: 'var(--shadow-soft)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px'
          }}>
            <ImageIcon size={36} style={{ color: 'var(--text-meta)', opacity: 0.4 }} />
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-ink)', fontFamily: 'var(--font-heading)' }}>
              No Diagram Images Extracted
            </h3>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-meta)', maxWidth: '420px', lineHeight: 1.5 }}>
              The currently retrieved legal contract clauses and reference sources do not contain embedded diagram figures or visual charts.
            </p>
          </div>
        </div>
      )}

      <div ref={chatEndRef} />

      {/* Ask a follow-up Floating Composer Card */}
      <div className="floating-composer-card">
        {/* Active Attached Document Context Badge */}
        {(attachedDoc || (documents && documents.length > 0)) && (
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 10px',
            background: 'rgba(239, 68, 68, 0.08)',
            border: '1px solid rgba(239, 68, 68, 0.2)',
            borderRadius: '12px',
            fontSize: '0.78rem',
            fontWeight: 600,
            color: 'var(--brand-rose)',
            marginBottom: '10px',
            width: 'fit-content'
          }}>
            <FileText size={14} />
            <span>
              Attached Context: <strong>{attachedDoc || documents[documents.length - 1]?.doc_name}</strong>
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-meta)', marginLeft: '4px' }}>
              ({documents.find(d => d.doc_name === (attachedDoc || documents[documents.length - 1]?.doc_name))?.chunk_count || 1} clauses indexed)
            </span>
            {attachedDoc && (
              <button
                onClick={() => setAttachedDoc(null)}
                title="Clear attachment focus"
                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, marginLeft: '4px', display: 'flex', alignItems: 'center', color: 'var(--brand-rose)' }}
              >
                <X size={12} />
              </button>
            )}
          </div>
        )}

        <textarea
          className="composer-textarea"
          rows={2}
          placeholder="Ask a follow-up..."
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          disabled={isLoading || isUploading}
        />

        <div className="composer-controls">
          <div className="composer-controls-left">
            <button
              type="button"
              className="paperclip-btn"
              onClick={handlePaperclipClick}
              disabled={isUploading}
              title="Attach & index legal PDF document"
              style={{ background: 'none', border: 'none', display: 'flex', alignItems: 'center' }}
            >
              <Paperclip size={18} style={{ color: isUploading ? 'var(--brand-rose)' : 'var(--text-meta)' }} />
            </button>

            {/* Model Selector Dropdown Pill */}
            <div
              className="model-selector-pill"
              onClick={() => setShowModelMenu(!showModelMenu)}
              title="Click to change active LLM provider"
            >
              <div className="rose-dot" />
              <span>{selectedModel.label}</span>
              <ChevronDown size={14} style={{ color: 'var(--text-meta)' }} />

              {/* Floating Dropdown Menu */}
              {showModelMenu && (
                <div className="model-dropdown-menu" onClick={(e) => e.stopPropagation()}>
                  {modelOptions.map((option, idx) => (
                    <div
                      key={idx}
                      className={`model-option-item ${selectedModel.provider === option.provider ? 'selected' : ''}`}
                      onClick={() => {
                        setSelectedModel(option);
                        setShowModelMenu(false);
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 600 }}>{option.label}</div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-meta)' }}>{option.desc}</div>
                      </div>
                      {selectedModel.provider === option.provider && (
                        <Check size={14} style={{ color: 'var(--brand-rose)' }} />
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <button
            className="send-circle-btn"
            onClick={() => handleSend()}
            disabled={isLoading || isUploading || !inputQuery.trim()}
            title="Send query"
          >
            <ArrowRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
