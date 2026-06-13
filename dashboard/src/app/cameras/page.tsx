"use client";

import { useState, useEffect } from "react";
import { getApiBaseUrl } from "@/utils/api";
import { 
  Camera, 
  Plus, 
  Trash2, 
  Check, 
  AlertCircle, 
  ShieldAlert, 
  RefreshCw 
} from "lucide-react";

interface CameraConfig {
  id: string;
  rtsp_url: string;
  zone_name: string;
  is_online: boolean;
  last_seen: string | null;
}

export default function CameraConfigPage() {
  const [cameras, setCameras] = useState<CameraConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form states
  const [formId, setFormId] = useState("");
  const [formRtsp, setFormRtsp] = useState("");
  const [formZone, setFormZone] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);

  const fetchCameras = async () => {
    try {
      const apiBase = getApiBaseUrl();
      const res = await fetch(`${apiBase}/api/cameras`);
      if (!res.ok) throw new Error("Failed to fetch camera configurations");
      const data = await res.json();
      setCameras(data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to load cameras");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCameras();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setFormSuccess(null);

    // Basic Validation
    if (!formId.trim()) return setFormError("Camera ID is required");
    if (!formRtsp.trim()) return setFormError("RTSP URL or stream index is required");
    if (!formZone.trim()) return setFormError("Zone/Location name is required");

    setSubmitting(true);
    try {
      const apiBase = getApiBaseUrl();
      const res = await fetch(`${apiBase}/api/cameras`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: formId.trim(),
          rtsp_url: formRtsp.trim(),
          zone_name: formZone.trim()
        })
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to upsert camera");
      }

      setFormSuccess(`Camera '${formId}' saved successfully!`);
      // Reset form fields
      setFormId("");
      setFormRtsp("");
      setFormZone("");
      // Refresh list
      fetchCameras();
    } catch (err: any) {
      setFormError(err.message || "Error submitting form");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm(`Are you sure you want to delete camera '${id}'?`)) return;

    try {
      const apiBase = getApiBaseUrl();
      const res = await fetch(`${apiBase}/api/cameras/${id}`, {
        method: "DELETE"
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to delete camera");
      }

      // Refresh list
      fetchCameras();
    } catch (err: any) {
      alert(err.message || "Error deleting camera");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-zinc-100">Camera Configuration</h2>
        <p className="text-sm text-zinc-400">
          Manage entry gate stream sources, RTSP endpoints, and monitored physical zones.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Form Panel */}
        <div className="lg:col-span-1">
          <div className="glass-panel p-6 space-y-6 bg-zinc-900/20">
            <div className="flex items-center gap-2 pb-3 border-b border-zinc-900">
              <Plus className="w-5 h-5 text-rose-500" />
              <h3 className="font-semibold text-zinc-200 text-sm">Add / Update Camera</h3>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
                  Camera ID (must be unique)
                </label>
                <input
                  type="text"
                  placeholder="e.g. cam_3"
                  value={formId}
                  onChange={(e) => setFormId(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 focus:border-rose-500 rounded-lg px-4 py-2.5 text-sm outline-none transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
                  RTSP Stream URL (or WebCam index)
                </label>
                <input
                  type="text"
                  placeholder="rtsp://admin:pass@192.168.1.50:554/h264"
                  value={formRtsp}
                  onChange={(e) => setFormRtsp(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 focus:border-rose-500 rounded-lg px-4 py-2.5 text-sm outline-none transition-colors font-mono text-xs"
                />
                <p className="text-[10px] text-zinc-500 mt-1">
                  For local webcams, use stream index (e.g. <code className="bg-zinc-900 px-1 py-0.5 rounded">0</code> or <code className="bg-zinc-900 px-1 py-0.5 rounded">1</code>)
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
                  Zone / Location Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Gate 3 Ingestion"
                  value={formZone}
                  onChange={(e) => setFormZone(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 focus:border-rose-500 rounded-lg px-4 py-2.5 text-sm outline-none transition-colors"
                />
              </div>

              {formError && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center gap-2 text-xs">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{formError}</span>
                </div>
              )}

              {formSuccess && (
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center gap-2 text-xs">
                  <Check className="w-4 h-4 shrink-0" />
                  <span>{formSuccess}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-rose-600 hover:bg-rose-500 disabled:bg-rose-800 text-white font-medium text-sm py-2.5 px-4 rounded-lg transition-colors flex items-center justify-center gap-2 shadow-lg shadow-rose-950/10"
              >
                {submitting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <span>Save Camera</span>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* List Panel */}
        <div className="lg:col-span-2">
          <div className="glass-panel p-6 space-y-6">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-900">
              <div className="flex items-center gap-2">
                <Camera className="w-5 h-5 text-rose-500" />
                <h3 className="font-semibold text-zinc-200 text-sm">Configured Streams</h3>
              </div>
              <button 
                onClick={fetchCameras}
                className="text-zinc-500 hover:text-zinc-300 transition-colors"
                title="Refresh Table"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>

            {loading ? (
              <div className="py-12 flex justify-center">
                <RefreshCw className="w-8 h-8 text-zinc-600 animate-spin" />
              </div>
            ) : error ? (
              <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center gap-3 text-sm">
                <ShieldAlert className="w-5 h-5" />
                <div>
                  <span className="font-semibold">Error loading cameras:</span> {error}
                </div>
              </div>
            ) : cameras.length === 0 ? (
              <div className="py-16 text-center text-zinc-500 text-sm">
                No cameras currently registered in database.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-zinc-900 text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                      <th className="py-3 px-4">ID</th>
                      <th className="py-3 px-4">Zone / Location</th>
                      <th className="py-3 px-4">Stream URL / Index</th>
                      <th className="py-3 px-4">Pipeline Status</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-900 text-sm text-zinc-300">
                    {cameras.map((camera) => (
                      <tr key={camera.id} className="hover:bg-zinc-900/30 transition-colors">
                        <td className="py-3.5 px-4 font-mono font-semibold text-zinc-200">
                          {camera.id}
                        </td>
                        <td className="py-3.5 px-4">
                          {camera.zone_name}
                        </td>
                        <td className="py-3.5 px-4 font-mono text-xs text-zinc-400 max-w-[200px] truncate" title={camera.rtsp_url}>
                          {camera.rtsp_url}
                        </td>
                        <td className="py-3.5 px-4">
                          <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[10px] font-semibold ${
                            camera.is_online 
                              ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                              : "bg-red-500/10 border-red-500/20 text-red-400"
                          }`}>
                            <span className={`w-1 h-1 rounded-full ${camera.is_online ? "bg-emerald-400" : "bg-red-400"}`} />
                            <span>{camera.is_online ? "Active" : "Offline"}</span>
                          </div>
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            onClick={() => {
                              // Load into form to update
                              setFormId(camera.id);
                              setFormRtsp(camera.rtsp_url);
                              setFormZone(camera.zone_name);
                              setFormSuccess(null);
                            }}
                            className="text-xs text-rose-400 hover:text-rose-300 mr-4 font-medium"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(camera.id)}
                            className="text-zinc-500 hover:text-red-400 transition-colors"
                            title="Delete Camera"
                          >
                            <Trash2 className="w-4 h-4 inline" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
