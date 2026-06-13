import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Sidebar from "@/components/Sidebar";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "NTPC PPE Compliance Dashboard",
  description: "AI-based multi-camera safety compliance and violation tracking system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
    >
      <body className="min-h-full flex bg-zinc-950 text-zinc-100 antialiased overflow-hidden">
        <Sidebar />
        <main className="flex-1 flex flex-col h-screen overflow-y-auto custom-scrollbar bg-zinc-950">
          <header className="h-16 border-b border-zinc-900 flex items-center justify-between px-8 bg-zinc-950 shrink-0 sticky top-0 z-10 backdrop-blur-md bg-zinc-950/80">
            <div className="flex items-center gap-4">
              <span className="text-zinc-500 text-sm">Location:</span>
              <span className="font-semibold text-sm bg-zinc-900 border border-zinc-800 px-3 py-1 rounded-full text-zinc-300">
                Gate Entry & Logistics
              </span>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex flex-col text-right">
                <span className="text-xs font-semibold text-zinc-300">Shift Supervisor</span>
                <span className="text-[10px] text-zinc-500">Logistics Gate PoC</span>
              </div>
              <div className="w-8 h-8 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center font-bold text-xs text-rose-400">
                N
              </div>
            </div>
          </header>
          <div className="flex-1 p-8">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
