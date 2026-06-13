"use client";

import { useState, useEffect } from "react";
import { getApiBaseUrl } from "@/utils/api";
import { 
  BarChart3, 
  Clock, 
  AlertTriangle, 
  Camera, 
  ShieldAlert,
  RefreshCw,
  TrendingUp,
  MapPin,
  PieChart as PieIcon
} from "lucide-react";
import dynamic from "next/dynamic";

// Dynamic import Recharts to prevent Server-Side Rendering (SSR) compilation mismatch crashes in Next.js
const ResponsiveContainer = dynamic(
  () => import("recharts").then((recharts) => recharts.ResponsiveContainer),
  { ssr: false }
);
const AreaChart = dynamic(
  () => import("recharts").then((recharts) => recharts.AreaChart),
  { ssr: false }
);
const Area = dynamic(
  () => import("recharts").then((recharts) => recharts.Area),
  { ssr: false }
);
const XAxis = dynamic(
  () => import("recharts").then((recharts) => recharts.XAxis),
  { ssr: false }
);
const YAxis = dynamic(
  () => import("recharts").then((recharts) => recharts.YAxis),
  { ssr: false }
);
const CartesianGrid = dynamic(
  () => import("recharts").then((recharts) => recharts.CartesianGrid),
  { ssr: false }
);
const Tooltip = dynamic(
  () => import("recharts").then((recharts) => recharts.Tooltip),
  { ssr: false }
);
const BarChart = dynamic(
  () => import("recharts").then((recharts) => recharts.BarChart),
  { ssr: false }
);
const Bar = dynamic(
  () => import("recharts").then((recharts) => recharts.Bar),
  { ssr: false }
);
const Cell = dynamic(
  () => import("recharts").then((recharts) => recharts.Cell),
  { ssr: false }
);
const PieChart = dynamic(
  () => import("recharts").then((recharts) => recharts.PieChart),
  { ssr: false }
);
const Pie = dynamic(
  () => import("recharts").then((recharts) => recharts.Pie),
  { ssr: false }
);
const Legend = dynamic(
  () => import("recharts").then((recharts) => recharts.Legend),
  { ssr: false }
);

interface AnalyticsSummary {
  total_violations: number;
  type_counts: { [key: string]: number };
  camera_counts: { [key: string]: number };
  zone_counts: { [key: string]: number };
  shift_counts: { [key: string]: number };
  hourly_counts: { [key: string]: number };
  active_cameras_count: number;
}

