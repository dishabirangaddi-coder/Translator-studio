import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReviewEditor from './components/ReviewEditor';
import './App.css';

const API_BASE_URL = "http://localhost:8000";

function App() {
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState(null);
  const [projectName, setProjectName] = useState("");
  const [sourceLang, setSourceLang] = useState("en");
  const [targetLang, setTargetLang] = useState("es");
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch all projects on mount
  const fetchProjects = async () => {
    try {
      // In a real production setup we query all projects. Let's write a quick mock fetch or database check.
      // Since we don't have a direct /projects listing endpoint yet, we can query it or query DB.
      // Let's create an endpoint in main.py to fetch projects, or we can fetch a test list.
      const res = await axios.get(`${API_BASE_URL}/glossary`); // Placeholder or test endpoint
      // We can also just fetch projects if we add it to FastAPI. Let's make sure FastAPI has GET /projects in main.py.
    } catch (e) {
      console.log("Error fetching projects", e);
    }
  };

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0]);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile || !projectName) {
      setError("Please select a file and enter a project name.");
      return;
    }
    
    setUploading(true);
    setError(null);
    
    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      // 1. Upload & Parse
      const uploadUrl = `${API_BASE_URL}/documents/upload?name=${encodeURIComponent(projectName)}&source_lang=${sourceLang}&target_lang=${targetLang}`;
      const uploadRes = await axios.post(uploadUrl, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      const newProject = uploadRes.data;
      
      // 2. Trigger translation immediately in background
      await axios.post(`${API_BASE_URL}/translation/${newProject.id}/translate`);
      
      // 3. Set as active project
      setSelectedProjectId(newProject.id);
      setProjects([newProject, ...projects]);
      setProjectName("");
      setSelectedFile(null);
      alert("Document uploaded successfully! AI translation started in the background.");
    } catch (err) {
      setError(err.response?.data?.detail || "Upload and parsing failed. Make sure backend is running.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Header */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex justify-between items-center shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-emerald-500 flex items-center justify-center font-bold text-slate-950">TS</div>
          <span className="text-xl font-bold tracking-wide">Translation Studio</span>
        </div>
        <div className="text-xs text-slate-400">Powered by Llama 3.1 & RLAIF</div>
      </header>

      {/* Main Workspace */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-6 p-6">
        
        {/* Sidebar Controls */}
        <div className="lg:col-span-1 space-y-6">
          
          {/* Upload Form */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 shadow-md">
            <h2 className="text-lg font-bold text-white mb-4">Create New Project</h2>
            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Project Name</label>
                <input
                  type="text"
                  placeholder="e.g. Sales Agreement"
                  className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-100 text-sm focus:outline-none focus:border-emerald-500"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Source Lang</label>
                  <select
                    className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-100 text-sm focus:outline-none focus:border-emerald-500"
                    value={sourceLang}
                    onChange={(e) => setSourceLang(e.target.value)}
                  >
                    <option value="en">English (en)</option>
                    <option value="es">Spanish (es)</option>
                    <option value="fr">French (fr)</option>
                    <option value="de">German (de)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Target Lang</label>
                  <select
                    className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-slate-100 text-sm focus:outline-none focus:border-emerald-500"
                    value={targetLang}
                    onChange={(e) => setTargetLang(e.target.value)}
                  >
                    <option value="es">Spanish (es)</option>
                    <option value="en">English (en)</option>
                    <option value="fr">French (fr)</option>
                    <option value="de">German (de)</option>
                    <option value="ja">Japanese (ja)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">Select Document (PDF/DOCX)</label>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  className="w-full text-xs text-slate-400 file:mr-4 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-slate-200 hover:file:bg-slate-700 cursor-pointer"
                  onChange={handleFileChange}
                />
              </div>

              {error && <p className="text-rose-500 text-xs">{error}</p>}

              <button
                type="submit"
                disabled={uploading}
                className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white font-medium rounded text-sm transition"
              >
                {uploading ? "Uploading & Translating..." : "Create & Translate"}
              </button>
            </form>
          </div>

          {/* Quick instructions / Help */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 text-xs text-slate-400 space-y-2">
            <h3 className="font-bold text-slate-300">How to test the workflow:</h3>
            <p>1. Type a project name, select languages, and upload a document.</p>
            <p>2. The backend splits paragraphs into segments and sends new phrases to Groq.</p>
            <p>3. If glossary terms match, they are strictly enforced in translation.</p>
            <p>4. Back-translations are displayed below each segment for review.</p>
          </div>
        </div>

        {/* Editor Area */}
        <div className="lg:col-span-3 bg-slate-900/50 border border-slate-800 rounded-lg shadow-md overflow-hidden min-h-[500px]">
          {selectedProjectId ? (
            <ReviewEditor projectId={selectedProjectId} />
          ) : (
            <div className="h-full flex flex-col justify-center items-center p-10 text-center">
              <svg className="w-16 h-16 text-slate-700 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h3 className="text-lg font-bold text-slate-300 mb-1">No Active Project Selected</h3>
              <p className="text-sm text-slate-500 max-w-sm">Create a new project in the sidebar or upload a document to begin side-by-side verification.</p>
            </div>
          )}
        </div>

      </main>
    </div>
  );
}

export default App;
