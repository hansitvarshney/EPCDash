'use client';

import React, { useState, useRef, useEffect, FormEvent, ChangeEvent } from 'react';

interface ActiveProject {
  id: number;
  name: string;
}

interface ManpowerDeployed {
  cumulative_masons: number;
  cumulative_helpers: number;
  total_man_days: number;
}

interface QuantityExecuted {
  category: string;
  element_id: string;
  total_output: number;
  unit: string;
}

interface AnalyticsData {
  manpower_deployed: ManpowerDeployed;
  quantities_executed: QuantityExecuted[];
  active_log_dates?: string[];
}

interface ChatMessage {
  role: 'user' | 'assistant';
  text: string;
}

export default function Home() {
  const [projects, setProjects] = useState<ActiveProject[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number>(1);
  const [activeTab, setActiveTab] = useState<'analytics' | 'auditor'>('analytics');

  const [analytics, setAnalytics] = useState<AnalyticsData>({
    manpower_deployed: { cumulative_masons: 0, cumulative_helpers: 0, total_man_days: 0 },
    quantities_executed: []
  });

  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadStatus, setUploadStatus] = useState<string>('');
  
  // 📚 Multi-Page Staging UI Array States
  const [queuedSheets, setQueuedSheets] = useState<File[]>([]);
  const [uploadingSheet, setUploadingSheet] = useState<boolean>(false);
  const [sheetUploadStatus, setSheetUploadStatus] = useState<string>('');

  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', text: "Hello! Drop any project tender or contract spec file above, and I'll map its connections so you can audit clauses instantly." }
  ]);
  const [chatInput, setChatInput] = useState<string>('');
  const [loadingAnswer, setLoadingAnswer] = useState<boolean>(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const sheetInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const res = await fetch('http://localhost:8000/projects');
        if (res.ok) {
          const data: ActiveProject[] = await res.json();
          setProjects(data);
          if (data.length > 0) setSelectedProjectId(data[0].id);
        }
      } catch (err) {
        console.log("⚠️ Backend server offline. Using local project workspace memory context.");
        setProjects([{ id: 1, name: "Gurgaon Sector Project Workspace 1" }]);
      }
    };
    fetchProjects();
  }, []);

  const fetchAnalytics = async (projectId: number): Promise<void> => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/analytics/summary/${projectId}`);
      if (res.ok) {
        const data: AnalyticsData = await res.json();
        setAnalytics(data);
      }
    } catch (err) {
      console.log("⚠️ Could not sync active matrix values from localhost:8000.");
    }
  };

  useEffect(() => {
    if (selectedProjectId) {
      fetchAnalytics(selectedProjectId);
    }
  }, [selectedProjectId]);

  const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>): Promise<void> => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadStatus(`Indexing "${file.name}" into local GraphRAG engine...`);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`http://localhost:8000/api/v1/projects/${selectedProjectId}/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        setUploadStatus(`✅ ${file.name} successfully linked.`);
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          text: `Master graph update complete! I have finished analyzing "${file.name}". Ask me any structural questions about it.` 
        }]);
        fetchAnalytics(selectedProjectId);
      } else {
        setUploadStatus(`❌ Upload failed: ${data.detail || 'Unknown error'}`);
      }
    } catch (err) {
      setUploadStatus('❌ Connection error to parsing backend.');
    } finally {
      setUploading(false);
    }
  };

  // 📥 Stage sheets without launching API triggers immediately
  const handleSheetSelection = (e: ChangeEvent<HTMLInputElement>): void => {
    if (e.target.files) {
      const selectedArr = Array.from(e.target.files);
      setQueuedSheets(prev => [...prev, ...selectedArr]);
      setSheetUploadStatus(''); // Clear alert states upon selection
    }
  };

  // ✕ Drop individual image out of the staging array
  const removeQueuedSheet = (indexToRemove: number): void => {
    setQueuedSheets(prev => prev.filter((_, idx) => idx !== indexToRemove));
  };

  // 🚀 Unified multi-file operational logistics transaction handler
  const handleBatchSheetUploadSubmit = async (): Promise<void> => {
    if (queuedSheets.length === 0) return;

    setUploadingSheet(true);
    setSheetUploadStatus(`Processing ${queuedSheets.length} document sheet page(s) concurrently...`);

    const formData = new FormData();
    // Pack all files under the exact field-key array 'files' targeting the backend
    queuedSheets.forEach(file => {
      formData.append('files', file);
    });

    try {
      const res = await fetch(`http://localhost:8000/api/v1/fanout-ingest?project_id=${selectedProjectId}`, {
        method: 'POST',
        body: formData,
      });
      
      const data = await res.json();
      if (res.ok) {
        setSheetUploadStatus(`✅ Success: Parsed all pages into a unified ledger date matrix.`);
        setQueuedSheets([]); // Wipe staging view
        fetchAnalytics(selectedProjectId); // Force dashboard calculation update
      } else {
        setSheetUploadStatus(`❌ Error processing multi-page architecture layout metrics.`);
      }
    } catch (err) {
      setSheetUploadStatus('❌ Unified network server cluster communication fault.');
    } finally {
      setUploadingSheet(false);
    }
  };

  const handleDeleteLog = async (reportDate: string) => {
    if (!confirm(`Are you sure you want to permanently erase the site log for ${reportDate}?`)) return;
    const cleanDate = reportDate.replace(/\//g, "-").trim();
    
    try {
      setSheetUploadStatus(`Purging site data for ${reportDate}...`);
      const res = await fetch(`http://localhost:8000/api/v1/projects/${selectedProjectId}/logs/${encodeURIComponent(cleanDate)}`, {
        method: 'DELETE'
      });
      
      if (res.ok) {
        setSheetUploadStatus(`🗑️ Log for ${reportDate} erased successfully.`);
        fetchAnalytics(selectedProjectId); 
      } else {
        const data = await res.json();
        setSheetUploadStatus(`❌ Purge failed: ${data.detail || 'Unknown error context'}`);
      }
    } catch (err) {
      setSheetUploadStatus('❌ Failed to establish communication network array to deletion API.');
    }
  };

  const handleSendMessage = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    if (!chatInput.trim() || loadingAnswer) return;

    const userMsg = chatInput.trim();
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setChatInput('');
    setLoadingAnswer(true);

    try {
      const res = await fetch(`http://localhost:8000/api/v1/projects/${selectedProjectId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMsg }),
      });
      const data = await res.json();
      if (res.ok) {
        setMessages(prev => [...prev, { role: 'assistant', text: data.response }]);
      } else {
        setMessages(prev => [...prev, { role: 'assistant', text: '⚠️ Error running graph search queries.' }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', text: '❌ Failed to reach the AI cluster backend.' }]);
    } finally {
      setLoadingAnswer(false);
    }
  };

  const processedDates = analytics.active_log_dates && analytics.active_log_dates.length > 0 ? analytics.active_log_dates : [];

  return (
    <main className="min-h-screen bg-[#0B0F19] text-[#E2E8F0] p-6 lg:p-10 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header Display */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between border-b border-slate-800 pb-6 gap-4 bg-[#111827] p-6 rounded-xl border border-slate-800/80 shadow-md">
          <div>
            <h1 className="text-xl lg:text-2xl font-black tracking-tight text-white uppercase">PROJECT EXECUTIVE CONTROL CENTER</h1>
            <p className="text-xs lg:text-sm text-slate-400 font-medium mt-1">EPC Turnkey Construction Dashboard & Document Matrix Hub</p>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <label htmlFor="project-select" className="text-xs font-bold uppercase tracking-wider text-slate-400">Workspace:</label>
              <select
                id="project-select"
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(Number(e.target.value))}
                className="bg-[#1F2937] border border-slate-700 text-white rounded-lg px-3 py-2 text-xs font-semibold focus:outline-hidden focus:border-blue-500 cursor-pointer"
              >
                {projects.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2 bg-emerald-950/40 border border-emerald-800/60 px-3 py-1.5 rounded-lg">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-[10px] font-bold text-emerald-400 tracking-wider uppercase">Live Link Sync</span>
            </div>
          </div>
        </div>

        {/* Tab Selection Row */}
        <div className="flex border-b border-slate-800 gap-2">
          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-5 py-2.5 text-xs font-bold uppercase tracking-wider transition-all rounded-t-lg ${
              activeTab === 'analytics' ? 'bg-[#111827] text-blue-400 border-t-2 border-blue-500 border-x border-slate-800' : 'text-slate-400 hover:text-white'
            }`}
          >
            📊 Operational Yields & Roster
          </button>
          <button
            onClick={() => setActiveTab('auditor')}
            className={`px-5 py-2.5 text-xs font-bold uppercase tracking-wider transition-all rounded-t-lg ${
              activeTab === 'auditor' ? 'bg-[#111827] text-blue-400 border-t-2 border-blue-500 border-x border-slate-800' : 'text-slate-400 hover:text-white'
            }`}
          >
            🤖 Document GraphRAG Assistant
          </button>
        </div>

        {/* Analytics Content Tab */}
        {activeTab === 'analytics' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <div className="bg-[#111827] p-6 rounded-xl border border-slate-800/80 shadow-xs">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Skilled Force Deployed</p>
                <p className="text-3xl font-black text-white mt-2">{analytics.manpower_deployed.cumulative_masons} <span className="text-xs font-normal text-slate-400">Masons</span></p>
              </div>
              <div className="bg-[#111827] p-6 rounded-xl border border-slate-800/80 shadow-xs">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Helper Support Forces</p>
                <p className="text-3xl font-black text-white mt-2">{analytics.manpower_deployed.cumulative_helpers} <span className="text-xs font-normal text-slate-400">Helpers</span></p>
              </div>
              <div className="bg-[#111827] p-6 rounded-xl border border-blue-900/50 shadow-xs bg-linear-to-br from-[#111827] to-[#112240]">
                <p className="text-[10px] font-bold text-blue-400 uppercase tracking-wider">Total Project Labor Force Burn</p>
                <p className="text-3xl font-black text-blue-400 mt-2">{analytics.manpower_deployed.total_man_days} <span className="text-xs font-normal text-blue-300/60">Man-Days</span></p>
              </div>
            </div>

            {/* Upgraded Multi-Page Stage & Trigger Console Block */}
            <div className="bg-[#111827] border border-slate-800 rounded-xl p-6 shadow-lg space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-emerald-950/50 border border-emerald-800/50 rounded-lg text-emerald-400 text-lg">📁</div>
                  <div>
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider">LOGISTICS LEDGER MULTI-SYNC</h3>
                    <p className="text-[11px] text-slate-400 mt-0.5">Select one or multiple consecutive site sheets or snapshots to parse them into a single active site ledger.</p>
                  </div>
                </div>
                <div>
                  <input 
                    type="file" 
                    ref={sheetInputRef} 
                    onChange={handleSheetSelection} 
                    className="hidden" 
                    multiple
                    accept="image/jpeg,image/png,image/jpg,application/pdf"
                  />
                  <button
                    type="button"
                    disabled={uploadingSheet}
                    onClick={() => sheetInputRef.current?.click()}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold px-4 py-2 rounded-lg border border-slate-700 transition-colors uppercase tracking-wide"
                  >
                    + Select Site Sheets
                  </button>
                </div>
              </div>

              {/* Staging Chips Interface Grid layout */}
              {queuedSheets.length > 0 && (
                <div className="bg-[#0B0F19]/60 border border-slate-800/80 rounded-lg p-4 space-y-3">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Staged Pages Queued For Extraction ({queuedSheets.length})</p>
                  <div className="flex flex-wrap gap-2">
                    {queuedSheets.map((file, idx) => (
                      <div key={idx} className="flex items-center gap-2 bg-[#1F2937] border border-slate-700 rounded-md px-3 py-1.5 text-xs">
                        <span className="font-mono text-emerald-400 font-bold">P{idx + 1}</span>
                        <span className="text-slate-200 max-w-[180px] truncate">{file.name}</span>
                        <button
                          type="button"
                          disabled={uploadingSheet}
                          onClick={() => removeQueuedSheet(idx)}
                          className="text-slate-500 hover:text-red-400 font-bold ml-1 transition-colors"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                  
                  {/* Processing execution execution node */}
                  <div className="pt-2">
                    <button
                      type="button"
                      disabled={uploadingSheet}
                      onClick={handleBatchSheetUploadSubmit}
                      className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white font-bold text-xs py-2.5 rounded-lg transition-all shadow-md uppercase tracking-wider"
                    >
                      {uploadingSheet ? "🤖 Aggregating & Auditing Site Ledger Matrices..." : `Execute Cognitive Ingest (${queuedSheets.length} Page${queuedSheets.length > 1 ? 's' : ''})`}
                    </button>
                  </div>
                </div>
              )}
            </div>

            {sheetUploadStatus && (
              <p className="text-xs font-bold text-center text-emerald-400 tracking-wide mt-1">{sheetUploadStatus}</p>
            )}

            {/* Yields Matrix Table Card */}
            <div className="bg-[#111827] border border-slate-800/80 rounded-xl shadow-md overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-800 bg-[#161F30]">
                <h2 className="font-bold text-white text-sm uppercase tracking-wide">Cumulative Executed Material Yields Matrix</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs lg:text-sm">
                  <thead>
                    <tr className="bg-[#1F2937]/50 border-b border-slate-800 text-slate-400 font-semibold tracking-wide">
                      <th className="p-4">Work Category</th>
                      <th className="p-4">Element ID / Reference</th>
                      <th className="p-4 text-right">Total Net Output Executed</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {analytics.quantities_executed.length === 0 ? (
                      <tr>
                        <td colSpan={3} className="p-8 text-center text-slate-500 font-medium">No material run records linked yet.</td>
                      </tr>
                    ) : (
                      (() => {
                        const mergedYields: Record<string, { category: string; element_id: string; total_output: number; unit: string }> = {};
                        analytics.quantities_executed.forEach((entry) => {
                          const normalizedId = entry.element_id.replace(/\s*\([^)]*\)/g, "").trim().toUpperCase();
                          if (mergedYields[normalizedId]) {
                            mergedYields[normalizedId].total_output += Number(entry.total_output);
                          } else {
                            mergedYields[normalizedId] = { ...entry, element_id: normalizedId };
                          }
                        });

                        return Object.values(mergedYields).map((entry, idx) => {
                          let displayCategory = entry.category;
                          if (displayCategory === "DAILY LAB. LABOUR REPORT" || displayCategory === "DAILY_LAB_LABOUR_REPORT") {
                            displayCategory = entry.element_id.startsWith("SW") ? "Shear Wall" : "General Civil Work";
                          } else {
                            displayCategory = displayCategory.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
                          }

                          return (
                            <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                              <td className="p-4 font-bold text-white">
                                <span className="px-2 py-0.5 bg-slate-800 border border-slate-700 rounded text-[10px] text-slate-300 uppercase tracking-wide mr-2">
                                  {displayCategory}
                                </span>
                              </td>
                              <td className="p-4 text-slate-300 font-mono text-xs">{entry.element_id}</td>
                              <td className="p-4 text-right font-black text-emerald-400">
                                {Number(entry.total_output).toLocaleString(undefined, { minimumFractionDigits: 2 })} 
                                <span className="text-xs font-normal text-slate-400 lowercase ml-1">{entry.unit}</span>
                              </td>
                            </tr>
                          );
                        });
                      })()
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Active Site Logs Management Shelf Control Center */}
            {processedDates.length > 0 && (
              <div className="bg-[#111827] border border-slate-800/80 rounded-xl p-6 shadow-md">
                <h3 className="text-xs font-bold uppercase tracking-wider mb-4 text-slate-400">Active Site Ledgers Injected</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  {processedDates.map((dateStr) => (
                    <div key={dateStr} className="flex items-center justify-between bg-[#1F2937]/40 p-3 rounded-lg border border-slate-800/80">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold text-slate-300">{dateStr}</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleDeleteLog(dateStr)}
                        className="text-[10px] font-extrabold uppercase tracking-wider text-red-400 hover:text-red-300 bg-red-950/20 hover:bg-red-950/50 border border-red-900/30 px-2.5 py-1 rounded-md transition-all"
                      >
                        Remove Sheet
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Auditor Assistant Tab */}
        {activeTab === 'auditor' && (
          <div className="bg-[#111827] border border-slate-800 rounded-xl shadow-xl overflow-hidden flex flex-col h-[650px]">
            <div className="px-6 py-4 border-b border-slate-800 bg-[#161F30] flex justify-between items-center">
              <div>
                <h2 className="text-sm lg:text-base font-bold text-white uppercase tracking-wide">Project Document AI Auditor</h2>
                <p className="text-xs text-slate-400 mt-0.5">Localized Clause Relationship & Cross-Specification Mapping Engine</p>
              </div>
              <div className="text-right text-xs text-blue-400 font-mono tracking-wider">ActiveGraph::Node_{selectedProjectId}</div>
            </div>

            <div className="p-4 bg-[#0F1622] border-b border-slate-800/80">
              <div 
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-700 hover:border-blue-500 rounded-lg p-5 text-center cursor-pointer transition-colors bg-[#111827] shadow-inner"
              >
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  onChange={handleFileUpload} 
                  className="hidden" 
                  accept="*"
                />
                <p className="text-sm font-semibold text-slate-200">
                  {uploading ? "Extracting Relationship Links..." : "Drag & drop or click to upload contract / spec file"}
                </p>
                <p className="text-xs text-slate-500 mt-1">Accepts PDF, TXT, DOCX, MD, Images</p>
              </div>
              {uploadStatus && (
                <p className="text-xs text-center font-bold mt-2 text-blue-400 tracking-wide">{uploadStatus}</p>
              )}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#0F1622]/40">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] rounded-lg px-4 py-2.5 text-xs lg:text-sm whitespace-pre-wrap leading-relaxed shadow-md ${
                    msg.role === 'user' ? 'bg-blue-600 text-white font-medium' : 'bg-[#1F2937] border border-slate-800 text-slate-100'
                  }`}>
                    {msg.text}
                  </div>
                </div>
              ))}
              {loadingAnswer && (
                <div className="flex justify-start">
                  <div className="bg-[#1F2937] border border-slate-800 text-slate-400 font-medium rounded-lg px-4 py-2 text-xs lg:text-sm shadow-md flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-ping" />
                    Crawling document knowledge network nodes...
                  </div>
                </div>
              )}
            </div>

            <form onSubmit={handleSendMessage} className="p-3 bg-[#111827] border-t border-slate-800 flex gap-2">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask about liabilities, penalty thresholds, transformer models..."
                className="flex-1 px-4 py-2.5 text-xs lg:text-sm border border-slate-700 rounded-lg focus:outline-hidden focus:border-blue-500 text-white bg-[#1F2937] shadow-inner"
                disabled={uploading}
              />
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 text-xs font-bold rounded-lg transition-colors disabled:opacity-50"
                disabled={!chatInput.trim() || loadingAnswer || uploading}
              >
                Query
              </button>
            </form>
          </div>
        )}
      </div>
    </main>
  );
}