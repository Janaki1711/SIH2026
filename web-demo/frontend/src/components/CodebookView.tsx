import React, { useState, useEffect } from 'react';

interface CodebookData {
  [category: string]: { [name: string]: number };
}

export default function CodebookView({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [codebook, setCodebook] = useState<CodebookData | null>(null);

  useEffect(() => {
    if (isOpen && !codebook) {
      fetch('http://localhost:8000/codebook')
        .then(r => r.json())
        .then(setCodebook)
        .catch(() => {});
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-tac-s1 border border-tac-border rounded-lg shadow-2xl w-[700px] max-h-[80vh] overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-tac-border">
          <h2 className="font-tactical font-bold tracking-widest text-tac-text text-lg flex items-center gap-2">
            <span className="text-xl">📖</span> SEMANTIC CODEBOOK v1.0
          </h2>
          <button onClick={onClose} className="text-tac-muted hover:text-white text-xl px-2">✕</button>
        </div>
        
        <div className="p-4 overflow-y-auto max-h-[70vh] space-y-4">
          {!codebook ? (
            <div className="text-center text-tac-muted font-mono py-8">Loading codebook from backend...</div>
          ) : (
            Object.entries(codebook).map(([category, mappings]) => (
              <div key={category}>
                <div className="font-tactical font-bold text-tac-amber tracking-widest text-sm mb-2 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-tac-amber rounded-full"></span>
                  {category}
                </div>
                <div className="grid grid-cols-2 gap-1">
                  {Object.entries(mappings).map(([name, code]) => (
                    <div key={name} className="flex items-center justify-between bg-tac-s2 border border-tac-border rounded px-3 py-1.5 font-mono text-xs">
                      <span className="text-tac-text">{name}</span>
                      <span className="text-tac-green font-bold">0x{(code as number).toString(16).toUpperCase().padStart(2, '0')}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
          
          <div className="mt-4 border-t border-tac-border pt-3">
            <p className="text-[10px] font-mono text-tac-muted leading-relaxed">
              This codebook is the single source of truth shared by the semantic encoder and decoder.
              All values are loaded dynamically from the Python backend (semantic_schema.py). 
              No mappings are duplicated in the frontend.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
