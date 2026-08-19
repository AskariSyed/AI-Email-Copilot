import React, { useState, useEffect } from 'react';
import { fetchEmails, fetchEmailDetail, generateDraft, Email, EmailDetail } from './services/api';

function App() {
  const [emails, setEmails] = useState<Email[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<EmailDetail | null>(null);
  const [draft, setDraft] = useState("");
  const [instructions, setInstructions] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadEmails();
  }, []);

  const loadEmails = async () => {
    setLoading(true);
    try {
      const data = await fetchEmails();
      setEmails(data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const handleSelectEmail = async (id: number) => {
    try {
      const data = await fetchEmailDetail(id);
      setSelectedEmail(data);
      setDraft("");
    } catch (e) {
      console.error(e);
    }
  };

  const handleGenerate = async (customInstructions: string = "") => {
    if (!selectedEmail) return;
    setIsGenerating(true);
    try {
      const res = await generateDraft(selectedEmail.id, customInstructions);
      setDraft(res.generated_body);
    } catch (e) {
      console.error(e);
      alert("Make sure the backend is running and API keys are set.");
    }
    setIsGenerating(false);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 h-screen p-4 flex flex-col">
        <h1 className="text-xl font-bold text-blue-600 mb-8">AI Email Copilot</h1>
        <nav className="flex-1 space-y-2">
          <a href="#" className="block px-4 py-2 bg-blue-50 text-blue-700 rounded-md font-medium">Inbox</a>
          <a href="#" className="block px-4 py-2 text-slate-600 hover:bg-slate-50 rounded-md">Drafts</a>
          <a href="#" className="block px-4 py-2 text-slate-600 hover:bg-slate-50 rounded-md">Settings</a>
        </nav>
        <button onClick={loadEmails} className="mt-auto px-4 py-2 bg-slate-900 text-white rounded-md text-sm font-medium hover:bg-slate-800 transition-colors">
          Refresh API
        </button>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Email List */}
        <div className="w-1/3 border-r border-slate-200 bg-white overflow-y-auto">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center">
            <h2 className="text-lg font-semibold">Inbox</h2>
            {loading && <span className="text-xs text-blue-500">Loading...</span>}
          </div>
          <div className="divide-y divide-slate-100">
            {emails.length === 0 && !loading && (
               <div className="p-4 text-sm text-slate-500">No emails found. Did you sync your account?</div>
            )}
            {emails.map((email) => (
              <div 
                key={email.id} 
                className={`p-4 cursor-pointer hover:bg-slate-50 transition-colors ${selectedEmail?.id === email.id ? 'bg-blue-50' : ''}`}
                onClick={() => handleSelectEmail(email.id)}
              >
                <div className="flex justify-between items-baseline mb-1">
                  <span className="font-semibold text-sm truncate">{email.sender}</span>
                  <span className="text-xs text-slate-500 shrink-0 ml-2">{new Date(email.timestamp).toLocaleDateString()}</span>
                </div>
                <h3 className="text-sm font-medium mb-1 truncate">{email.subject || "No Subject"}</h3>
                <p className="text-xs text-slate-500 line-clamp-2">
                  {email.snippet || "No snippet available"}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Email Detail & Copilot */}
        <div className="flex-1 bg-white overflow-y-auto">
          {selectedEmail ? (
            <div className="p-6 max-w-4xl mx-auto flex gap-6">
              {/* Original Email */}
              <div className="flex-1 min-w-0">
                <div className="mb-6">
                  <h2 className="text-2xl font-bold mb-2 break-words">{selectedEmail.subject}</h2>
                  <div className="flex justify-between items-center text-sm text-slate-600">
                    <div className="truncate">
                      <span className="font-semibold text-slate-900">{selectedEmail.sender}</span>
                    </div>
                    <span className="shrink-0 ml-4">{new Date(selectedEmail.timestamp).toLocaleString()}</span>
                  </div>
                </div>
                <div className="prose prose-sm text-slate-700 max-w-none whitespace-pre-wrap">
                  {selectedEmail.cleaned_body || "No body content available."}
                </div>
              </div>

              {/* Copilot Panel */}
              <div className="w-80 bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-col shrink-0 h-fit sticky top-6">
                <h3 className="font-semibold text-sm mb-4 flex items-center text-indigo-600">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                  Copilot Draft
                </h3>
                
                <textarea 
                  className="w-full h-64 p-3 text-sm border border-slate-200 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 mb-4 bg-white resize-none"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  placeholder="Click Generate to create a draft..."
                />

                <div className="space-y-2 mb-4">
                  <input 
                    type="text" 
                    placeholder="Tell Copilot to tweak this..." 
                    value={instructions}
                    onChange={(e) => setInstructions(e.target.value)}
                    className="w-full text-sm px-3 py-2 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500" 
                  />
                  <div className="flex gap-2">
                    <button onClick={() => handleGenerate("Make it shorter")} disabled={isGenerating} className="flex-1 px-2 py-1.5 bg-white border border-slate-200 rounded text-xs hover:bg-slate-50 disabled:opacity-50">Shorter</button>
                    <button onClick={() => handleGenerate("Make it more formal")} disabled={isGenerating} className="flex-1 px-2 py-1.5 bg-white border border-slate-200 rounded text-xs hover:bg-slate-50 disabled:opacity-50">More Formal</button>
                  </div>
                </div>

                <div className="mt-auto space-y-2">
                  <button className="w-full py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 shadow-sm transition-colors disabled:opacity-50">
                    Create Gmail Draft
                  </button>
                  <button 
                    onClick={() => handleGenerate(instructions)}
                    disabled={isGenerating}
                    className="w-full py-2 bg-white text-slate-700 border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors disabled:opacity-50"
                  >
                    {isGenerating ? "Generating..." : (draft ? "Regenerate" : "Generate")}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-400">
              Select an email to read
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
