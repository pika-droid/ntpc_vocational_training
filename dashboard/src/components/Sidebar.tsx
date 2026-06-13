"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  Video, 
  ClipboardList, 
  BarChart3, 
  Camera, 
  ShieldAlert 
} from "lucide-react";

export default function Sidebar() {
  const pathname = usePathname();

  const menuItems = [
    { name: "Overview", path: "/", icon: LayoutDashboard },
    { name: "Live Streams", path: "/live", icon: Video },
    { name: "Violation Logs", path: "/logs", icon: ClipboardList },
    { name: "Compliance Analytics", path: "/analytics", icon: BarChart3 },
    { name: "Camera Config", path: "/cameras", icon: Camera },
  ];

  return (
    <aside className="w-64 border-r border-zinc-800 bg-zinc-950 flex flex-col justify-between shrink-0 h-screen sticky top-0">
      <div className="flex flex-col">
        {/* Brand Header */}
        <div className="h-16 flex items-center gap-3 px-6 border-b border-zinc-900 bg-zinc-950">
          <div className="p-2 bg-rose-500/10 rounded-lg text-rose-500">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-semibold text-zinc-100 tracking-tight text-sm">NTPC Safety Portal</h1>
            <p className="text-[10px] text-zinc-400 font-medium tracking-wider uppercase">PPE Compliance PoC</p>
          </div>
        </div>

        {/* Menu Items */}
        <nav className="flex-1 px-4 py-6 space-y-1.5">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.path;

            return (
              <Link
                key={item.name}
                href={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 group relative ${
                  isActive
                    ? "bg-rose-500/10 text-rose-400 border-l-2 border-rose-500 rounded-l-none"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/60"
                }`}
              >
                <Icon className={`w-5 h-5 shrink-0 transition-transform duration-200 group-hover:scale-105 ${
                  isActive ? "text-rose-400" : "text-zinc-400 group-hover:text-zinc-300"
                }`} />
                <span>{item.name}</span>
                {isActive && (
                  <span className="absolute right-3 w-1.5 h-1.5 rounded-full bg-rose-500 glow-rose" />
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-zinc-900 bg-zinc-950/50">
        <div className="flex items-center gap-3 p-3 rounded-lg bg-zinc-900/40 border border-zinc-900">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse glow-emerald" />
          <div className="text-[11px]">
            <p className="font-medium text-zinc-300">System Pipeline</p>
            <p className="text-zinc-500">Monitoring Active</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
