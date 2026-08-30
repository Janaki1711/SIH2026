import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../lib/websocket';

export default function PerformanceLab() {
  const wsUrl = `ws://localhost:8000/ws/hubbli`; // Use hubbli connection for lab commands
  const { state: wsState, lastMessage, sendMessage } = useWebSocket(wsUrl);

  const [metrics, setMetrics] = useState<any>(null);
  const [testResults, setTestResults] = useState<any[]>([]);
  const [lossRate, setLossRate] = useState(0.0);

  useEffect(() => {
    // Poll system metrics
    const interval = setInterval(() => {
      sendMessage({ type: 'get_system_metrics' });
    }, 2000);
    return () => clearInterval(interval);
  }, [sendMessage]);

  useEffect(() => {
    if (!lastMessage) return;
    const { type } = lastMessage;
    
    if (type === 'system_metrics') {
      setMetrics(lastMessage.data);
    } else if (type === 'test_result') {
      setTestResults(prev => [lastMessage.data, ...prev].slice(0, 5));
    }
  }, [lastMessage]);

  const handleTest = (testType: string, params: any = {}) => {
    sendMessage({ type: testType, ...params });
  };

  const updateLossRate = (rate: number) => {
    setLossRate(rate);
    sendMessage({ type: 'set_loss_rate', rate });
  };

  return (
    <div className="h-full flex flex-col p-4 gap-4 overflow-y-auto">
      <div className="flex items-center justify-between mb-4 border-b border-tac-border pb-4">
        <div>
          <h1 className="font-tactical font-bold text-3xl tracking-widest text-tac-blue glow-blue">
            PERFORMANCE LAB
          </h1>
          <p className="text-tac-muted font-mono text-sm mt-1">SIH 2026 BENCHMARK & METRICS</p>
        </div>
        <div className="font-mono text-sm flex flex-col items-end">
          <div className="text-tac-muted">BACKEND CONNECTION</div>
          <div className={wsState === 'OPEN' ? 'text-tac-green' : 'text-tac-red'}>{wsState}</div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        
        {/* System Metrics */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-4">
          <div className="tac-panel">
            <h3 className="font-tactical font-bold text-lg border-b border-tac-border pb-2 mb-4">SYSTEM TELEMETRY</h3>
            {metrics ? (
              <div className="space-y-4 font-mono text-sm">
                <div className="metric-card blue">
                  <div className="text-tac-muted mb-1">M3 ADAPTER MODE</div>
                  <div className="text-white text-xs whitespace-pre-wrap">{metrics.adapter_mode}</div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="metric-card">
                    <div className="text-tac-muted mb-1">PROCESS CPU</div>
                    <div className="text-xl font-bold text-tac-green">{metrics.process_cpu_pct}%</div>
                  </div>
                  <div className="metric-card">
                    <div className="text-tac-muted mb-1">PROCESS MEM</div>
                    <div className="text-xl font-bold text-tac-green">{metrics.process_mem_mb} MB</div>
                  </div>
                  <div className="metric-card">
                    <div className="text-tac-muted mb-1">SYSTEM CPU</div>
                    <div className="text-xl font-bold text-tac-blue">{metrics.system_cpu_pct}%</div>
                  </div>
                  <div className="metric-card">
                    <div className="text-tac-muted mb-1">SYSTEM MEM</div>
                    <div className="text-xl font-bold text-tac-blue">{metrics.system_mem_used_pct}%</div>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="text-tac-muted mb-1">TOTAL MESSAGES DB</div>
                  <div className="text-xl font-bold text-tac-amber">{metrics.stats.total_messages}</div>
                </div>
                <div className="text-[10px] text-tac-muted border border-tac-border p-2 rounded">
                  {metrics.note}
                </div>
              </div>
            ) : (
              <div className="text-tac-muted text-center py-10 font-mono">LOADING METRICS...</div>
            )}
          </div>

          <div className="tac-panel">
             <h3 className="font-tactical font-bold text-lg border-b border-tac-border pb-2 mb-4">ENVIRONMENT</h3>
             <div className="space-y-4">
                <div>
                   <div className="text-xs font-mono text-tac-muted mb-1">PACKET LOSS SIMULATION</div>
                   <div className="flex items-center gap-4">
                      <input 
                         type="range" min="0" max="1" step="0.05" 
                         value={lossRate} 
                         onChange={e => updateLossRate(parseFloat(e.target.value))}
                         className="flex-1 accent-tac-amber"
                      />
                      <span className="font-mono w-12 text-right text-tac-amber font-bold">
                         {(lossRate * 100).toFixed(0)}%
                      </span>
                   </div>
                </div>
             </div>
          </div>
        </div>

        {/* Test Controls */}
        <div className="col-span-12 lg:col-span-8 flex flex-col gap-4">
          <div className="tac-panel">
            <h3 className="font-tactical font-bold text-lg border-b border-tac-border pb-2 mb-4">PROTOCOL COMPLIANCE TESTS</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="border border-tac-border p-4 rounded bg-tac-s2">
                <h4 className="font-bold text-white mb-2">END-TO-END LATENCY</h4>
                <p className="text-xs text-tac-muted mb-4 h-10">Measures total processing time across the full pipeline for 5 standard phrases.</p>
                <button onClick={() => handleTest('test_latency')} className="btn-blue w-full">RUN TEST</button>
              </div>
              <div className="border border-tac-border p-4 rounded bg-tac-s2">
                <h4 className="font-bold text-white mb-2">CRC16 CORRUPTION</h4>
                <p className="text-xs text-tac-muted mb-4 h-10">Simulates bit flips in transit and verifies CRC16/CCITT-FALSE catches the corruption.</p>
                <button onClick={() => handleTest('test_crc')} className="btn-blue w-full">RUN TEST</button>
              </div>
              <div className="border border-tac-border p-4 rounded bg-tac-s2">
                <h4 className="font-bold text-white mb-2">ENCRYPTION BENCHMARK</h4>
                <p className="text-xs text-tac-muted mb-4 h-10">Measures encryption/decryption overhead on the payload.</p>
                <button onClick={() => handleTest('test_encryption')} className="btn-blue w-full">RUN TEST</button>
              </div>
              <div className="border border-tac-border p-4 rounded bg-tac-s2">
                <h4 className="font-bold text-white mb-2">PACKET BURST</h4>
                <p className="text-xs text-tac-muted mb-4 h-10">Sends 50 rapid packets to test loss rate and sequencing.</p>
                <button onClick={() => handleTest('test_packets', { count: 50, loss_rate: lossRate })} className="btn-blue w-full">RUN TEST</button>
              </div>
            </div>
          </div>

          <div className="tac-panel flex-1">
            <h3 className="font-tactical font-bold text-lg border-b border-tac-border pb-2 mb-4">TEST RESULTS</h3>
            <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
              {testResults.length === 0 ? (
                <div className="text-tac-muted text-center py-10 font-mono">NO TESTS RUN YET</div>
              ) : (
                testResults.map((res, i) => (
                  <div key={i} className="bg-tac-s3 border border-tac-border rounded p-3 font-mono text-sm">
                    <div className="flex justify-between items-center mb-2 border-b border-tac-border pb-2">
                      <span className="font-bold text-tac-green">{res.test}</span>
                      <span className="text-[10px] text-tac-amber bg-tac-amber/10 px-2 py-0.5 rounded">
                        {res.mode}
                      </span>
                    </div>
                    <pre className="text-xs text-tac-text overflow-x-auto">
                      {JSON.stringify(res, null, 2)}
                    </pre>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
