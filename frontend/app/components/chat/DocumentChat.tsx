'use client';

import { useRef, useState } from 'react';
import { Bot, Paperclip, Send } from 'lucide-react';
import { ChatMessage, sendChatMessage, uploadReferenceDocument } from '../../lib/api';

export default function DocumentChat({ siteId }: { siteId: number }) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'assistant', text: 'Upload a contract, tender, or spec file, and ask me anything about clauses, liabilities, or milestones.' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      await uploadReferenceDocument(siteId, file);
      setMessages((prev) => [...prev, { role: 'assistant', text: `Indexed "${file.name}" into the knowledge graph. Ask away.` }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', text: `Failed to index document: ${err instanceof Error ? err.message : 'unknown error'}` }]);
    } finally {
      setUploading(false);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;
    setMessages((prev) => [...prev, { role: 'user', text: question }]);
    setInput('');
    setLoading(true);
    try {
      const { response } = await sendChatMessage(siteId, question);
      setMessages((prev) => [...prev, { role: 'assistant', text: response }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'assistant', text: `Query failed: ${err instanceof Error ? err.message : 'unknown error'}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#111827] border border-slate-800 rounded-xl shadow-xl overflow-hidden flex flex-col h-[520px]">
      <div className="px-6 py-4 border-b border-slate-800 bg-[#161F30] flex items-center justify-between">
        <h2 className="text-sm font-bold text-white uppercase tracking-wide flex items-center gap-2">
          <Bot size={15} className="text-blue-400" /> Document Assistant
        </h2>
        <input
          type="file"
          ref={fileRef}
          className="hidden"
          accept=".pdf,.txt,.docx,.md"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleUpload(file);
            e.target.value = '';
          }}
        />
        <button
          onClick={() => fileRef.current?.click()}
          disabled={uploading}
          className="flex items-center gap-1.5 text-[11px] font-bold text-slate-300 hover:text-white bg-slate-800/60 hover:bg-slate-800 border border-slate-700 px-3 py-1.5 rounded-lg transition-colors"
        >
          <Paperclip size={11} /> {uploading ? 'Indexing...' : 'Attach'}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-[#0F1622]/40">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] rounded-lg px-4 py-2.5 text-xs whitespace-pre-wrap leading-relaxed shadow-md ${
                msg.role === 'user' ? 'bg-blue-600 text-white font-medium' : 'bg-[#1F2937] border border-slate-800 text-slate-100'
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-[#1F2937] border border-slate-800 text-slate-400 font-medium rounded-lg px-4 py-2 text-xs shadow-md">Thinking...</div>
          </div>
        )}
      </div>

      <form onSubmit={handleSend} className="p-3 bg-[#111827] border-t border-slate-800 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about liabilities, penalty clauses, milestones..."
          className="flex-1 px-4 py-2.5 text-xs border border-slate-700 rounded-lg focus:outline-hidden focus:border-blue-500 text-white bg-[#1F2937]"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 text-xs font-bold rounded-lg transition-colors disabled:opacity-50"
        >
          <Send size={13} />
        </button>
      </form>
    </div>
  );
}
