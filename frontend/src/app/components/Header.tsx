"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Briefcase, TrendingUp, Search } from "lucide-react";

export default function Header() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 w-full bg-white border-b border-[#e0e0e0] shadow-sm">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        {/* Left section: Logo & Search Box */}
        <div className="flex items-center space-x-3 flex-1">
          <Link href="/" className="flex items-center space-x-2 shrink-0 group">
            <div className="h-9 w-9 rounded-[4px] bg-[#0a66c2] flex items-center justify-center font-bold text-xl text-white tracking-tighter">
              JI
            </div>
            <span className="font-bold text-lg text-[#0a66c2] hidden md:inline-block tracking-tight">
              JobIntel
            </span>
          </Link>
          <div className="max-w-xs w-full hidden sm:block relative">
            <input
              type="text"
              placeholder="Search jobs, skills, salaries..."
              className="w-full bg-[#edf3f8] hover:bg-[#e4ebf2] text-sm text-[#191919] placeholder-[#5e5e5e] border border-transparent rounded-[4px] py-1.5 pl-9 pr-3 focus:outline-none focus:bg-white focus:border-[#0a66c2] focus:ring-1 focus:ring-[#0a66c2] transition-all"
              disabled
            />
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-[#5e5e5e]" />
          </div>
        </div>

        {/* Right section: Navigation Menu Items */}
        <nav className="flex items-center space-x-1 sm:space-x-4">
          <Link
            href="/"
            className={`flex flex-col items-center justify-center px-3 h-14 border-b-2 transition-all group ${
              pathname === "/"
                ? "border-[#191919] text-[#191919]"
                : "border-transparent text-[#5e5e5e] hover:text-[#191919]"
            }`}
          >
            <Home className="h-5.5 w-5.5" />
            <span className="text-[10px] sm:text-[11px] font-normal mt-0.5 hidden sm:inline">Home</span>
          </Link>
          <Link
            href="/jobs"
            className={`flex flex-col items-center justify-center px-3 h-14 border-b-2 transition-all group ${
              pathname === "/jobs"
                ? "border-[#191919] text-[#191919]"
                : "border-transparent text-[#5e5e5e] hover:text-[#191919]"
            }`}
          >
            <Briefcase className="h-5.5 w-5.5" />
            <span className="text-[10px] sm:text-[11px] font-normal mt-0.5 hidden sm:inline">Jobs</span>
          </Link>
          <Link
            href="/benchmarks"
            className={`flex flex-col items-center justify-center px-3 h-14 border-b-2 transition-all group ${
              pathname === "/benchmarks"
                ? "border-[#191919] text-[#191919]"
                : "border-transparent text-[#5e5e5e] hover:text-[#191919]"
            }`}
          >
            <TrendingUp className="h-5.5 w-5.5" />
            <span className="text-[10px] sm:text-[11px] font-normal mt-0.5 hidden sm:inline">Salaries</span>
          </Link>
          
          <div className="h-8 w-[1px] bg-[#e0e0e0] mx-2 hidden sm:block" />
          
          {/* Connection Status Profile Widget */}
          <div className="flex items-center space-x-2 pl-2">
            <div className="relative h-9 w-9 rounded-full bg-[#e0e0e0] border border-[#d0d0d0] flex items-center justify-center font-bold text-[#5e5e5e] text-sm shadow-inner cursor-default">
              JD
              <span className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full bg-emerald-600 border border-white animate-pulse" />
            </div>
            <div className="hidden lg:block text-left">
              <p className="text-[11px] font-semibold text-[#191919] leading-tight">Django Service</p>
              <p className="text-[9px] text-[#5e5e5e] leading-none">Live Connection</p>
            </div>
          </div>
        </nav>
      </div>
    </header>
  );
}
