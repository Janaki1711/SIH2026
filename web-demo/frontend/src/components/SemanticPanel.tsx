import React, { useState } from 'react';

interface SemanticFieldData {
  field: string;
  value: string | number;
  code: number;
  source_phrase: string;
  encoded_value: string;
  confidence?: number;
  source?: string;
}

interface SemanticData {
  fields: SemanticFieldData[];
  is_fallback: boolean;
  fallback_text: string;
  fallback_reason: string;
  matched_fields: string[];
  failed_fields: string[];
}

interface SemanticPanelProps {
  semanticData: SemanticData | null;
  originalText: string;
  semanticBinaryHex: string;
  metrics: any;
  side: 'sender' | 'receiver';
}

export default function SemanticPanel({ semanticData, originalText, semanticBinaryHex, metrics, side }: SemanticPanelProps) {
  const [expandedField, setExpandedField] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(true);

  if (!semanticData) {
    return (
      <div className="tac-panel flex flex-col items-center justify-center text-tac-muted font-mono text-sm py-8 gap-3">
        <div className="text-2xl opacity-40">🧠</div>
        <div>AWAITING SEMANTIC EXTRACTION...</div>
      </div>
    );
  }

  const isFallback = semanticData.is_fallback;
  const originalBytes = metrics?.original_text_bytes || 0;
  const semanticBytes = metrics?.semantic_payload_bytes || 0;
  const finalBytes = metrics?.final_packet_bytes || 0;
  const reductionPct = metrics?.reduction_pct || 0;

  // Calculate bar widths relative to the largest value
  const maxBytes = Math.max(originalBytes, finalBytes, 1);
  const origBarW = Math.round((originalBytes / maxBytes) * 100);
  const semBarW = Math.max(Math.round((semanticBytes / maxBytes) * 100), 2);
  const finalBarW = Math.round((finalBytes / maxBytes) * 100);

  return (
    <div className="tac-panel flex flex-col gap-4">
      {/* Header */}
      <div 
        className="flex items-center justify-between cursor-pointer pb-2 border-b border-tac-border"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <h3 className="font-tactical font-bold tracking-widest text-tac-text flex items-center gap-2 text-sm">
          <span className="text-lg">🧠</span>
          {side === 'sender' ? 'SEMANTIC MESSAGE' : 'DECODED SEMANTIC MESSAGE'}
        </h3>
        <div className="flex items-center gap-3">
          {!isFallback ? (
            <span className="flex items-center gap-1.5 text-[10px] font-mono bg-tac-green/15 text-tac-green border border-tac-green/30 px-2 py-0.5 rounded">
              <span className="w-1.5 h-1.5 bg-tac-green rounded-full animate-pulse"></span>
              SEMANTIC MODE ACTIVE
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-[10px] font-mono bg-tac-amber/15 text-tac-amber border border-tac-amber/30 px-2 py-0.5 rounded">
              <span className="w-1.5 h-1.5 bg-tac-amber rounded-full"></span>
              FALLBACK MODE
            </span>
          )}
          <span className="text-tac-muted text-xs">{isExpanded ? '▼' : '▶'}</span>
        </div>
      </div>

      {isExpanded && (
        <>
          {/* Original Input */}
          {originalText && (
            <div>
              <div className="text-[10px] font-mono text-tac-muted mb-1 flex items-center gap-1.5">
                <span>🗣️</span> ORIGINAL INPUT
              </div>
              <div className="font-ui text-sm text-white bg-tac-s3 p-3 rounded border border-tac-border leading-relaxed">
                {originalText}
              </div>
              <div className="text-center text-tac-muted text-lg mt-2">↓</div>
            </div>
          )}

          {/* Semantic Fields or Fallback */}
          {!isFallback ? (
            <>
              {/* Semantic Fields Grid */}
              <div className="space-y-1.5">
                {semanticData.fields.map((field) => {
                  const isExpField = expandedField === field.field;
                  const isUnknown = field.value === 'UNKNOWN' || field.value === 0;
                  const isCritical = field.field === 'URGENCY' && field.value === 'CRITICAL';
                  
                  return (
                    <div key={field.field}>
                      <div 
                        className={`flex items-center justify-between p-2.5 rounded border cursor-pointer transition-all duration-200 ${
                          isExpField ? 'bg-tac-blue/10 border-tac-blue/40' : 'bg-tac-s2 border-tac-border hover:border-tac-blue/30'
                        }`}
                        onClick={() => setExpandedField(isExpField ? null : field.field)}
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-xs font-mono font-bold text-tac-muted w-24">{field.field}</span>
                          <span className={`text-sm font-mono font-bold ${
                            isCritical ? 'text-tac-red' :
                            isUnknown ? 'text-tac-muted' : 'text-tac-green'
                          }`}>
                            {String(field.value)}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          {field.source && (
                            <span className={`text-[9px] px-1 py-0.2 rounded border font-mono ${
                              field.source === 'TINYML' ? 'bg-tac-cyan/10 text-tac-cyan border-tac-cyan/30' :
                              field.source === 'HYBRID' ? 'bg-tac-amber/10 text-tac-amber border-tac-amber/30' :
                              'bg-tac-blue/10 text-tac-blue border-tac-blue/20'
                            }`}>
                              {field.source}
                            </span>
                          )}
                          {!isUnknown ? (
                            <span className="text-tac-green text-xs">✓</span>
                          ) : (
                            <span className="text-tac-amber text-xs">⚠</span>
                          )}
                          <span className="text-[10px] text-tac-muted">{isExpField ? '▼' : '▶'}</span>
                        </div>
                      </div>
                      
                      {/* Field Inspector (expanded) */}
                      {isExpField && (
                        <div className="mt-1 ml-4 p-3 bg-tac-s3 rounded border border-tac-blue/20 space-y-2 text-xs font-mono animate-fadeIn">
                          <div className="flex justify-between">
                            <span className="text-tac-muted">Field:</span>
                            <span className="text-white">{field.field}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-tac-muted">Human Value:</span>
                            <span className="text-tac-green font-bold">{String(field.value)}</span>
                          </div>
                          {field.source && (
                            <div className="flex justify-between">
                              <span className="text-tac-muted">Engine Source:</span>
                              <span className="text-tac-cyan font-bold">{field.source}</span>
                            </div>
                          )}
                          {field.confidence !== undefined && (
                            <div className="flex justify-between">
                              <span className="text-tac-muted">Confidence:</span>
                              <span className="text-tac-green font-bold">{Math.round(field.confidence * 100)}%</span>
                            </div>
                          )}
                          <div className="flex justify-between">
                            <span className="text-tac-muted">Semantic ID:</span>
                            <span className="text-tac-blue font-bold">0x{field.code.toString(16).toUpperCase().padStart(2, '0')}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-tac-muted">Encoded Value:</span>
                            <span className="text-tac-amber font-bold">{field.encoded_value || `0x${field.code.toString(16).toUpperCase().padStart(2, '0')}`}</span>
                          </div>
                          {field.source_phrase && (
                            <div className="flex justify-between">
                              <span className="text-tac-muted">Source Phrase:</span>
                              <span className="text-white italic">"{field.source_phrase}"</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Matched/Failed Fields Summary */}
              {(semanticData.matched_fields.length > 0 || semanticData.failed_fields.length > 0) && (
                <div className="flex gap-2 flex-wrap text-[10px] font-mono">
                  {semanticData.matched_fields.map(f => (
                    <span key={f} className="bg-tac-green/10 text-tac-green border border-tac-green/20 px-1.5 py-0.5 rounded">
                      ✓ {f}
                    </span>
                  ))}
                  {semanticData.failed_fields.map(f => (
                    <span key={f} className="bg-tac-amber/10 text-tac-amber border border-tac-amber/20 px-1.5 py-0.5 rounded">
                      ⚠ {f}
                    </span>
                  ))}
                </div>
              )}

              {/* Semantic → Binary Arrow */}
              <div className="text-center text-tac-muted text-lg">↓</div>

              {/* Semantic Binary */}
              <div>
                <div className="text-[10px] font-mono text-tac-muted mb-1 flex items-center gap-1.5">
                  <span>📦</span> SEMANTIC BINARY ({semanticBytes} BYTES)
                </div>
                <div className="hex-display text-base tracking-widest">
                  {semanticBinaryHex || 'N/A'}
                </div>
              </div>
            </>
          ) : (
            /* Fallback Mode Display */
            <div className="space-y-3">
              <div className="bg-tac-amber/10 border border-tac-amber/30 rounded p-3 space-y-2">
                <div className="text-xs font-mono font-bold text-tac-amber flex items-center gap-2">
                  <span>🟡</span> FALLBACK MODE ACTIVE
                </div>
                {semanticData.fallback_reason && (
                  <div className="text-xs font-mono text-tac-muted">
                    <span className="text-tac-amber">Reason:</span> {semanticData.fallback_reason}
                  </div>
                )}
                {semanticData.failed_fields.length > 0 && (
                  <div className="text-xs font-mono text-tac-muted">
                    <span className="text-tac-red">Failed fields:</span> {semanticData.failed_fields.join(', ')}
                  </div>
                )}
                {semanticData.matched_fields.length > 0 && (
                  <div className="text-xs font-mono text-tac-muted">
                    <span className="text-tac-green">Matched fields:</span> {semanticData.matched_fields.join(', ')}
                  </div>
                )}
              </div>
              
              <div className="text-[10px] font-mono text-tac-muted">
                Fallback: Zlib compressed UTF-8 text. Semantic information that WAS extracted is preserved.
                This is a safety mechanism, not an error.
              </div>
            </div>
          )}

          {/* Compression Comparison Bars */}
          {metrics && (
            <>
              <div className="text-center text-tac-muted text-lg">↓</div>
              <div className="space-y-2.5">
                <div className="text-[10px] font-mono text-tac-muted mb-1">COMPRESSION COMPARISON</div>
                
                {/* Original */}
                <div className="space-y-0.5">
                  <div className="flex justify-between text-[10px] font-mono">
                    <span className="text-tac-muted">ORIGINAL TEXT</span>
                    <span className="text-white">{originalBytes} bytes</span>
                  </div>
                  <div className="h-3 bg-tac-s3 rounded overflow-hidden">
                    <div className="h-full bg-tac-red/60 rounded transition-all duration-700" style={{ width: `${origBarW}%` }}></div>
                  </div>
                </div>
                
                {/* Semantic */}
                <div className="space-y-0.5">
                  <div className="flex justify-between text-[10px] font-mono">
                    <span className="text-tac-muted">SEMANTIC PAYLOAD</span>
                    <span className="text-tac-green font-bold">{semanticBytes} bytes</span>
                  </div>
                  <div className="h-3 bg-tac-s3 rounded overflow-hidden">
                    <div className="h-full bg-tac-green rounded transition-all duration-700" style={{ width: `${semBarW}%` }}></div>
                  </div>
                </div>
                
                {/* Final Packet */}
                <div className="space-y-0.5">
                  <div className="flex justify-between text-[10px] font-mono">
                    <span className="text-tac-muted">FINAL SECURE PACKET</span>
                    <span className="text-tac-amber">{finalBytes} bytes</span>
                  </div>
                  <div className="h-3 bg-tac-s3 rounded overflow-hidden">
                    <div className="h-full bg-tac-amber/60 rounded transition-all duration-700" style={{ width: `${finalBarW}%` }}></div>
                  </div>
                </div>

                <div className="text-right text-tac-green font-bold text-xs font-mono mt-1">
                  {reductionPct}% SEMANTIC REDUCTION
                </div>
                <div className="text-[9px] text-tac-muted font-mono">
                  Reduction = (original − semantic) / original × 100 — MEASURED
                </div>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
