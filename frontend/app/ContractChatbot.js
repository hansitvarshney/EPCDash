'use client';

import React, { useState, useRef } from 'react';

const quickPrompts = [
    { label: "🔍 Audit Delay Liabilities", query: "Analyze all clauses regarding project delays, extensions of time (EOT), liquidated damages, and penalty thresholds. What happens if there is a 5-month delay?" },
    { label: "💳 Check Billing Milestones", query: "Summarize the entire payment milestone schedule, mobilization advance conditions, and retention money release clauses." },
    { label: "⚠️ Find Risk Factors", query: "Identify the top 3 highest risk liabilities, force majeure conditions, or termination clauses assigned to us as the contractor." }
];
export default function ContractChatbot({ projectId }) {
    const [uploading, setUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState('');
    const [uploadedFiles, setUploadedFiles] = useState([]); // Tracks multiple doc contexts
    const [messages, setMessages] = useState([
        { role: 'assistant', text: "Hello! Drop any project tender or contract spec file above, and I'll map its connections so you can audit clauses instantly." }
    ]);
    const [input, setInput] = useState('');
    const [loadingAnswer, setLoadingAnswer] = useState(false);
    const fileInputRef = useRef(null);

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploading(true);
        setUploadStatus(`Indexing "${file.name}" into GraphRAG database...`);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/upload`, {
                method: 'POST',
                body: formData,
            });

            const data = await res.json();
            if (res.ok) {
                setUploadStatus(`✅ ${file.name} successfully linked.`);
                
                // Append file to our UI chip array using backend metadata if present
                if (data && data.file_name) {
                    setUploadedFiles(prev => [...prev, { id: data.id, name: data.file_name }]);
                } else {
                    setUploadedFiles(prev => [...prev, { id: Date.now(), name: file.name }]);
                }

                setMessages(prev => [
                    ...prev,
                    { role: 'assistant', text: `Master graph update complete! I have finished analyzing "${file.name}". Go ahead and ask me any structural questions about it.` }
                ]);
            } else {
                setUploadStatus(`❌ Upload Failed: ${data.detail || 'Unknown error'}`);
            }
        } catch (err) {
            setUploadStatus('❌ Connection error to parsing backend.');
        } finally {
            setUploading(false);
        }
    };

    const handleRemoveDocument = async (docId) => {
        try {
            const res = await fetch(`http://localhost:8000/projects/${projectId}/documents/${docId}`, {
                method: 'DELETE',
            });

            if (res.ok) {
                // Instantly filter document context out of the active UI state view
                setUploadedFiles(prev => prev.filter(f => f.id !== docId));
            } else {
                console.error("Backend document removal failed.");
            }
        } catch (err) {
            console.error("Network error during document removal:", err);
        }
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!input.trim() || loadingAnswer) return;

        const userMsg = input.trim();
        setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
        setInput('');
        setLoadingAnswer(true);

        try {
            const res = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: userMsg }),
            });

            const data = await res.json();
            if (res.ok) {
                setMessages(prev => [...prev, { role: 'assistant', text: data.response }]);
            } else {
                setMessages(prev => [...prev, { role: 'assistant', text: '❌ Error: Failed to fetch query evaluation.' }]);
            }
        } catch (err) {
            setMessages(prev => [...prev, { role: 'assistant', text: '❌ Network context connection broken.' }]);
        } finally {
            setLoadingAnswer(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-[#0f172a] text-slate-100 p-4">
            {/* Top Drag & Drop Context Zone */}
            <div 
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-700 hover:border-blue-500 rounded-xl p-6 text-center cursor-pointer transition-colors bg-[#1e293b]/50"
            >
                <input 
                    type="file" 
                    ref={fileInputRef} 
                    onChange={handleFileUpload} 
                    className="hidden" 
                    accept=".pdf,.txt,.docx,.md"
                />
                <h3 className="font-semibold text-slate-200">Drag & drop or click to upload contract / spec file</h3>
                <p className="text-xs text-slate-400 mt-1">Accepts PDF, TXT, DOCX, MD</p>
                
                {uploadStatus && (
                    <p className="text-xs font-bold mt-3 text-blue-400 tracking-wide">{uploadStatus}</p>
                )}

                {/* Interactive Document Removal Chips */}
                {uploadedFiles.length > 0 && (
                    <div className="flex flex-wrap gap-2 justify-center mt-4" onClick={(e) => e.stopPropagation()}>
                        {uploadedFiles.map((f) => (
                            <div key={f.id} className="flex items-center gap-2 bg-slate-800 text-slate-200 border border-slate-700 rounded-full px-3 py-1 text-xs shadow-md">
                                <span>{f.name}</span>
                                <button 
                                    onClick={() => handleRemoveDocument(f.id)} 
                                    className="text-slate-400 hover:text-red-400 transition-colors ml-1 font-bold text-sm focus:outline-none"
                                    title="Remove document framework context"
                                >
                                    ×
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Chat Stream View Interface */}
            <div className="flex-1 overflow-y-auto my-4 p-4 space-y-4 bg-[#161e2f]/40 rounded-xl border border-slate-800/60">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] rounded-lg px-4 py-2.5 text-sm leading-relaxed shadow-sm ${
                            msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-100 whitespace-pre-wrap'
                        }`}>
                            {msg.text}
                        </div>
                    </div>
                ))}
                {loadingAnswer && (
                    <div className="flex justify-start">
                        <div className="bg-slate-800 text-slate-400 rounded-lg px-4 py-2.5 text-sm animate-pulse">
                            Thinking and analyzing knowledge graph connections...
                        </div>
                    </div>
                )}
            </div>

            {/* Input Submission Bar */}
            
        {/* Quick Audit Shortcuts for Easy Navigation */}
<div className="flex flex-wrap gap-2 mb-3">
    {quickPrompts.map((btn, idx) => (
        <button
            key={idx}
            type="button"
            disabled={loadingAnswer}
            onClick={async () => {
                // Set the input field text and automatically submit it
                setInput(btn.query);
                // Trigger the message append and backend call instantly
                setMessages(prev => [...prev, { role: 'user', text: btn.label }]);
                setLoadingAnswer(true);
                try {
                    const res = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/chat`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ question: btn.query }),
                    });
                    const data = await res.json();
                    if (res.ok) {
                        setMessages(prev => [...prev, { role: 'assistant', text: data.response }]);
                    } else {
                        setMessages(prev => [...prev, { role: 'assistant', text: '❌ Error evaluating clause.' }]);
                    }
                } catch (err) {
                    setMessages(prev => [...prev, { role: 'assistant', text: '❌ Connection error.' }]);
                } finally {
                    setLoadingAnswer(false);
                    setInput('');
                }
            }}
            className="bg-slate-800 hover:bg-blue-900/60 text-slate-300 hover:text-blue-400 border border-slate-700 hover:border-blue-500 rounded-lg px-3 py-1.5 text-xs font-medium transition-all"
        >
            {btn.label}
        </button>
    ))}
</div>    
            
            <form onSubmit={handleSendMessage} className="flex gap-2">
                <input 
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask about liabilities, penalty thresholds, transformer models..."
                    className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                />
                <button 
                    type="submit" 
                    disabled={loadingAnswer || !input.trim()}
                    className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-medium px-5 py-2 rounded-lg text-sm transition-colors"
                >
                    Query
                </button>
            </form>
        </div>
    );
}