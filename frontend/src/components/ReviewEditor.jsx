import React, { useEffect, useState } from 'react';
import { useTranslationStore } from '../store/useTranslationStore';

export default function ReviewEditor({ projectId }) {
  const { segments, fetchProjectSegments, approveSegment, loading } = useTranslationStore();
  const [editingTranslations, setEditingTranslations] = useState({});

  useEffect(() => {
    if (projectId) {
      fetchProjectSegments(projectId);
    }
  }, [projectId, fetchProjectSegments]);

  const handleTextChange = (segmentId, value) => {
    setEditingTranslations({
      ...editingTranslations,
      [segmentId]: value
    });
  };

  if (loading) return <div className="text-center p-10 text-slate-400">Loading document segments...</div>;
  if (!segments || segments.length === 0) return <div className="text-center p-10 text-slate-500">No segments found. Upload a document to start.</div>;

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center border-b pb-4 border-slate-700">
        <h1 className="text-2xl font-bold text-white">Side-by-Side Translation Editor</h1>
        <span className="bg-emerald-500/20 text-emerald-400 px-3 py-1 rounded text-sm">Reviewing</span>
      </div>

      <div className="space-y-4">
        {segments.map((seg) => {
          const currentText = editingTranslations[seg.id] ?? seg.translated_text ?? "";
          const isFuzzy = seg.match_type === "fuzzy";
          const isExact = seg.match_type === "exact";
          
          return (
            <div key={seg.id} className="grid grid-cols-2 gap-4 bg-slate-900 border border-slate-800 p-4 rounded-lg">
              
              {/* Left Column: Original Segment */}
              <div className="space-y-2 border-r border-slate-800 pr-4">
                <div className="flex justify-between text-xs text-slate-500">
                  <span>Segment #{seg.position} ({seg.segment_type})</span>
                  {isExact && <span className="text-emerald-400 font-bold">100% TM MATCH</span>}
                  {isFuzzy && <span className="text-amber-400 font-bold">FUZZY MATCH ({Math.round(seg.match_score * 100)}%)</span>}
                </div>
                <p className="text-slate-200 text-lg leading-relaxed">{seg.source_text}</p>
              </div>

              {/* Right Column: Editable Target Translation */}
              <div className="space-y-3 flex flex-col justify-between pl-2">
                <div className="flex justify-between items-center">
                  <span className={`text-xs px-2 py-0.5 rounded font-mono ${
                    seg.confidence_score >= 8 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                  }`}>
                    AI Confidence: {seg.confidence_score ? `${seg.confidence_score}/10` : 'N/A'}
                  </span>
                  
                  {seg.status === "accepted" ? (
                    <span className="text-emerald-400 text-sm font-semibold flex items-center gap-1">✓ Approved</span>
                  ) : (
                    <button
                      onClick={() => approveSegment(seg.id, currentText)}
                      className="bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1 rounded text-sm font-medium transition"
                    >
                      Approve & Save to TM
                    </button>
                  )}
                </div>

                <textarea
                  className="w-full bg-slate-950 text-slate-100 border border-slate-800 rounded p-2 focus:outline-none focus:border-emerald-500 transition leading-relaxed"
                  rows={3}
                  value={currentText}
                  onChange={(e) => handleTextChange(seg.id, e.target.value)}
                />

                {/* Back-Translation Verification Panel */}
                {seg.back_translated_text && (
                  <div className="bg-slate-950/50 border border-slate-800/80 p-2 rounded text-xs">
                    <span className="text-slate-500 font-semibold block mb-1">Back-Translation (AI interpretation in English):</span>
                    <p className="text-slate-400 italic">"{seg.back_translated_text}"</p>
                  </div>
                )}
              </div>

            </div>
          );
        })}
      </div>
    </div>
  );
}
