import React, { useState, useEffect, useRef } from 'react';

interface Stage {
  stage: string;
  status: string;
  duration_ms: number;
  input_bytes: number;
  output_bytes: number;
  details: any;
  ts: number;
}

interface PipelineViewProps {
  side: 'sender' | 'receiver';
  stages: Stage[];
}

const STAGE_ICONS: Record<string, string> = {
  STT_INPUT: '🎤',
  SEMANTIC_PARSING: '🧠',
  SEMANTIC_COMPRESSION: '📦',
  PROTOBUF_SERIALIZATION: '📋',
  CRC16: '✓',
  ENCRYPTION: '🔐',
  TRANSMISSION: '📡',
  PACKET_RECEIVED: '📡',
  DECRYPTION: '🔓',
  CRC16_VALIDATION: '✓',
  PROTOBUF_DECODING: '📋',
  SEMANTIC_DECODING: '🧠',
  LANGUAGE_REALIZATION: '🌐',
  TTS: '🔊',
};

const STAGE_LABELS: Record<string, string> = {
  STT_INPUT: 'INPUT',
  SEMANTIC_PARSING: 'SEMANTIC',
  SEMANTIC_COMPRESSION: 'ENCODE',
  PROTOBUF_SERIALIZATION: 'PROTOBUF',
  CRC16: 'CRC',
  ENCRYPTION: 'ENCRYPT',
  TRANSMISSION: 'TX',
  PACKET_RECEIVED: 'RX',
  DECRYPTION: 'DECRYPT',
  CRC16_VALIDATION: 'CRC',
  PROTOBUF_DECODING: 'DECODE',
  SEMANTIC_DECODING: 'SEMANTIC',
  LANGUAGE_REALIZATION: 'TRANSLATE',
  TTS: 'TTS',
};

const STAGE_EXPLANATIONS: Record<string, string> = {
  STT_INPUT: 'Speech-to-Text converts voice to natural language text. In this demo, typed text is used as the STT output.',
  SEMANTIC_PARSING: 'Instead of transmitting the entire sentence, iTANTRA extracts operational meaning using structured fields such as ACTION, TARGET, URGENCY, and QUANTITY.',
  SEMANTIC_COMPRESSION: 'The structured semantic message is bit-packed into an ultra-compact binary representation — typically 4 bytes for a full tactical command.',
  PROTOBUF_SERIALIZATION: 'Serializes the semantic payload into the M3 VoicePacket protobuf wire format with headers, callsign, and metadata.',
  CRC16: 'CRC16-CCITT-FALSE checksum detects accidental corruption during transmission.',
  ENCRYPTION: 'ChaCha20-Poly1305 authenticated encryption protects the packet from unauthorized reading or tampering.',
  TRANSMISSION: 'Sends the encrypted packet over the local demo transport (WebSocket). In production, this would be LoRa, BLE, or WFB-ng.',
  PACKET_RECEIVED: 'The encrypted packet arrives at the receiving station via local demo transport.',
  DECRYPTION: 'ChaCha20-Poly1305 authenticated decryption verifies integrity and recovers the plaintext.',
  CRC16_VALIDATION: 'Verifies the CRC16 checksum matches the received data to detect any corruption.',
  PROTOBUF_DECODING: 'Deserializes the M3 VoicePacket protobuf to extract the semantic payload bytes.',
  SEMANTIC_DECODING: 'Reconstructs the original operational meaning from the compact binary representation.',
  LANGUAGE_REALIZATION: 'Generates a natural language sentence in the target language directly from the semantic fields — NOT from translating the source text.',
  TTS: 'Text-to-Speech converts the generated target language text into audible speech.',
};

