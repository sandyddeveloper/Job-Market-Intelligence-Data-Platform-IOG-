import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Job Intelligence Market Platform",
  description: "Advanced dashboard to analyze job postings, salary trends, and hiring benchmarks.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased dark`}>
      <body className="min-h-full flex bg-slate-950 text-slate-100 font-sans">
        {/* Navigation Sidebar */}
        <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between shrink-0">
          <div>
            {/* Logo area */}
            <div className="p-6 border-b border-slate-800 flex items-center space-x-3">
              <div className="h-8 w-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-lg text-white shadow-md shadow-indigo-500/20">
                J
              </div>
              <span className="font-bold text-lg tracking-wide bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                JobIntel Platform
              </span>
            </div>

            {/* Nav links */}
            <nav className="p-4 space-y-1">
              <Link
                href="/"
                className="flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-slate-300 hover:text-white hover:bg-slate-800/60"
              >
                <span>📊 Dashboard Overview</span>
              </Link>
              <Link
                href="/jobs"
                className="flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-slate-300 hover:text-white hover:bg-slate-800/60"
              >
                <span>💼 Job Search Portal</span>
              </Link>
              <Link
                href="/benchmarks"
                className="flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-slate-300 hover:text-white hover:bg-slate-800/60"
              >
                <span>📈 Salary Benchmarks</span>
              </Link>
            </nav>
          </div>

          {/* Footer info */}
          <div className="p-4 border-t border-slate-800">
            <div className="flex items-center space-x-3 bg-slate-950/60 p-3 rounded-lg border border-slate-800/50">
              <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <div className="text-xs">
                <p className="font-medium text-slate-300">Django API Connection</p>
                <p className="text-slate-500">Live Status: Active</p>
              </div>
            </div>
          </div>
        </aside>

        {/* Content workspace */}
        <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          {children}
        </main>
      </body>
    </html>
  );
}
