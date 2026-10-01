import React, { useState, useEffect, useRef } from 'react';
import { useWebSocket } from '../lib/websocket';
import PipelineView from './PipelineView';
import PacketInspector from './PacketInspector';
import SemanticPanel from './SemanticPanel';
import CodebookView from './CodebookView';

interface LocationProps {
  location: 'hubbli' | 'tolankere';
}

export default function LocationDashboard({ location }: LocationProps) {
  const wsUrl = `ws://localhost:8000/ws/${location}`;
  const { state: wsState, lastMessage, sendMessage } = useWebSocket(wsUrl);

  const [partnerConnected, setPartnerConnected] = useState(false);
  const [partnerName, setPartnerName] = useState<string>(location === 'hubbli' ? 'tolankere' : 'hubbli');
  
  const [inputText, setInputText] = useState('');
  const [language, setLanguage] = useState(location === 'hubbli' ? 'hi' : 'ta');
  const [targetLanguage, setTargetLanguage] = useState(location === 'hubbli' ? 'ta' : 'hi');
  const [callsign, setCallsign] = useState(location.toUpperCase());
  
  const [outboundStages, setOutboundStages] = useState<any[]>([]);
  const [inboundStages, setInboundStages] = useState<any[]>([]);
  const [latestPacketFields, setLatestPacketFields] = useState<any>(null);
  const [latestHexDump, setLatestHexDump] = useState<string>('');
  const [latestMetrics, setLatestMetrics] = useState<any>(null);
  const [latestSemantic, setLatestSemantic] = useState<any>(null);
  const [latestSemanticHex, setLatestSemanticHex] = useState<string>('');
  const [latestOriginalText, setLatestOriginalText] = useState<string>('');
  const [messages, setMessages] = useState<any[]>([]);
  const [codebookOpen, setCodebookOpen] = useState(false);

  // Track which side produced the latest semantic data
  const [semanticSide, setSemanticSide] = useState<'sender' | 'receiver'>('sender');

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  useEffect(() => {
    if (!lastMessage) return;
    const { type } = lastMessage;

    if (type === 'connected') {
      setPartnerConnected(lastMessage.partner_connected);
      setPartnerName(lastMessage.partner);
      sendMessage({ type: 'set_language', language });
    } else if (type === 'partner_connected') {
      setPartnerConnected(true);
    } else if (type === 'partner_disconnected') {
      setPartnerConnected(false);
    } else if (type === 'pipeline_start') {
      if (lastMessage.side === 'sender') setOutboundStages([]);
      else setInboundStages([]);
    } else if (type === 'stage_update') {
      const setFn = lastMessage.side === 'sender' ? setOutboundStages : setInboundStages;
      setFn(prev => [...prev.filter(s => s.stage !== lastMessage.stage), lastMessage]);
      
      // Capture semantic data from stages
      if (lastMessage.stage === 'SEMANTIC_PARSING' && lastMessage.details?.semantic_data) {
        setLatestSemantic(lastMessage.details.semantic_data);
        setSemanticSide('sender');
      }
      if (lastMessage.stage === 'SEMANTIC_DECODING' && lastMessage.details?.semantic_data) {
        setLatestSemantic(lastMessage.details.semantic_data);
        setSemanticSide('receiver');
      }
    } else if (type === 'packet_ready') {
      setLatestPacketFields(lastMessage.packet_fields);
      setLatestHexDump(lastMessage.hex_dump);
      setLatestSemantic(lastMessage.semantic_data);
      setLatestSemanticHex(lastMessage.semantic_binary_hex || '');
      setLatestOriginalText(lastMessage.original_text || '');
      setLatestMetrics(lastMessage.metrics);
      setSemanticSide('sender');
    } else if (type === 'message_sent_confirmed') {
      setMessages(prev => [...prev, { ...lastMessage, direction: 'outbound' }]);
      setLatestOriginalText(lastMessage.original_text);
      setLatestMetrics(lastMessage.metrics);
    } else if (type === 'message_delivered') {
      setMessages(prev => [...prev, { ...lastMessage, direction: 'inbound' }]);
      setLatestPacketFields(lastMessage.packet_fields);
      setLatestHexDump(lastMessage.hex_dump);
      setLatestMetrics(lastMessage.metrics);
      setLatestSemantic(lastMessage.semantic_data);
      setLatestOriginalText(lastMessage.translated_text);
      setSemanticSide('receiver');
    } else if (type === 'packet_lost') {
      if (!lastMessage.from_location) {
        setMessages(prev => [...prev, { 
          direction: 'outbound', timestamp: Date.now()/1000,
          original_text: "PACKET LOST IN TRANSIT", error: true, is_sos: false,
        }]);
      }
    }
  }, [lastMessage]);

  useEffect(() => {
    sendMessage({ type: 'set_language', language });
  }, [language, sendMessage]);

  const handleSend = () => {
    if (!inputText.trim()) return;
    sendMessage({
      type: 'send_message', text: inputText, language, target_language: targetLanguage,
      callsign, priority: 0
    });
    setInputText('');
  };

  const handleDemoSend = (preset: string) => {
    sendMessage({ type: 'demo_send', preset, callsign, target_language: targetLanguage });
  };

  const handleSOS = () => {
    sendMessage({ type: 'trigger_sos', callsign, target_language: targetLanguage });
  };

  return (
    <div className="h-screen flex flex-col p-3 gap-3 overflow-hidden">
      {/* Top Bar */}
      <div className="flex items-center justify-between tac-panel-dark shrink-0 py-2 px-4">
        <div className="flex items-center gap-5">
          <div>
            <div className="text-[9px] font-mono text-tac-muted">STATION</div>
            <div className="font-tactical font-bold text-xl tracking-wider text-white">{location.toUpperCase()}</div>
          </div>
          <div>
            <div className="text-[9px] font-mono text-tac-muted">CALLSIGN</div>
            <input type="text" value={callsign} onChange={e => setCallsign(e.target.value)}
              className="tac-input py-0.5 px-2 w-28 font-mono text-xs" />
          </div>
          <div>
            <div className="text-[9px] font-mono text-tac-muted">LOCAL LANG</div>
            <select value={language} onChange={e => setLanguage(e.target.value)} className="tac-select py-0.5 w-28 text-xs">
              <option value="hi">Hindi</option><option value="mr">Marathi</option>
              <option value="te">Telugu</option><option value="ta">Tamil</option>
              <option value="kn">Kannada</option><option value="en">English</option>
            </select>
          </div>
          <div>
            <div className="text-[9px] font-mono text-tac-muted">TARGET LANG</div>
            <select value={targetLanguage} onChange={e => setTargetLanguage(e.target.value)} className="tac-select py-0.5 w-28 text-xs">
              <option value="hi">Hindi</option><option value="mr">Marathi</option>
              <option value="te">Telugu</option><option value="ta">Tamil</option>
              <option value="kn">Kannada</option><option value="en">English</option>
            </select>
          </div>
        </div>
        
        <div className="flex items-center gap-5">
          <button onClick={() => setCodebookOpen(true)} className="btn-ghost text-[9px] font-mono">📖 CODEBOOK</button>
          <div className="text-right">
            <div className="text-[9px] font-mono text-tac-muted">LINK</div>
            <span className={`text-xs font-mono ${wsState === 'OPEN' ? 'text-tac-green' : 'text-tac-red'}`}>{wsState}</span>
          </div>
          <div className="text-right">
            <div className="text-[9px] font-mono text-tac-muted">{partnerName.toUpperCase()}</div>
            <div className="flex items-center gap-1.5 justify-end">
              <span className={partnerConnected ? 'connected-dot' : 'disconnected-dot'}></span>
              <span className={`text-xs font-mono ${partnerConnected ? 'text-tac-green' : 'text-tac-red'}`}>
                {partnerConnected ? 'ONLINE' : 'OFFLINE'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: 5 columns */}
      <div className="flex-1 grid grid-cols-20 gap-3 min-h-0">
        
        {/* Column 1: Communication Log (4 cols) */}
        <div className="col-span-4 flex flex-col min-h-0">
          <div className="tac-panel flex-1 flex flex-col min-h-0">
            <h3 className="font-tactical font-bold tracking-widest text-tac-text text-xs mb-3 border-b border-tac-border pb-2 shrink-0">
              COMM LOG
            </h3>
            
            <div className="flex-1 overflow-y-auto space-y-2 pr-1 font-ui">
              {messages.length === 0 && (
                <div className="text-center text-tac-muted text-xs mt-8 font-mono">NO MESSAGES</div>
              )}
              {messages.map((msg, idx) => (
                <div key={idx} className={`p-2 rounded border text-xs ${
                  msg.error ? 'bg-tac-red/10 border-tac-red' :
                  msg.is_sos ? 'bg-tac-red/20 border-tac-red' :
                  msg.direction === 'outbound' ? 'bg-tac-s2 border-tac-border' : 'bg-tac-surface border-tac-green/30'
                }`}>
                  <div className="flex justify-between items-center mb-1 font-mono text-[9px]">
                    <span className={`px-1.5 py-0.5 rounded ${msg.direction === 'outbound' ? 'bg-tac-amber/20 text-tac-amber' : 'bg-tac-green/20 text-tac-green'}`}>
                      {msg.direction === 'outbound' ? 'TX' : 'RX'}
                    </span>
                    <span className="text-tac-muted">{msg.timestamp ? new Date(msg.timestamp * 1000).toLocaleTimeString() : ''}</span>
                  </div>
                  
                  {msg.error ? (
                    <div className="text-tac-red font-mono font-bold text-center">{msg.original_text}</div>
                  ) : (
                    <>
                      <div className="font-medium leading-snug">
                        {msg.direction === 'inbound' ? msg.translated_text : msg.original_text}
                      </div>
                      <div className="mt-1.5 text-[9px] text-tac-muted flex justify-between border-t border-tac-border pt-1">
                        <span>{msg.metrics?.total_latency_ms?.toFixed(1)}ms</span>
                        <span>Sem: {msg.metrics?.semantic_payload_bytes}B</span>
                        <span>Pkt: {msg.metrics?.final_packet_bytes}B</span>
                      </div>
                    </>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="shrink-0 mt-3 border-t border-tac-border pt-3">
              <div className="flex gap-1.5 mb-1.5">
                <input type="text" value={inputText}
                  onChange={e => setInputText(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSend()}
                  placeholder="Type message..."
                  className="tac-input flex-1 text-sm py-1.5" />
                <button onClick={handleSend}
                  disabled={!inputText.trim() || !partnerConnected}
                  className="btn-primary disabled:opacity-50 text-xs px-3">SEND</button>
              </div>
              <div className="grid grid-cols-3 gap-1.5">
                <button onClick={() => handleDemoSend('hindi')} className="btn-ghost text-[9px]">DEMO HI</button>
                <button onClick={() => handleDemoSend('english')} className="btn-ghost text-[9px]">DEMO EN</button>
                <button onClick={handleSOS} className="btn-danger text-[9px] font-bold">🚨 SOS</button>
              </div>
            </div>
          </div>
        </div>

        {/* Column 2: Semantic Panel (5 cols) */}
        <div className="col-span-5 flex flex-col min-h-0 overflow-y-auto">
          <SemanticPanel 
            semanticData={latestSemantic}
            originalText={latestOriginalText}
            semanticBinaryHex={latestSemanticHex}
            metrics={latestMetrics}
            side={semanticSide}
          />
        </div>

        {/* Column 3: Outbound Pipeline (3 cols) */}
        <div className="col-span-3 min-h-0">
          <PipelineView side="sender" stages={outboundStages} />
        </div>

        {/* Column 4: Inbound Pipeline (3 cols) */}
        <div className="col-span-3 min-h-0">
          <PipelineView side="receiver" stages={inboundStages} />
        </div>

        {/* Column 5: Packet Inspector (5 cols) */}
        <div className="col-span-5 min-h-0">
          <PacketInspector 
            packetFields={latestPacketFields} 
            hexDump={latestHexDump}
            metrics={latestMetrics}
          />
        </div>
      </div>

      {/* Codebook Modal */}
      <CodebookView isOpen={codebookOpen} onClose={() => setCodebookOpen(false)} />
    </div>
  );
}
