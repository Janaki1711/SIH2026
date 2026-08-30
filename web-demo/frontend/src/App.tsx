import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LocationDashboard from './components/LocationDashboard';
import PerformanceLab from './components/PerformanceLab';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-tac-bg text-tac-text scanlines font-ui overflow-hidden flex flex-col">
        {/* Global Header */}
        <header className="h-12 border-b border-tac-border bg-tac-surface flex items-center px-6 z-10 justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="font-tactical font-bold text-xl tracking-widest text-tac-green glow-green">
              iTANTRA <span className="text-tac-muted">M3</span>
            </div>
            <div className="text-xs font-mono text-tac-muted border-l border-tac-border pl-3 ml-1">
              PROTOCOL SIMULATOR :: SIH 2026
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="text-tac-muted">PHASE 1 + 2 + 3 DEMO</span>
            <div className="flex items-center gap-2">
               <span className="w-2 h-2 rounded-full bg-tac-green animate-pulse-green"></span>
               <span className="text-tac-green">SYSTEM ONLINE</span>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 relative z-10 overflow-hidden">
          <Routes>
            <Route path="/" element={<Navigate to="/hubbli" replace />} />
            <Route path="/hubbli" element={<LocationDashboard location="hubbli" />} />
            <Route path="/tolankere" element={<LocationDashboard location="tolankere" />} />
            <Route path="/lab" element={<PerformanceLab />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
