"use client";

import { useState, useEffect } from "react";
import { getApiBaseUrl, getImageUrl } from "@/utils/api";
import { 
  ClipboardList, 
  Search, 
  Download, 
  X, 
  Eye, 
  RefreshCw, 
  ChevronLeft, 
  ChevronRight,
  AlertTriangle
} from "lucide-react";

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

interface CameraConfig {
  id: string;
  rtsp_url: string;
  zone_name: string;
  is_online: boolean;
  last_seen: string | null;
}

export default function ViolationLogsPage() {
  const [violations, setViolations] = useState<Violation[]>([]);
  const [cameras, setCameras] = useState<CameraConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filter states
  const [selectedCamera, setSelectedCamera] = useState("");
  const [selectedType, setSelectedType] = useState("");
  const [selectedShift, setSelectedShift] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // Modal screenshot preview
  const [previewImage, setPreviewImage] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const apiBase = getApiBaseUrl();
      
      // Fetch cameras for dropdown filter
      const camsRes = await fetch(`${apiBase}/api/cameras`);
      if (camsRes.ok) {
        const camsData = await camsRes.json();
        setCameras(camsData);
      }

      // Build query string
      const queryParams = new URLSearchParams();
      if (selectedCamera) queryParams.append("camera_id", selectedCamera);
      if (selectedType) queryParams.append("violation_type", selectedType);
      if (selectedShift) queryParams.append("shift", selectedShift);
      if (startDate) queryParams.append("start_date", startDate);
      if (endDate) queryParams.append("end_date", endDate);

      const violationsRes = await fetch(`${apiBase}/api/violations?${queryParams.toString()}`);
      if (!violationsRes.ok) throw new Error("Failed to load violations log");
      const violationsData = await violationsRes.json();
      
      // Sort desc by ID (newest first)
      const sorted = (violationsData || []).sort((a: Violation, b: Violation) => b.id - a.id);
      setViolations(sorted);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to load log entries");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedCamera, selectedType, selectedShift, startDate, endDate]);

  const handleExportCSV = () => {
    if (violations.length === 0) {
      alert("No data available to export.");
      return;
    }

    const headers = [
      "ID",
      "Camera ID",
      "Zone / Location",
      "Timestamp",
      "Violation Type",
      "Confidence %",
      "Shift",
      "Screenshot URL"
    ];

    const rows = violations.map(item => [
      item.id,
      item.camera_id,
      `"${item.zone.replace(/"/g, '""')}"`,
      item.timestamp,
      item.violation_type,
      Math.round(item.confidence * 100),
      item.shift,
      getImageUrl(item.screenshot_url)
    ]);

    const csvContent = "data:text/csv;charset=utf-8," 
      + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
      
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `ntpc_ppe_violations_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Helper formatting functions
  const getFriendlyType = (type: string) => {
    switch (type) {
      case "both_missing": return "Helmet & Vest Missing";
      case "helmet_missing": return "Helmet Missing";
      case "vest_missing": return "Vest Missing";
      default: return type || "Unknown";
    }
  };

  const getBadgeClass = (type: string) => {
    switch (type) {
      case "both_missing": return "bg-rose-500/10 border-rose-500/20 text-rose-400";
      case "helmet_missing": return "bg-amber-500/10 border-amber-500/20 text-amber-400";
      case "vest_missing": return "bg-orange-500/10 border-orange-500/20 text-orange-400";
      default: return "bg-zinc-800 border-zinc-700 text-zinc-300";
    }
  };

  const formatTimestamp = (ts: string) => {
    try {
      // 2026-06-13T15:23:34 -> 2026-06-13 15:23:34
      return ts.replace("T", " ").split(".")[0];
    } catch {
      return ts;
    }
  };

  // Pagination Logic
  const totalPages = Math.ceil(violations.length / itemsPerPage) || 1;
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = violations.slice(indexOfFirstItem, indexOfLastItem);

  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  // Reset all filters
  const resetFilters = () => {
    setSelectedCamera("");
    setSelectedType("");
    setSelectedShift("");
    setStartDate("");
    setEndDate("");
    setCurrentPage(1);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-zinc-100">Violation History Logs</h2>
          <p className="text-sm text-zinc-400">
            Audit trailing and historical log list of confirmed entry violations.
          </p>
        </div>

        <button
          onClick={handleExportCSV}
          disabled={violations.length === 0}
          className="bg-rose-600 hover:bg-rose-500 disabled:bg-zinc-850 disabled:text-zinc-500 text-white text-sm font-semibold py-2.5 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors shrink-0 shadow-lg shadow-rose-950/10"
        >
          <Download className="w-4 h-4" />
          <span>Export Filtered CSV</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center gap-3 text-sm">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <div>
            <span className="font-semibold">Backend offline:</span> Make sure your FastAPI backend is running. (Connecting to {getApiBaseUrl()})
          </div>
        </div>
      )}

      {/* Filters Panel */}
      <div className="glass-panel p-6 bg-zinc-900/10 space-y-4">
        <div className="flex items-center gap-2 border-b border-zinc-900 pb-2.5">
          <Search className="w-4.5 h-4.5 text-rose-500" />
          <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">Search Filters</h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* Camera Filter */}
          <div>
            <label className="block text-[10px] font-semibold text-zinc-500 uppercase tracking-wider mb-2">Camera Location</label>
            <select
              value={selectedCamera}
              onChange={(e) => { setSelectedCamera(e.target.value); setCurrentPage(1); }}
              className="w-full bg-zinc-950 border border-zinc-800 focus:border-rose-500 rounded-lg px-3 py-2 text-xs outline-none text-zinc-300 transition-colors"
            >
              <option value="">All Cameras</option>
              {cameras.map(c => (
                <option key={c.id} value={c.id}>{c.zone_name} ({c.id})</option>
              ))}
            </select>
          </div>

          {/* Type Filter */}
          <div>
            <label className="block text-[10px] font-semibold text-zinc-500 uppercase tracking-wider mb-2">Violation Type</label>
            <select
              value={selectedType}
              onChange={(e) => { setSelectedType(e.target.value); setCurrentPage(1); }}
              className="w-full bg-zinc-950 border border-zinc-800 focus:border-rose-500 rounded-lg px-3 py-2 text-xs outline-none text-zinc-300 transition-colors"
            >
              <option value="">All Types</option>
              <option value="both_missing">Helmet & Vest Missing</option>
              <option value="helmet_missing">Helmet Missing</option>
              <option value="vest_missing">Vest Missing</option>
            </select>
          </div>

          {/* Shift Filter */}
          <div>
            <label className="block text-[10px] font-semibold text-zinc-500 uppercase tracking-wider mb-2">Shift Schedule</label>
            <select
              value={selectedShift}
              onChange={(e) => { setSelectedShift(e.target.value); setCurrentPage(1); }}
              className="w-full bg-zinc-950 border border-zinc-800 focus:border-rose-500 rounded-lg px-3 py-2 text-xs outline-none text-zinc-300 transition-colors"
            >
              <option value="">All Shifts</option>
              <option value="morning">Morning Shift</option>
              <option value="evening">Evening Shift</option>
              <option value="outside_shift">Off-Shift Hours</option>
            </select>
          </div>

          {/* Start Date */}
          <div>
            <label className="block text-[10px] font-semibold text-zinc-500 uppercase tracking-wider mb-2">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => { setStartDate(e.target.value); setCurrentPage(1); }}
              className="w-full bg-zinc-950 border border-zinc-800 focus:border-rose-500 rounded-lg px-3 py-1.5 text-xs outline-none text-zinc-300 transition-colors"
            />
          </div>

          {/* End Date */}
          <div>
            <label className="block text-[10px] font-semibold text-zinc-500 uppercase tracking-wider mb-2">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => { setEndDate(e.target.value); setCurrentPage(1); }}
              className="w-full bg-zinc-950 border border-zinc-800 focus:border-rose-500 rounded-lg px-3 py-1.5 text-xs outline-none text-zinc-300 transition-colors"
            />
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            onClick={resetFilters}
            className="text-xs text-zinc-400 hover:text-zinc-200 font-semibold"
          >
            Clear All Filters
          </button>
        </div>
      </div>

      {/* Logs Table */}
      <div className="glass-panel p-6 space-y-6">
        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center gap-3">
            <RefreshCw className="w-8 h-8 text-zinc-600 animate-spin" />
            <span className="text-zinc-500 text-xs font-semibold uppercase tracking-wider">Reloading logs...</span>
          </div>
        ) : violations.length === 0 ? (
          <div className="py-20 text-center text-zinc-500 text-sm">
            No violation entries match the current search filters.
          </div>
        ) : (
          <div className="space-y-4">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-zinc-900 text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                    <th className="py-3 px-4">Event ID</th>
                    <th className="py-3 px-4">Date & Time</th>
                    <th className="py-3 px-4">Camera / Zone</th>
                    <th className="py-3 px-4">Violation Type</th>
                    <th className="py-3 px-4">Confidence</th>
                    <th className="py-3 px-4">Shift</th>
                    <th className="py-3 px-4 text-center">Screenshot</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-900 text-sm text-zinc-300">
                  {currentItems.map((item) => (
                    <tr key={item.id} className="hover:bg-zinc-900/20 transition-colors">
                      <td className="py-3.5 px-4 font-mono text-zinc-400">#{item.id}</td>
                      <td className="py-3.5 px-4 font-mono text-xs">{formatTimestamp(item.timestamp)}</td>
                      <td className="py-3.5 px-4">
                        <span className="font-semibold text-zinc-200">{item.zone}</span>
                        <p className="text-[10px] text-zinc-500 font-mono mt-0.5">{item.camera_id}</p>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-semibold ${getBadgeClass(item.violation_type)}`}>
                          {getFriendlyType(item.violation_type)}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-mono text-xs">
                        {Math.round(item.confidence * 100)}%
                      </td>
                      <td className="py-3.5 px-4 uppercase text-[10px] font-semibold text-zinc-400 tracking-wider">
                        {item.shift}
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <div className="flex justify-center">
                          <button
                            onClick={() => setPreviewImage(getImageUrl(item.screenshot_url))}
                            className="p-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-rose-400 hover:text-rose-300 transition-all flex items-center gap-1.5 text-xs font-semibold"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>View</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="flex items-center justify-between border-t border-zinc-900 pt-4 text-xs font-semibold text-zinc-400 uppercase tracking-wider">
              <span>
                Showing {indexOfFirstItem + 1} to {Math.min(indexOfLastItem, violations.length)} of {violations.length} entries
              </span>

              <div className="flex items-center gap-2">
                <button
                  onClick={handlePrevPage}
                  disabled={currentPage === 1}
                  className="p-2 rounded bg-zinc-900 border border-zinc-800 disabled:bg-zinc-950 disabled:border-zinc-900 disabled:text-zinc-650 text-zinc-300 hover:text-zinc-100 transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="px-3">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  onClick={handleNextPage}
                  disabled={currentPage === totalPages}
                  className="p-2 rounded bg-zinc-900 border border-zinc-800 disabled:bg-zinc-950 disabled:border-zinc-900 disabled:text-zinc-650 text-zinc-300 hover:text-zinc-100 transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Preview Modal */}
      {previewImage && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="relative glass-panel bg-zinc-950 border-zinc-800 max-w-4xl w-full overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-zinc-900 bg-zinc-950/80 flex items-center justify-between">
              <span className="font-semibold text-sm text-zinc-200">Enlarged Evidence Image</span>
              <button 
                onClick={() => setPreviewImage(null)}
                className="p-1 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            
            <div className="aspect-video bg-black flex items-center justify-center p-2">
              <img 
                src={previewImage} 
                alt="Enlarged Violation" 
                className="max-h-[70vh] w-auto max-w-full object-contain rounded"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