const COLORS = ["#f43f5e", "#f59e0b", "#f97316", "#10b981", "#6366f1"];

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    try {
      const apiBase = getApiBaseUrl();
      const res = await fetch(`${apiBase}/api/analytics/summary`);
      if (!res.ok) throw new Error("Failed to fetch compliance summary statistics");
      const data = await res.json();
      setSummary(data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to load analytics summaries");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
    // Poll every 5 seconds for analytics updates
    const interval = setInterval(fetchAnalytics, 5000);
    return () => clearInterval(interval);
  }, []);

  // Format Recharts data structures
  const getHourlyData = () => {
    if (!summary) return [];
    return Array.from({ length: 24 }, (_, i) => {
      const val = summary.hourly_counts[i] || summary.hourly_counts[String(i)] || 0;
      return {
        hour: `${String(i).padStart(2, "0")}:00`,
        Violations: val
      };
    });
  };

  const getCameraData = () => {
    if (!summary) return [];
    return Object.entries(summary.camera_counts || {}).map(([id, count]) => ({
      name: id,
      Violations: count
    }));
  };

  const getZoneData = () => {
    if (!summary) return [];
    return Object.entries(summary.zone_counts || {}).map(([name, count]) => ({
      name: name.length > 15 ? `${name.substring(0, 15)}...` : name,
      Violations: count
    }));
  };

  const getShiftData = () => {
    if (!summary) return [];
    return Object.entries(summary.shift_counts || {}).map(([shift, count]) => ({
      name: shift === "outside_shift" ? "Off-Shift" : shift.charAt(0).toUpperCase() + shift.slice(1),
      Violations: count
    }));
  };

  const getTypeData = () => {
    if (!summary) return [];
    return Object.entries(summary.type_counts || {}).map(([type, count]) => {
      let name = type;
      if (type === "both_missing") name = "Helmet & Vest Missing";
      else if (type === "helmet_missing") name = "Helmet Missing";
      else if (type === "vest_missing") name = "Vest Missing";
      return { name, value: count };
    });
  };

  const isDataEmpty = !summary || summary.total_violations === 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-zinc-100">Compliance Analytics</h2>
          <p className="text-sm text-zinc-400">
            Graphical insights and reports detailing safety gear compliance distributions.
          </p>
        </div>
        
        <button 
          onClick={fetchAnalytics}
          className="bg-zinc-900 hover:bg-zinc-850 text-zinc-300 text-xs font-semibold py-2.5 px-4 rounded-lg flex items-center justify-center gap-2 border border-zinc-800 transition-colors shrink-0"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh Reports</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center gap-3 text-sm">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <div>
            <span className="font-semibold">Backend Link offline:</span> Make sure your FastAPI backend is running. (Connecting to {getApiBaseUrl()})
          </div>
        </div>
      )}

      {loading && !summary ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-80 rounded-xl bg-zinc-900/30 animate-pulse border border-zinc-900" />
          ))}
        </div>
      ) : isDataEmpty ? (
        <div className="glass-panel p-24 text-center max-w-xl mx-auto space-y-4">
          <div className="w-12 h-12 bg-zinc-900 border border-zinc-800 text-zinc-500 rounded-lg flex items-center justify-center mx-auto">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-zinc-200">No Analytics Data</h3>
            <p className="text-xs text-zinc-400">
              Violations database is currently empty. Run streams to generate report logs.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Hourly Trend (Area Chart) */}
          <div className="glass-panel p-6 space-y-4 bg-zinc-900/10">
            <div className="flex items-center gap-2 border-b border-zinc-900 pb-2.5">
              <TrendingUp className="w-4.5 h-4.5 text-rose-500" />
              <h3 className="font-semibold text-zinc-200 text-sm">Hourly Violation Load</h3>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={getHourlyData()} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorViolations" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#f43f5e" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis dataKey="hour" stroke="#71717a" fontSize={10} />
                  <YAxis stroke="#71717a" fontSize={10} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a", borderRadius: 8 }}
                    labelStyle={{ color: "#a1a1aa", fontWeight: "bold" }}
                  />
                  <Area type="monotone" dataKey="Violations" stroke="#f43f5e" fillOpacity={1} fill="url(#colorViolations)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Breakdown by Type (Pie Chart) */}
          <div className="glass-panel p-6 space-y-4 bg-zinc-900/10">
            <div className="flex items-center gap-2 border-b border-zinc-900 pb-2.5">
              <PieIcon className="w-4.5 h-4.5 text-rose-500" />
              <h3 className="font-semibold text-zinc-200 text-sm">Violation Type Share</h3>
            </div>
            <div className="h-64 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={getTypeData()}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {getTypeData().map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a", borderRadius: 8 }}
                  />
                  <Legend 
                    verticalAlign="bottom" 
                    height={36} 
                    iconType="circle"
                    formatter={(value) => <span className="text-[11px] text-zinc-400 font-semibold uppercase tracking-wider">{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Violations by Zone (Bar Chart) */}
          <div className="glass-panel p-6 space-y-4 bg-zinc-900/10">
            <div className="flex items-center gap-2 border-b border-zinc-900 pb-2.5">
              <MapPin className="w-4.5 h-4.5 text-rose-500" />
              <h3 className="font-semibold text-zinc-200 text-sm">Violations by Physical Zone</h3>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={getZoneData()} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis dataKey="name" stroke="#71717a" fontSize={10} />
                  <YAxis stroke="#71717a" fontSize={10} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a", borderRadius: 8 }}
                    labelStyle={{ color: "#a1a1aa", fontWeight: "bold" }}
                  />
                  <Bar dataKey="Violations" fill="#f59e0b" radius={[4, 4, 0, 0]}>
                    {getZoneData().map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Violations by Shift (Bar Chart) */}
          <div className="glass-panel p-6 space-y-4 bg-zinc-900/10">
            <div className="flex items-center gap-2 border-b border-zinc-900 pb-2.5">
              <Clock className="w-4.5 h-4.5 text-rose-500" />
              <h3 className="font-semibold text-zinc-200 text-sm">Violations by Shift</h3>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={getShiftData()} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis dataKey="name" stroke="#71717a" fontSize={10} />
                  <YAxis stroke="#71717a" fontSize={10} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "#09090b", borderColor: "#27272a", borderRadius: 8 }}
                    labelStyle={{ color: "#a1a1aa", fontWeight: "bold" }}
                  />
                  <Bar dataKey="Violations" fill="#10b981" radius={[4, 4, 0, 0]}>
                    {getShiftData().map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[(index + 2) % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
