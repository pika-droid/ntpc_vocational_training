"use client";

import { useEffect, useState } from "react";
import { getApiBaseUrl } from "@/utils/api";
import { Camera, Radio, Tv, AlertTriangle, Play, Pause } from "lucide-react";

interface CameraConfig {
  id: string;
  rtsp_url: string;
  zone_name: string;
  is_online: boolean;
  last_seen: string | null;
}

export default function LiveStreamsPage() {
  const [cameras, setCameras] = useState<CameraConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFeeds, setActiveFeeds] = useState<{ [key: string]: boolean }>({});

  const fetchCameras = async () => {
    try {
      const apiBase = getApiBaseUrl();
      const res = await fetch(`${apiBase}/api/cameras`);
      if (!res.ok) throw new Error("Failed to fetch camera configurations");
      const data = await res.ok ? await res.json() : [];
      setCameras(data);
      
      // Initialize active feed state for newly discovered cameras
      setActiveFeeds(prev => {
        const next = { ...prev };
        data.forEach((cam: CameraConfig) => {
          if (next[cam.id] === undefined) {
            next[cam.id] = true; // Enabled by default
          }
        });
        return next;
      });
      
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Failed to connect to the backend server");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCameras();
    // Poll every 3 seconds for active camera configuration and online status updates
    const interval = setInterval(fetchCameras, 3000);
    return () => clearInterval(interval);
  }, []);

  const toggleFeed = (id: string) => {
    setActiveFeeds(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const activeCamsCount = cameras.filter(c => c.is_online).length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-zinc-100">Live Video Streams</h2>
          <p className="text-sm text-zinc-400">
            Real-time feed monitoring for safety compliance gate entries.
          </p>
        </div>
        
        <div className="flex items-center gap-3 bg-zinc-900 border border-zinc-800 px-4 py-2 rounded-lg">
          <Radio className="w-5 h-5 text-rose-500 animate-pulse" />
          <div className="text-xs">
            <span className="font-semibold text-zinc-200">
              {activeCamsCount} / {cameras.length}
            </span>
            <span className="text-zinc-500 ml-1">Cameras Online</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center gap-3 text-sm">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <div>
            <span className="font-semibold">Backend offline:</span> Make sure your FastAPI backend is running. (Connecting to {getApiBaseUrl()})
          </div>
        </div>
      )}

      {loading && cameras.length === 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2].map((i) => (
            <div key={i} className="h-80 rounded-xl bg-zinc-900/40 border border-zinc-850 animate-pulse" />
          ))}
        </div>
      ) : cameras.length === 0 ? (
        <div className="glass-panel p-16 text-center max-w-xl mx-auto space-y-4">
          <div className="w-12 h-12 bg-zinc-900 border border-zinc-800 text-zinc-500 rounded-lg flex items-center justify-center mx-auto">
            <Tv className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-zinc-200">No Cameras Configured</h3>
            <p className="text-xs text-zinc-400">
              Go to the Camera Config page to add RTSP streams.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {cameras.map((camera) => {
            const isFeedActive = activeFeeds[camera.id];
            
            return (
              <div 
                key={camera.id} 
                className={`glass-panel overflow-hidden flex flex-col ${
                  camera.is_online ? "border-zinc-805" : "border-red-950/20"
                }`}
              >
                {/* Header */}
                <div className="p-4 border-b border-zinc-900 bg-zinc-950/50 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-zinc-900 border border-zinc-800 rounded-lg text-zinc-400">
                      <Camera className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-zinc-200 text-sm">{camera.zone_name}</h3>
                      <p className="text-[10px] text-zinc-500 font-mono">{camera.id} • {camera.rtsp_url}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    {/* Active/Offline Badge */}
                    <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[10px] font-semibold ${
                      camera.is_online
                        ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                        : "bg-red-500/10 border-red-500/20 text-red-400"
                    }`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${
                        camera.is_online ? "bg-emerald-400 animate-pulse" : "bg-red-400"
                      }`} />
                      <span>{camera.is_online ? "Active" : "Offline"}</span>
                    </div>

                    {/* Stream Pause/Play */}
                    <button
                      onClick={() => toggleFeed(camera.id)}
                      className="p-1.5 rounded-md hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
                      title={isFeedActive ? "Pause Stream" : "Resume Stream"}
                    >
                      {isFeedActive ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Video Container */}
                <div className="relative aspect-video bg-black flex items-center justify-center overflow-hidden">
                  {isFeedActive ? (
                    <img
                      src={`${getApiBaseUrl()}/api/cameras/${camera.id}/stream`}
                      alt={`${camera.zone_name} Live Stream`}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        // If feed loading error occurs, fallback to showing offline message
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  ) : (
                    <div className="text-center space-y-2">
                      <Tv className="w-8 h-8 text-zinc-600 mx-auto" />
                      <p className="text-xs text-zinc-500">Stream paused by supervisor</p>
                    </div>
                  )}

                  {/* Offline Overlay if backend tells us camera is down */}
                  {!camera.is_online && (
                    <div className="absolute inset-0 bg-zinc-950/80 backdrop-blur-sm flex flex-col items-center justify-center p-4 text-center">
                      <div className="w-10 h-10 rounded-full bg-red-500/10 border border-red-500/20 text-red-500 flex items-center justify-center mb-3 glow-rose">
                        <AlertTriangle className="w-5 h-5" />
                      </div>
                      <h4 className="text-sm font-semibold text-zinc-200">Camera Feed Unavailable</h4>
                      <p className="text-[11px] text-zinc-400 max-w-xs mt-1">
                        Check that the IP Webcam app is running on the phone and MediaMTX is receiving the stream.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
