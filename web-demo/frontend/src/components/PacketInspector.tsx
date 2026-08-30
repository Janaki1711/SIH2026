import React from 'react';

interface PacketInspectorProps {
  packetFields: any;
  hexDump: string;
  metrics: any;
}

export default function PacketInspector({ packetFields, hexDump, metrics }: PacketInspectorProps) {
  if (!packetFields) {
    return (
      <div className="tac-panel h-full flex flex-col items-center justify-center text-tac-muted font-mono text-sm gap-4">
        <div className="w-8 h-8 border-2 border-tac-border border-t-tac-green rounded-full animate-spin"></div>
        WAITING FOR TRANSMISSION...
      </div>
    );
  }

  return (
    <div className="tac-panel h-full flex flex-col">
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-tac-border shrink-0">
        <h3 className="font-tactical font-bold tracking-widest text-tac-text flex items-center gap-2 text-xs">
          <span className="w-2 h-2 bg-tac-blue rounded-full glow-blue"></span>
          BINARY PACKET (M3)
        </h3>
        <span className="text-[10px] font-mono text-tac-muted">
          SEQ #{packetFields.sequence_number}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto pr-1 space-y-4">
        {/* Packet Header Fields */}
        <div className="grid grid-cols-2 gap-1.5 text-xs font-mono">
          <div className="bg-tac-s3 p-2 rounded border border-tac-border">
            <div className="text-[9px] text-tac-muted mb-0.5">PRIORITY</div>
            <div className={packetFields.priority === 'LIFE_SAFETY_ALERT' ? 'text-tac-red font-bold' : 'text-tac-green text-sm'}>
              {packetFields.priority}
            </div>
          </div>
          <div className="bg-tac-s3 p-2 rounded border border-tac-border">
            <div className="text-[9px] text-tac-muted mb-0.5">CALLSIGN</div>
            <div className="text-white text-sm">{packetFields.source_callsign}</div>
          </div>
          <div className="bg-tac-s3 p-2 rounded border border-tac-border">
            <div className="text-[9px] text-tac-muted mb-0.5">CRC16 (CCITT)</div>
            <div className="text-tac-blue font-bold text-sm">{packetFields.crc16}</div>
          </div>
          <div className="bg-tac-s3 p-2 rounded border border-tac-border">
            <div className="text-[9px] text-tac-muted mb-0.5">ENCRYPTION</div>
            <div className="text-tac-blue text-sm">{packetFields.encryption}</div>
          </div>
          <div className="bg-tac-s3 p-2 rounded border border-tac-border">
            <div className="text-[9px] text-tac-muted mb-0.5">SRC LANG</div>
            <div className="text-white text-sm">{packetFields.source_language}</div>
          </div>
          <div className="bg-tac-s3 p-2 rounded border border-tac-border">
            <div className="text-[9px] text-tac-muted mb-0.5">TGT LANG</div>
            <div className="text-white text-sm">{packetFields.target_language}</div>
          </div>
        </div>

        {/* Size Breakdown */}
        <div className="bg-tac-s2 p-2.5 rounded border border-tac-border space-y-1.5">
          <div className="flex items-center justify-between text-[10px] font-mono">
            <span className="text-tac-muted">SEMANTIC PAYLOAD</span>
            <span className="text-tac-green font-bold">{packetFields.semantic_payload_bytes} B</span>
          </div>
          <div className="flex items-center justify-between text-[10px] font-mono border-t border-tac-border pt-1.5">
            <span className="text-tac-muted">FINAL PACKET (HEADERS + MAC)</span>
            <span className="text-tac-amber font-bold text-sm">{packetFields.final_packet_bytes} B</span>
          </div>
        </div>

        {/* Hex Dump */}
        <div>
          <div className="text-[10px] font-mono text-tac-muted mb-1">RAW WIRE FORMAT (HEX)</div>
          <div className="hex-display text-[10px]">
            {hexDump || 'NO DATA'}
          </div>
        </div>
      </div>
    </div>
  );
}
