import React, { useState, useEffect } from 'react';
import { fetchEmails, fetchEmailDetail, generateDraft, syncGmail, getAuthUrl, fetchDrafts, fetchSettings, saveSettings, saveDraft, sendEmailReply, chatWithInbox, fetchAccounts, analyzeStyle, type Email, type EmailDetail } from './services/api';

function App() {
  const [activeTab, setActiveTab] = useState<"inbox" | "drafts" | "settings" | "chat">("inbox");
  
  // Inbox State
  const [emails, setEmails] = useState<Email[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<EmailDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [hasMore, setHasMore] = useState(true);
  
  // Drafts State
  const [draftsList, setDraftsList] = useState<any[]>([]);
  
  // Settings State
  const [settingsData, setSettingsData] = useState<any>({ manual: {}, inferred: {} });
  const [isSavingSettings, setIsSavingSettings] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  // Copilot State
  const [draft, setDraft] = useState("");
  const [instructions, setInstructions] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [contextUsed, setContextUsed] = useState<any>(null);
  
  // Chat State
  const [chatQuery, setChatQuery] = useState("");
  const [chatHistory, setChatHistory] = useState<{role: 'user' | 'ai', content: string, sources?: any[]}[]>([]);
  const [isChatting, setIsChatting] = useState(false);
  
  // Auth & Global
  const [isSyncing, setIsSyncing] = useState(false);
  const [account, setAccount] = useState<any>(null);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [activeAccountId, setActiveAccountId] = useState<number | null>(null);
  const [inboxWidth, setInboxWidth] = useState(400);
  const [isResizing, setIsResizing] = useState(false);

  useEffect(() => {
    if (!isResizing) return;
    const handleMouseMove = (e: MouseEvent) => {
       let newWidth = e.clientX;
       if (newWidth < 250) newWidth = 250;
       if (newWidth > 800) newWidth = 800;
       setInboxWidth(newWidth);
    };
    const handleMouseUp = () => setIsResizing(false);
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  useEffect(() => {
    const initAuth = async () => {
      try {
        const accs = await fetchAccounts();
        if (accs && accs.length > 0) {
          setAccounts(accs);
          setAccount(accs[0]);
          setActiveAccountId(accs[0].id);
        }
      } catch (e) {
        console.error(e);
      }
    };

    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('auth') === 'success') {
      alert("Successfully connected to Gmail!");
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    
    initAuth();
  }, []);

  useEffect(() => {
    if (activeAccountId !== null) {
      loadEmails(0, true);
    }
  }, [activeAccountId]);

  useEffect(() => {
    if (activeTab === "drafts") {
      loadDrafts();
    } else if (activeTab === "settings") {
      loadSettings();
    }
  }, [activeTab]);

  const loadDrafts = async () => {
    try {
      const data = await fetchDrafts();
      setDraftsList(data);
    } catch (e) {
      console.error(e);
    }
  };

  const loadSettings = async () => {
    try {
      const data = await fetchSettings();
      const profileData = data.profile_data || {};
      if (!profileData.manual && !profileData.inferred) {
          setSettingsData({ manual: profileData, inferred: {} });
      } else {
          setSettingsData({
              manual: profileData.manual || {},
              inferred: profileData.inferred || {},
              last_inferred_at: profileData.last_inferred_at
          });
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSaveSettings = async () => {
    setIsSavingSettings(true);
    try {
      await saveSettings({ profile_data: settingsData });
      alert("Settings saved successfully!");
    } catch (e) {
      console.error(e);
      alert("Failed to save settings");
    }
    setIsSavingSettings(false);
  };

  const handleAnalyzeStyle = async () => {
    setIsAnalyzing(true);
    try {
      const data = await analyzeStyle();
      setSettingsData({
          manual: data.profile_data.manual || {},
          inferred: data.profile_data.inferred || {},
          last_inferred_at: data.profile_data.last_inferred_at
      });
      alert("Successfully analyzed your sent emails!");
    } catch (e) {
      console.error(e);
      alert("Failed to analyze style. Make sure you have sent emails in the database.");
    }
    setIsAnalyzing(false);
  };

  const handleConnect = async () => {
    try {
      const data = await getAuthUrl();
      window.location.href = data.url;
    } catch (e) {
      console.error(e);
      alert("Failed to get auth URL. Is the backend running?");
    }
  };

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      const res = await syncGmail(activeAccountId || undefined);
      alert(`Sync complete! Downloaded ${res.emails_synced} emails.`);
      loadEmails(0, true);
    } catch (e) {
      console.error(e);
      alert("Failed to sync emails. Did you connect your account?");
    }
    setIsSyncing(false);
  };

  const loadEmails = async (skip = 0, reset = false) => {
    if (!hasMore && !reset) return;
    setLoading(true);
    try {
      const data = await fetchEmails(skip, 20, activeAccountId || undefined);
      if (data.length < 20) setHasMore(false);
      
      if (reset) {
        setEmails(data);
        setHasMore(data.length === 20);
      } else {
        setEmails(prev => [...prev, ...data]);
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const bottom = e.currentTarget.scrollHeight - e.currentTarget.scrollTop <= e.currentTarget.clientHeight + 50;
    if (bottom && !loading && hasMore) {
      loadEmails(emails.length);
    }
  };

  const handleSelectEmail = async (id: number) => {
    try {
      const data = await fetchEmailDetail(id);
      setSelectedEmail(data);
      setDraft("");
      setContextUsed(null);
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
      setContextUsed(res.context_used);
    } catch (e) {
      console.error(e);
      alert("Make sure the backend is running and API keys are set.");
    }
    setIsGenerating(false);
  };

  const handleSaveDraft = async () => {
    if (!draft) {
      alert("Generate a draft first before saving.");
      return;
    }
    try {
      await saveDraft({
        subject: `Re: ${selectedEmail?.subject || ''}`,
        body: draft,
        original_email_id: selectedEmail?.id
      });
      alert("Draft saved to database!");
    } catch (e) {
      console.error(e);
      alert("Failed to save draft");
    }
  };

  const handleSend = async () => {
    if (!draft || !selectedEmail) {
      alert("Generate a draft first before sending.");
      return;
    }
    setIsSending(true);
    try {
      await sendEmailReply(selectedEmail.id, draft);
      alert("Email sent successfully!");
      setDraft(""); // Clear draft on success
    } catch (e) {
      console.error(e);
      alert("Failed to send email");
    }
    setIsSending(false);
  };

  const handleChat = async () => {
    if (!chatQuery.trim()) return;
    
    const query = chatQuery;
    setChatQuery("");
    setChatHistory(prev => [...prev, { role: 'user', content: query }]);
    setIsChatting(true);
    
    try {
      const res = await chatWithInbox(query, activeAccountId || undefined);
      setChatHistory(prev => [...prev, { role: 'ai', content: res.response, sources: res.sources }]);
    } catch (e) {
      console.error(e);
      setChatHistory(prev => [...prev, { role: 'ai', content: "Failed to get an answer from the server." }]);
    }
    
    setIsChatting(false);
  };

  return (
    <div className="h-screen bg-[#F8FAFC] text-slate-800 flex flex-col font-sans overflow-hidden">
      
      {/* Top Navbar */}
      <header className="h-16 flex-none bg-white/70 backdrop-blur-xl border-b border-slate-200/60 flex items-center justify-between px-6 z-50 shadow-sm shadow-slate-100/50">
        
        {/* Brand */}
        <div className="flex items-center gap-3 w-64">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold shadow-lg shadow-indigo-200">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
          </div>
          <h1 className="text-xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600">
            Email Copilot
          </h1>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-slate-100/50 p-1 rounded-xl border border-slate-200/50">
          {(['inbox', 'chat', 'drafts', 'settings'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-5 py-1.5 rounded-lg text-sm font-semibold transition-all duration-200 capitalize ${
                activeTab === tab 
                  ? 'bg-white text-indigo-700 shadow-[0_2px_10px_rgb(0,0,0,0.06)]' 
                  : 'text-slate-500 hover:text-slate-700 hover:bg-slate-200/50'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>

        {/* Profile / Sync / Switch */}
        <div className="w-64 flex justify-end items-center gap-4">
          {account ? (
            <div className="flex items-center gap-4">
              <button 
                onClick={handleSync} 
                disabled={isSyncing} 
                className="px-4 py-1.5 bg-indigo-50 text-indigo-600 font-semibold text-sm rounded-full hover:bg-indigo-100 transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                <svg className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                {isSyncing ? "Syncing..." : "Sync"}
              </button>
              
              <div className="flex items-center gap-2 group relative">
                {account.picture_url ? (
                  <img src={account.picture_url} alt="Profile" className="w-9 h-9 rounded-full ring-2 ring-white shadow-sm" />
                ) : (
                  <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 text-indigo-700 flex items-center justify-center font-bold ring-2 ring-white shadow-sm">
                    {account.name ? account.name[0] : "U"}
                  </div>
                )}
                
                {/* Hover Dropdown */}
                <div className="absolute right-0 top-full mt-2 w-64 bg-white rounded-xl shadow-xl border border-slate-100 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 transform origin-top-right scale-95 group-hover:scale-100 z-50">
                  <div className="p-3 border-b border-slate-50 bg-slate-50/50 rounded-t-xl">
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Connected Accounts</p>
                    <div className="space-y-1">
                      {accounts.map(acc => (
                        <button 
                          key={acc.id} 
                          onClick={() => { setAccount(acc); setActiveAccountId(acc.id); }}
                          className={`w-full text-left px-3 py-2 rounded-lg flex items-center gap-3 transition-colors ${activeAccountId === acc.id ? 'bg-indigo-50 border border-indigo-100' : 'hover:bg-slate-100 border border-transparent'}`}
                        >
                          <div className="w-6 h-6 rounded-full bg-slate-200 overflow-hidden shrink-0">
                            {acc.picture_url ? <img src={acc.picture_url} /> : <div className="w-full h-full flex items-center justify-center text-xs font-bold text-slate-500">{acc.name[0]}</div>}
                          </div>
                          <div className="min-w-0">
                            <p className={`text-sm font-semibold truncate ${activeAccountId === acc.id ? 'text-indigo-700' : 'text-slate-700'}`}>{acc.email_address}</p>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="p-2">
                    <button onClick={handleConnect} className="w-full text-left px-3 py-2.5 text-sm text-indigo-600 font-semibold hover:bg-indigo-50 rounded-lg transition-colors flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" /></svg>
                      Add Another Account
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <button onClick={handleConnect} className="px-5 py-2 bg-slate-900 text-white text-sm font-semibold rounded-full hover:bg-slate-800 transition-colors shadow-lg shadow-slate-900/20">
              Connect Gmail
            </button>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex overflow-hidden max-w-[1600px] w-full mx-auto relative">
        
        {activeTab === "inbox" && (
          <>
            {/* Inbox List */}
            <div style={{ width: inboxWidth }} className={`flex-none bg-white/40 backdrop-blur-sm flex flex-col h-full z-10 relative ${isResizing ? 'select-none' : ''}`}>
              {/* Resizer Handle */}
              <div 
                onMouseDown={(e) => { e.preventDefault(); setIsResizing(true); }}
                className="absolute top-0 right-0 bottom-0 w-1.5 cursor-col-resize hover:bg-indigo-300 active:bg-indigo-500 z-50 border-r border-slate-200/60 transition-colors"
              />
              <div className="p-4 flex justify-between items-center bg-white/50 border-b border-slate-100 pr-6">
                <h2 className="text-lg font-bold text-slate-800">Inbox</h2>
                {loading && <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>}
              </div>
              
              <div className="flex-1 overflow-y-auto px-2 py-2 space-y-1 custom-scrollbar" onScroll={handleScroll}>
                {emails.length === 0 && !loading && (
                   <div className="p-6 text-sm text-slate-500 text-center bg-white rounded-xl border border-slate-100 shadow-sm mt-4">
                     No emails found. Sync your account to get started.
                   </div>
                )}
                {emails.map((email) => {
                  const isActive = selectedEmail?.id === email.id;
                  return (
                    <div 
                      key={email.id} 
                      onClick={() => handleSelectEmail(email.id)}
                      className={`p-4 cursor-pointer rounded-xl transition-all duration-200 border ${
                        isActive 
                          ? 'bg-white border-indigo-200 shadow-md shadow-indigo-100/50' 
                          : 'bg-transparent border-transparent hover:bg-white hover:border-slate-200 hover:shadow-sm'
                      }`}
                    >
                      <div className="flex justify-between items-baseline mb-1">
                        <span className={`text-sm truncate ${isActive ? 'font-bold text-indigo-900' : 'font-semibold text-slate-800'}`}>
                          {email.sender.split('<')[0].trim()}
                        </span>
                        <span className={`text-[11px] shrink-0 ml-2 ${isActive ? 'text-indigo-500 font-medium' : 'text-slate-400'}`}>
                          {new Date(email.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                        </span>
                      </div>
                      <h3 className={`text-sm mb-1 truncate ${isActive ? 'font-semibold text-slate-900' : 'font-medium text-slate-700'}`}>
                        {email.subject || "No Subject"}
                      </h3>
                      <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">
                        {email.snippet || "No snippet available"}
                      </p>
                    </div>
                  )
                })}
                {hasMore && !loading && emails.length > 0 && (
                  <div className="py-4 text-center">
                    <div className="w-5 h-5 mx-auto border-2 border-slate-300 border-t-indigo-500 rounded-full animate-spin"></div>
                  </div>
                )}
              </div>
            </div>

            {/* Email Detail & Copilot */}
            <div className="flex-1 overflow-y-auto bg-slate-50/50 p-6 flex gap-6 h-full">
              {selectedEmail ? (
                <>
                  {/* Original Email */}
                  <div className="flex-1 min-w-0 flex flex-col h-full bg-white rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 overflow-hidden">
                    <div className="p-6 border-b border-slate-100 bg-white z-10 relative">
                      <h2 className="text-2xl font-bold mb-4 text-slate-900 leading-tight">{selectedEmail.subject}</h2>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center text-slate-600 font-bold text-lg">
                          {selectedEmail.sender.charAt(0).toUpperCase()}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-sm text-slate-900 truncate">{selectedEmail.sender.split('<')[0].trim()}</p>
                          <p className="text-xs text-slate-500 truncate">{selectedEmail.sender.match(/<(.*)>/)?.[1] || selectedEmail.sender}</p>
                        </div>
                        <span className="text-sm font-medium text-slate-400">
                          {new Date(selectedEmail.timestamp).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex-1 relative bg-white">
                      {selectedEmail.body ? (
                        <iframe 
                          title="Email content"
                          srcDoc={selectedEmail.body}
                          className="w-full h-full border-none absolute inset-0 bg-white"
                          sandbox="allow-popups allow-popups-to-escape-sandbox allow-same-origin"
                        />
                      ) : (
                        <div className="prose prose-slate max-w-none p-6 text-sm">
                          {selectedEmail.cleaned_body || "No body content available."}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Copilot Panel */}
                  <div className="w-[380px] shrink-0 h-full flex flex-col gap-4">
                    <div className="flex-1 bg-white/80 backdrop-blur-xl border border-indigo-100 rounded-2xl shadow-xl shadow-indigo-100/50 p-5 flex flex-col relative overflow-hidden">
                      {/* Decorative gradient orb */}
                      <div className="absolute top-0 right-0 w-32 h-32 bg-purple-400/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
                      <div className="absolute bottom-0 left-0 w-32 h-32 bg-indigo-400/20 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2"></div>
                      
                      <h3 className="font-bold text-base mb-4 flex items-center text-indigo-700 relative z-10">
                        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                        AI Copilot
                      </h3>
                      
                      <div className="flex-1 relative z-10 flex flex-col">
                        <textarea 
                          className="flex-1 w-full p-4 text-sm text-slate-700 bg-white/90 border border-slate-200/60 rounded-xl shadow-inner focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none transition-all duration-200"
                          value={draft}
                          onChange={(e) => setDraft(e.target.value)}
                          placeholder="Hit Generate or type your draft here..."
                        />
                        {contextUsed && (
                          <div className="mt-3 p-3 bg-indigo-50/50 border border-indigo-100 rounded-lg flex items-start gap-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
                            <svg className="w-4 h-4 text-indigo-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                            <div>
                              <p className="text-xs font-bold text-indigo-900 mb-1">Sources Retrieved</p>
                              <div className="flex gap-3 text-[10px] text-slate-600 font-medium">
                                <span>{contextUsed.thread_emails_count} thread msg(s)</span>
                                <span>&middot;</span>
                                <span>{contextUsed.sender_emails_count} past msg(s)</span>
                                <span>&middot;</span>
                                <span>{contextUsed.similar_emails_count} similar msg(s)</span>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>

                      <div className="mt-4 space-y-3 relative z-10">
                        <div className="relative">
                          <input 
                            type="text" 
                            placeholder="Instruct the AI (e.g. 'say yes politely')" 
                            value={instructions}
                            onChange={(e) => setInstructions(e.target.value)}
                            className="w-full text-sm px-4 py-3 bg-white border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm transition-all" 
                            onKeyDown={(e) => { if(e.key === 'Enter') handleGenerate(instructions); }}
                          />
                          <button 
                            onClick={() => handleGenerate(instructions)}
                            disabled={isGenerating}
                            className="absolute right-1.5 top-1.5 bottom-1.5 px-3 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700 transition-colors disabled:opacity-50 flex items-center gap-1 shadow-md shadow-indigo-200"
                          >
                            {isGenerating ? (
                              <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                            ) : (
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                            )}
                            GEN
                          </button>
                        </div>
                        
                        <div className="flex gap-2">
                          <button onClick={() => handleGenerate("Make it shorter and more concise")} disabled={isGenerating} className="flex-1 py-2 bg-white text-slate-600 border border-slate-200 rounded-xl text-xs font-medium hover:bg-slate-50 hover:border-slate-300 transition-all disabled:opacity-50 shadow-sm">Shorter</button>
                          <button onClick={() => handleGenerate("Make it more formal and professional")} disabled={isGenerating} className="flex-1 py-2 bg-white text-slate-600 border border-slate-200 rounded-xl text-xs font-medium hover:bg-slate-50 hover:border-slate-300 transition-all disabled:opacity-50 shadow-sm">More Formal</button>
                        </div>

                        <div className="flex gap-2 mt-2">
                          <button 
                            onClick={handleSaveDraft} 
                            disabled={isSending || !draft}
                            className="flex-1 py-3 bg-white border border-slate-200 text-slate-700 rounded-xl text-sm font-bold hover:bg-slate-50 transition-all disabled:opacity-50 shadow-sm"
                          >
                            Save Draft
                          </button>
                          <button 
                            onClick={handleSend} 
                            disabled={isSending || !draft}
                            className="flex-[2] py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl text-sm font-bold hover:from-indigo-700 hover:to-purple-700 transition-all disabled:opacity-50 shadow-lg shadow-indigo-200 flex items-center justify-center gap-2"
                          >
                            {isSending ? (
                              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                            ) : (
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
                            )}
                            {isSending ? "Sending..." : "Send via Gmail"}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center text-slate-400 bg-white rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100">
                  <svg className="w-16 h-16 mb-4 text-slate-200" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                  <p className="text-lg font-medium">Select an email to view</p>
                </div>
              )}
            </div>
          </>
        )}

        {activeTab === "drafts" && (
          <div className="flex-1 overflow-y-auto p-10 flex justify-center">
            <div className="w-full max-w-5xl">
              <h2 className="text-3xl font-extrabold mb-8 text-slate-900 tracking-tight">Saved Drafts</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {draftsList.length === 0 ? (
                  <div className="col-span-full p-12 text-center bg-white rounded-2xl border border-slate-100 shadow-sm">
                    <svg className="w-12 h-12 mx-auto text-slate-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                    <p className="text-slate-500 font-medium">No drafts saved yet. Generate one in the Inbox!</p>
                  </div>
                ) : (
                  draftsList.map((d: any) => (
                    <div key={d.id} className="bg-white border border-slate-200/60 rounded-2xl p-6 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 flex flex-col group cursor-pointer relative overflow-hidden">
                      <div className="absolute inset-0 bg-gradient-to-br from-indigo-50/0 to-indigo-50/0 group-hover:from-indigo-50/50 group-hover:to-transparent transition-all duration-300"></div>
                      <div className="relative z-10">
                        <div className="flex justify-between items-start mb-3">
                          <span className="px-2.5 py-1 bg-indigo-50 text-indigo-600 rounded-md text-[10px] font-bold uppercase tracking-wider">Draft</span>
                          <span className="text-xs text-slate-400 font-medium">{new Date(d.created_at).toLocaleDateString()}</span>
                        </div>
                        <h3 className="font-bold text-lg mb-3 text-slate-900 leading-tight">{d.subject || "No Subject"}</h3>
                        <div className="text-sm text-slate-600 line-clamp-5 mb-4 relative prose prose-sm">
                          {d.body}
                        </div>
                      </div>
                      <div className="mt-auto relative z-10 pt-4 border-t border-slate-100 flex justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                        <button className="text-indigo-600 font-semibold text-sm flex items-center gap-1 hover:text-indigo-700">
                          Edit <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === "settings" && (
          <div className="flex-1 overflow-y-auto p-10 flex justify-center">
            <div className="w-full max-w-3xl">
              <h2 className="text-3xl font-extrabold mb-8 text-slate-900 tracking-tight">Preferences</h2>
              
              <div className="bg-white border border-slate-200/80 rounded-3xl p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-50 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
                
                <div className="relative z-10">
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-indigo-100 text-indigo-600 rounded-2xl flex items-center justify-center shadow-inner">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                      </div>
                      <div>
                        <h3 className="text-xl font-bold text-slate-900">AI Style Profile</h3>
                        <p className="text-sm text-slate-500">Train the AI to write exactly like you.</p>
                      </div>
                    </div>
                    <button 
                      onClick={handleAnalyzeStyle}
                      disabled={isAnalyzing}
                      className="px-4 py-2 bg-indigo-50 text-indigo-700 rounded-xl text-sm font-bold shadow-sm hover:bg-indigo-100 transition-all disabled:opacity-50"
                    >
                      {isAnalyzing ? "Analyzing..." : "Analyze My Sent Emails"}
                    </button>
                  </div>

                  {settingsData.inferred && Object.keys(settingsData.inferred).length > 0 && (
                    <div className="mb-8 p-4 bg-indigo-50/50 rounded-2xl border border-indigo-100/50">
                      <h4 className="text-sm font-bold text-indigo-900 mb-3">AI Inferred Traits</h4>
                      <div className="grid grid-cols-2 gap-3">
                        {Object.entries(settingsData.inferred).map(([key, value]) => (
                          <div key={key} className="bg-white px-3 py-2 rounded-lg text-xs border border-indigo-50 shadow-sm flex flex-col">
                            <span className="text-slate-400 capitalize mb-1">{key.replace(/_/g, ' ')}</span>
                            <span className="font-semibold text-slate-700">{value as string}</span>
                          </div>
                        ))}
                      </div>
                      <p className="mt-3 text-[10px] text-slate-400">Last analyzed: {settingsData.last_inferred_at ? new Date(settingsData.last_inferred_at).toLocaleString() : 'Never'}</p>
                    </div>
                  )}
                  
                  <div className="mb-8">
                    <label className="block text-sm font-semibold text-slate-700 mb-2">Manual Overrides & Instructions</label>
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <label className="block text-xs font-semibold text-slate-500 mb-1">Formality Override</label>
                        <input type="text" placeholder="e.g. Highly Professional" className="w-full p-2 text-sm border rounded-lg focus:ring-2 focus:ring-indigo-500" value={settingsData.manual?.formality || ""} onChange={e => setSettingsData({...settingsData, manual: {...settingsData.manual, formality: e.target.value}})} />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-500 mb-1">Greeting Override</label>
                        <input type="text" placeholder="e.g. Hi [Name]," className="w-full p-2 text-sm border rounded-lg focus:ring-2 focus:ring-indigo-500" value={settingsData.manual?.greeting_style || ""} onChange={e => setSettingsData({...settingsData, manual: {...settingsData.manual, greeting_style: e.target.value}})} />
                      </div>
                    </div>
                    <textarea 
                      className="w-full h-32 p-4 text-sm text-slate-700 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-slate-50 hover:bg-white transition-colors resize-none shadow-inner"
                      placeholder="e.g. Keep it brief. Use bullet points. Always sign off with 'Best, [My Name]'"
                      value={settingsData.manual?.instructions || ""}
                      onChange={(e) => setSettingsData({ ...settingsData, manual: { ...settingsData.manual, instructions: e.target.value } })}
                    />
                    <p className="mt-2 text-xs text-slate-500 font-medium">These manual instructions always override the AI inferred traits.</p>
                  </div>
                  
                  <div className="flex justify-end pt-6 border-t border-slate-100">
                    <button 
                      onClick={handleSaveSettings}
                      disabled={isSavingSettings}
                      className="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl text-sm font-bold shadow-lg shadow-indigo-200 hover:shadow-indigo-300 hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:transform-none"
                    >
                      {isSavingSettings ? "Saving..." : "Save Preferences"}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "chat" && (
          <div className="flex-1 overflow-hidden flex justify-center p-6 bg-slate-50/50">
            <div className="w-full max-w-4xl bg-white rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 flex flex-col overflow-hidden relative">
              <div className="p-6 border-b border-slate-100 bg-white z-10 flex items-center gap-4">
                <div className="w-12 h-12 bg-gradient-to-br from-indigo-100 to-purple-100 text-indigo-600 rounded-2xl flex items-center justify-center shadow-inner">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-slate-900">Inbox Chat</h2>
                  <p className="text-sm text-slate-500">Ask the AI questions about your emails.</p>
                </div>
              </div>
              
              <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/30">
                {chatHistory.length === 0 && (
                  <div className="text-center text-slate-400 mt-20">
                    <svg className="w-16 h-16 mx-auto text-slate-200 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                    <p>Try asking: "What was the latest update on the Q3 report?"</p>
                  </div>
                )}
                {chatHistory.map((msg, idx) => (
                  <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] rounded-2xl p-5 ${msg.role === 'user' ? 'bg-indigo-600 text-white shadow-md shadow-indigo-200' : 'bg-white border border-slate-200 shadow-sm text-slate-800'}`}>
                      <div className="prose prose-sm max-w-none">
                        {msg.content.split('\n').map((line, i) => <p key={i} className={msg.role === 'user' ? 'text-white' : ''}>{line}</p>)}
                      </div>
                      
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-slate-100">
                          <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Sources</p>
                          <div className="flex flex-col gap-2">
                            {msg.sources.map((s, sidx) => (
                              <div key={sidx} className="bg-slate-50 rounded-lg p-2 text-xs border border-slate-100 flex items-center gap-2">
                                <svg className="w-4 h-4 text-slate-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                                <span className="truncate font-medium text-slate-600">{s.subject || "No Subject"}</span>
                                <span className="text-slate-400 shrink-0">&middot; {s.sender.split('<')[0].trim()}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {isChatting && (
                  <div className="flex justify-start">
                    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                      <div className="flex gap-2">
                        <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                        <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0.4s" }}></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="p-4 bg-white border-t border-slate-100">
                <div className="relative">
                  <input 
                    type="text" 
                    value={chatQuery}
                    onChange={(e) => setChatQuery(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') handleChat(); }}
                    placeholder="Ask anything about your inbox..."
                    className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl px-5 py-4 pr-16 focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-inner"
                  />
                  <button 
                    onClick={handleChat}
                    disabled={isChatting || !chatQuery.trim()}
                    className="absolute right-2 top-2 bottom-2 aspect-square bg-indigo-600 text-white rounded-lg flex items-center justify-center hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-md shadow-indigo-200"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 12h14M12 5l7 7-7 7" /></svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