export default function PipelineView({ side, stages }: PipelineViewProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [techView, setTechView] = useState(false);
  const [expandedStage, setExpandedStage] = useState<string | null>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [stages]);

  const STAGE_ORDER = side === 'sender' ? [
    'STT_INPUT', 'SEMANTIC_PARSING', 'SEMANTIC_COMPRESSION',
    'PROTOBUF_SERIALIZATION', 'CRC16', 'ENCRYPTION', 'TRANSMISSION'
  ] : [
    'PACKET_RECEIVED', 'DECRYPTION', 'CRC16_VALIDATION',
    'PROTOBUF_DECODING', 'SEMANTIC_DECODING', 'LANGUAGE_REALIZATION', 'TTS'
  ];

  return (
    <div className="tac-panel h-full flex flex-col">
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-tac-border shrink-0">
        <h3 className="font-tactical font-bold tracking-widest text-tac-text flex items-center gap-2 text-xs">
          <span className={`w-2 h-2 rounded-full ${side === 'sender' ? 'bg-tac-amber glow-amber' : 'bg-tac-green glow-green'}`}></span>
          {side === 'sender' ? 'OUTBOUND PIPELINE' : 'INBOUND PIPELINE'}
        </h3>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setTechView(!techView)}
            className={`text-[9px] font-mono px-2 py-0.5 rounded border transition-all ${
              techView ? 'bg-tac-blue/20 border-tac-blue/40 text-tac-blue' : 'border-tac-border text-tac-muted hover:text-white'
            }`}
          >
            TECHNICAL VIEW
          </button>
          <span className="text-[10px] font-mono text-tac-muted">
            {stages.length > 0 ? `${stages.length}/${STAGE_ORDER.length}` : 'IDLE'}
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto pr-1 space-y-1" ref={scrollRef}>
        {STAGE_ORDER.map((stageName, idx) => {
          const stageData = stages.find(s => s.stage === stageName);
          const status = stageData ? stageData.status : 'WAITING';
          const isExp = expandedStage === stageName;
          
          let borderColor = 'border-tac-border';
          let bgColor = 'bg-transparent';
          let opacity = 'opacity-40';
          if (status === 'SUCCESS') { borderColor = 'border-tac-green/30'; bgColor = 'bg-tac-green/5'; opacity = 'opacity-100'; }
          else if (status === 'FAILED') { borderColor = 'border-tac-red/30'; bgColor = 'bg-tac-red/5'; opacity = 'opacity-100'; }

          return (
            <div key={stageName}>
              <div 
                className={`flex items-center gap-2 px-3 py-1.5 rounded border ${borderColor} ${bgColor} ${opacity} cursor-pointer hover:bg-tac-s2 transition-all duration-200`}
                onClick={() => setExpandedStage(isExp ? null : stageName)}
              >
                <span className="text-sm w-6 text-center">{STAGE_ICONS[stageName] || '•'}</span>
                <span className="text-[11px] font-mono font-bold flex-1">{STAGE_LABELS[stageName] || stageName}</span>
                
                {stageData && stageData.duration_ms > 0 && (
                  <span className="text-[9px] font-mono text-tac-blue">{stageData.duration_ms.toFixed(1)}ms</span>
                )}
                
                {(stageData?.input_bytes || 0) > 0 || (stageData?.output_bytes || 0) > 0 ? (
                  <span className="text-[9px] font-mono text-tac-muted">
                    {stageData?.input_bytes || 0}→<span className="text-tac-green">{stageData?.output_bytes || 0}B</span>
                  </span>
                ) : null}

                <span className={`text-[8px] font-mono font-bold px-1.5 py-0.5 rounded ${
                  status === 'SUCCESS' ? 'bg-tac-green/20 text-tac-green' :
                  status === 'FAILED' ? 'bg-tac-red/20 text-tac-red' :
                  'bg-tac-s3 text-tac-muted'
                }`}>{status}</span>
              </div>
              
              {/* Expanded Details */}
              {isExp && stageData && (
                <div className="ml-8 mt-1 mb-2 p-2.5 bg-tac-s3 border border-tac-border rounded text-xs font-mono space-y-1.5 animate-fadeIn">
                  {stageData.details?.mode && (
                    <div className="text-[10px] text-tac-amber bg-tac-amber/10 p-1.5 border border-tac-amber/20 rounded">
                      {stageData.details.mode}
                    </div>
                  )}
                  {stageData.details?.reduction_pct !== undefined && (
                    <div className="text-tac-green font-bold">{stageData.details.reduction_pct}% BYTE REDUCTION</div>
                  )}
                  {stageData.details?.crc_value && (
                    <div className="flex justify-between"><span className="text-tac-muted">CRC:</span><span className="text-tac-blue">{stageData.details.crc_value}</span></div>
                  )}
                  {stageData.details?.algo && (
                    <div className="flex justify-between"><span className="text-tac-muted">Algorithm:</span><span className="text-tac-blue">{stageData.details.algo}</span></div>
                  )}
                  {stageData.details?.transport && (
                    <div className="flex justify-between"><span className="text-tac-muted">Transport:</span><span>{stageData.details.transport}</span></div>
                  )}
                  {stageData.details?.translated_text && (
                    <div className="text-white font-ui mt-1">{stageData.details.translated_text}</div>
                  )}
                </div>
              )}

              {/* Technical Explanation */}
              {techView && STAGE_EXPLANATIONS[stageName] && (
                <div className="ml-8 mb-1 text-[9px] font-mono text-tac-muted leading-relaxed italic px-2">
                  {STAGE_EXPLANATIONS[stageName]}
                </div>
              )}

              {/* Arrow between stages */}
              {idx < STAGE_ORDER.length - 1 && (
                <div className={`text-center text-tac-muted text-[10px] ${opacity}`}>↓</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
