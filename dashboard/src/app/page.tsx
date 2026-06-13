"use client";

import { useState, useEffect } from "react";
import { getApiBaseUrl, getImageUrl } from "@/utils/api";
import { 
  ShieldAlert, 
  Camera, 
  Clock, 
  AlertTriangle, 
  ExternalLink,
  Info,
  Calendar,
  X,
  FileSpreadsheet
} from "lucide-react";
import Link from "next/link";

interface Violation {
  id: number;
  camera_id: string;
  zone: string;
  timestamp: string;
  violation_type: string;
  confidence: number;
  screenshot_url: string;
  shift: string;
}

interface AnalyticsSummary {
  total_violations: number;
  type_counts: { [key: string]: number };
  camera_counts: { [key: string]: number };
  zone_counts: { [key: string]: number };
  shift_counts: { [key: string]: number };
  hourly_counts: { [key: string]: number };
  active_cameras_count: number;
}

export default function DashboardOverview() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [recentViolations, setRecentViolations] = useState<Violation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedScreenshot, setSelectedScreenshot] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    try {
      const apiBase = getApiBaseUrl();
      
      // Fetch summary statistics
      const summaryRes = await fetch(`${apiBase}/api/analytics/summary`);
      if (!summaryRes.ok) throw new Error("Failed to fetch analytics summary");
      const summaryData = await summaryRes.json();
      setSummary(summaryData);

      // Fetch recent violations
      const violationsRes = await fetch(`${apiBase}/api/violations`);
      if (!violationsRes.ok) throw new Error("Failed to fetch violations");
      const violationsData = await violationsRes.json();
      // Sort desc by timestamp or ID and take top 8
      const sorted = (violationsData || []).sort((a: Violation, b: Violation) => b.id - a.id).slice(0, 8);
      setRecentViolations(sorted);

      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    // Poll every 3 seconds for near real-time alerts
    const interval = setInterval(fetchDashboardData, 3000);
    return () => clearInterval(interval);
  }, []);

  const getFriendlyType = (type: string) => {
    switch (type) {
      case "both_missing": return "Helmet & Vest Missing";
      case "helmet_missing": return "Helmet Missing";
      case "vest_missing": return "Safety Vest Missing";
      default: return type || "Unknown Violation";
    }
  };

  const getTypeBadgeColor = (type: string) => {
    switch (type) {
      case "both_missing": return "bg-rose-500/10 border-rose-500/30 text-rose-400 glow-rose";
      case "helmet_missing": return "bg-amber-500/10 border-amber-500/30 text-amber-400 glow-amber";
      case "vest_missing": return "bg-orange-500/10 border-orange-500/30 text-orange-400 glow-amber";
      default: return "bg-zinc-800 border-zinc-700 text-zinc-300";
    }
  };

  return (
    <div className="space-y-8">
      {/* Header section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-zinc-100">Safety Compliance Center</h2>
          <p className="text-sm text-zinc-400">
            Real-time tracking of personal protective equipment (PPE) violations.
          </p>
        </div>
        
        <div className="flex items-center gap-2 text-xs text-zinc-400 bg-zinc-900 border border-zinc-850 px-3.5 py-1.5 rounded-lg">
          <Calendar className="w-4 h-4 text-rose-500" />
          <span>Live Tracking Active</span>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center gap-3 text-sm">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <div>
            <span className="font-semibold">Connection Alert:</span> Make sure your FastAPI backend is running. (Connecting to {getApiBaseUrl()})
          </div>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Violations Card */}
        <div className="glass-panel p-6 bg-zinc-900/20 flex flex-col justify-between h-32 relative overflow-hidden group hover:border-zinc-700 transition-colors">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Total Violations</span>
            <div className="p-1.5 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-3xl font-bold text-zinc-100">
              {loading && !summary ? "..." : summary?.total_violations ?? 0}
            </h3>
            <p className="text-[10px] text-zinc-500 mt-1">Logged safety infractions</p>
          </div>
        </div>

        {/* Active Streams Card */}
        <div className="glass-panel p-6 bg-zinc-900/20 flex flex-col justify-between h-32 relative overflow-hidden hover:border-zinc-700 transition-colors">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Active Cameras</span>
            <div className="p-1.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Camera className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-3xl font-bold text-zinc-100">
              {loading && !summary ? "..." : summary?.active_cameras_count ?? 0}
            </h3>
            <p className="text-[10px] text-zinc-500 mt-1">Live ingest feeds configured</p>
          </div>
        </div>

        {/* Helmet Missing Count Card */}
        <div className="glass-panel p-6 bg-zinc-900/20 flex flex-col justify-between h-32 relative overflow-hidden hover:border-zinc-700 transition-colors">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">No Helmet Logs</span>
            <div className="p-1.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-400">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-3xl font-bold text-zinc-100">
              {loading && !summary ? "..." : 
                (summary?.type_counts?.["helmet_missing"] ?? 0) + (summary?.type_counts?.["both_missing"] ?? 0)
              }
            </h3>
            <p className="text-[10px] text-zinc-500 mt-1">Total helmet-related errors</p>
          </div>
        </div>

        {/* Vest Missing Count Card */}
        <div className="glass-panel p-6 bg-zinc-900/20 flex flex-col justify-between h-32 relative overflow-hidden hover:border-zinc-700 transition-colors">
          <div className="flex justify-between items-start">
            <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">No Safety Vest Logs</span>
            <div className="p-1.5 rounded bg-orange-500/10 border border-orange-500/20 text-orange-400">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-4">
            <h3 className="text-3xl font-bold text-zinc-100">
              {loading && !summary ? "..." : 
                (summary?.type_counts?.["vest_missing"] ?? 0) + (summary?.type_counts?.["both_missing"] ?? 0)
              }
            </h3>
            <p className="text-[10px] text-zinc-500 mt-1">Total vest-related errors</p>
          </div>
        </div>
      </div>

      {/* Main Dashboard Split Layout */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Recent Violations Feed (Takes 2 cols) */}
        <div className="xl:col-span-2 glass-panel p-6 space-y-6">
          <div className="flex items-center justify-between pb-3 border-b border-zinc-900">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-rose-500" />
              <h3 className="font-semibold text-zinc-200 text-sm">Real-time Violation Feed</h3>
            </div>
            <Link 
              href="/logs" 
              className="text-xs text-rose-400 hover:text-rose-300 font-semibold flex items-center gap-1 group"
            >
              <span>View History Log</span>
              <ExternalLink className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>

          {loading && recentViolations.length === 0 ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-24 rounded-lg bg-zinc-900/30 animate-pulse border border-zinc-900" />
              ))}
            </div>
          ) : recentViolations.length === 0 ? (
            <div className="py-16 text-center text-zinc-500 text-sm space-y-2">
              <Clock className="w-8 h-8 text-zinc-700 mx-auto" />
              <p>No safety violations logged yet today.</p>
            </div>
          ) : (
            <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
              {recentViolations.map((violation) => (
                <div 
                  key={violation.id} 
                  className="flex items-center justify-between p-3.5 rounded-lg border border-zinc-900 bg-zinc-950/40 hover:bg-zinc-900/40 transition-colors gap-4"
                >
                  <div className="flex items-center gap-4 min-w-0">
                    {/* Thumbnail click to enlarge */}
                    <div 
                      onClick={() => setSelectedScreenshot(getImageUrl(violation.screenshot_url))}
                      className="w-16 h-12 bg-black border border-zinc-800 rounded overflow-hidden shrink-0 cursor-zoom-in hover:border-zinc-600 transition-colors group relative"
                    >
                      <img 
                        src={getImageUrl(violation.screenshot_url)} 
                        alt="Violation Crop"
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-200"
                        onError={(e) => {
                          e.currentTarget.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="64" height="48" viewBox="0 0 64 48"><rect width="64" height="48" fill="%2318181b"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="%2352525b" font-size="8">Offline</text></svg>';
                        }}
                      />
                    </div>
                    
                    <div className="min-w-0 space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`px-2 py-0.5 rounded-full border text-[10px] font-semibold ${getTypeBadgeColor(violation.violation_type)}`}>
                          {getFriendlyType(violation.violation_type)}
                        </span>
                        <span className="text-[10px] text-zinc-500 font-mono">
                          Conf: {Math.round(violation.confidence * 100)}%
                        </span>
                      </div>
                      <p className="text-xs text-zinc-400 truncate">
                        Location: <span className="font-semibold text-zinc-300">{violation.zone}</span> ({violation.camera_id})
                      </p>
                    </div>
                  </div>

                  <div className="text-right shrink-0">
                    <span className="text-xs text-zinc-500 font-medium font-mono">
                      {violation.timestamp.split("T")[1]?.slice(0, 8) || violation.timestamp}
                    </span>
                    <p className="text-[10px] text-zinc-600 font-semibold uppercase tracking-wider mt-0.5">
                      {violation.shift} Shift
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Shift stats & details (Takes 1 col) */}
        <div className="glass-panel p-6 space-y-6 flex flex-col justify-between">
          <div className="space-y-6">
            <div className="flex items-center gap-2 pb-3 border-b border-zinc-900">
              <Clock className="w-5 h-5 text-rose-500" />
              <h3 className="font-semibold text-zinc-200 text-sm">Shift Distributions</h3>
            </div>

            {loading && !summary ? (
              <div className="space-y-4 py-4">
                {[1, 2].map((i) => (
                  <div key={i} className="h-12 bg-zinc-900/20 animate-pulse rounded border border-zinc-900" />
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {/* Morning Shift */}
                <div className="p-3 bg-zinc-950/50 border border-zinc-900 rounded-lg space-y-2">
                  <div className="flex justify-between text-xs font-semibold text-zinc-400">
                    <span>Morning Shift (09:00 - 13:00)</span>
                    <span className="text-rose-400">{summary?.shift_counts?.["morning"] ?? 0} events</span>
                  </div>
                  <div className="w-full bg-zinc-900 h-1.5 rounded-full overflow-hidden">
                    <div 
                      className="bg-rose-500 h-full glow-rose transition-all duration-500"
                      style={{ 
                        width: `${summary?.total_violations ? 
                          ((summary.shift_counts?.["morning"] ?? 0) / summary.total_violations) * 100 : 0}%` 
                      }}
                    />
                  </div>
                </div>

                {/* Evening Shift */}
                <div className="p-3 bg-zinc-950/50 border border-zinc-900 rounded-lg space-y-2">
                  <div className="flex justify-between text-xs font-semibold text-zinc-400">
                    <span>Evening Shift (15:00 - 19:00)</span>
                    <span className="text-rose-400">{summary?.shift_counts?.["evening"] ?? 0} events</span>
                  </div>
                  <div className="w-full bg-zinc-900 h-1.5 rounded-full overflow-hidden">
                    <div 
                      className="bg-amber-500 h-full glow-amber transition-all duration-500"
                      style={{ 
                        width: `${summary?.total_violations ? 
                          ((summary.shift_counts?.["evening"] ?? 0) / summary.total_violations) * 100 : 0}%` 
                      }}
                    />
                  </div>
                </div>

                {/* Outside Shift */}
                <div className="p-3 bg-zinc-950/50 border border-zinc-900 rounded-lg space-y-2">
                  <div className="flex justify-between text-xs font-semibold text-zinc-400">
                    <span>Off-Shift Hours</span>
                    <span className="text-zinc-400">{summary?.shift_counts?.["outside_shift"] ?? 0} events</span>
                  </div>
                  <div className="w-full bg-zinc-900 h-1.5 rounded-full overflow-hidden">
                    <div 
                      className="bg-zinc-700 h-full transition-all duration-500"
                      style={{ 
                        width: `${summary?.total_violations ? 
                          ((summary.shift_counts?.["outside_shift"] ?? 0) / summary.total_violations) * 100 : 0}%` 
                      }}
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="p-4 bg-zinc-950 border border-zinc-900 rounded-lg flex gap-3 text-xs text-zinc-400">
            <Info className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
            <p>
              Timer threshold is configured at <strong className="text-zinc-300">2.0 seconds</strong> of continuous non-compliance before logging screenshot evidence.
            </p>
          </div>
        </div>
      </div>

      {/* Screenshot Expand Modal */}
      {selectedScreenshot && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="relative glass-panel bg-zinc-950 border-zinc-800 max-w-4xl w-full overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-zinc-900 bg-zinc-950/80 flex items-center justify-between sticky top-0 z-10">
              <span className="font-semibold text-sm text-zinc-200">Violation Screenshot Evidence</span>
              <button 
                onClick={() => setSelectedScreenshot(null)}
                className="p-1 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            
            <div className="aspect-video bg-black flex items-center justify-center p-2">
              <img 
                src={selectedScreenshot} 
                alt="Enlarged Violation Evidence" 
                className="max-h-[70vh] w-auto max-w-full object-contain rounded"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
