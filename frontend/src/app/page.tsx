"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from "recharts";
import { 
  Briefcase, 
  TrendingUp, 
  MapPin, 
  Layers, 
  FileText, 
  Compass, 
  MoreHorizontal, 
  Plus, 
  Image as ImageIcon,
  Calendar,
  MessageSquare,
  ThumbsUp,
  Share2,
  Send
} from "lucide-react";

interface OverviewData {
  total_jobs: number;
  average_salary_usd: number;
  remote_distribution: Array<{ remote_allowed: boolean | null; count: number }>;
  work_type_distribution: Array<{ work_type: string; formatted_work_type: string | null; count: number }>;
  experience_level_distribution: Array<{ formatted_experience_level: string | null; count: number }>;
  top_industries: Array<{ industry_id: number; industry_name: string; job_count: number }>;
  top_skills: Array<{ skill_abr: string; skill_name: string; job_count: number }>;
  data_source_distribution: Array<{ data_source: string; count: number }>;
}

const COLORS = ["#0a66c2", "#00a0dc", "#0073b1", "#33a0fc", "#70b5f9", "#b3dbff"];

export default function DashboardPage() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    fetch("http://127.0.0.1:8000/api/v1/dashboard/overview/")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch dashboard data");
        return res.json();
      })
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (!mounted) {
    return (
      <div className="flex-1 bg-[#f3f2f0] py-12 flex items-center justify-center">
        <div className="text-[#5e5e5e] text-sm">Loading workspace...</div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="w-full max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-5 animate-pulse">
        <div className="lg:col-span-3 space-y-4">
          <div className="h-64 bg-white border border-[#e0e0e0] rounded-lg" />
        </div>
        <div className="lg:col-span-6 space-y-4">
          <div className="h-28 bg-white border border-[#e0e0e0] rounded-lg" />
          <div className="h-96 bg-white border border-[#e0e0e0] rounded-lg" />
        </div>
        <div className="lg:col-span-3 space-y-4">
          <div className="h-80 bg-white border border-[#e0e0e0] rounded-lg" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex-1 py-16 flex flex-col items-center justify-center">
        <div className="bg-white border border-[#e0e0e0] p-8 rounded-lg text-center max-w-md shadow-sm">
          <h2 className="text-[#b24020] font-semibold text-lg mb-2">Failed to load Dashboard</h2>
          <p className="text-[#5e5e5e] text-sm mb-4">
            Could not retrieve data from the backend. Please confirm that the Django server is running.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-5 py-2 bg-[#0a66c2] hover:bg-[#004182] text-white rounded-full text-sm font-semibold transition-all shadow-sm"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  // Calculate calculations
  const remoteCount = data.remote_distribution.find((d) => d.remote_allowed === true)?.count || 0;
  const nonRemoteCount = data.remote_distribution.find((d) => d.remote_allowed === false)?.count || 0;
  const remoteRatio = data.total_jobs > 0 ? (remoteCount / data.total_jobs) * 100 : 0;

  const experienceData = data.experience_level_distribution.map((d) => ({
    name: d.formatted_experience_level || "Associate",
    value: d.count
  }));

  const workTypeData = data.work_type_distribution.map((d) => ({
    name: d.formatted_work_type || d.work_type || "Full-time",
    value: d.count
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
      {/* LEFT COLUMN: Profile / Navigation Summary */}
      <aside className="lg:col-span-3 space-y-3">
        {/* Profile Card Summary */}
        <div className="bg-white border border-[#e0e0e0] rounded-lg overflow-hidden shadow-sm">
          <div className="h-16 bg-[#a0b4b7] relative" />
          <div className="px-4 pb-4 text-center border-b border-[#e0e0e0]">
            <div className="-mt-8 mx-auto h-16 w-16 rounded-full bg-white border-2 border-white overflow-hidden shadow-sm flex items-center justify-center text-2xl font-bold text-[#0a66c2]">
              JI
            </div>
            <h2 className="text-base font-bold text-[#191919] mt-3">JobIntel Service</h2>
            <p className="text-xs text-[#5e5e5e] mt-0.5">Platform Analytics & Intelligence</p>
          </div>
          <div className="p-4 space-y-3 text-xs border-b border-[#e0e0e0]">
            <div className="flex justify-between items-center">
              <span className="text-[#5e5e5e]">Total Indexed Postings</span>
              <span className="font-bold text-[#0a66c2]">{data.total_jobs.toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-[#5e5e5e]">Avg Annual Salary</span>
              <span className="font-bold text-[#0a66c2]">
                ${data.average_salary_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}
              </span>
            </div>
          </div>
          <div className="p-3 bg-[#f9f9f9] text-center hover:bg-[#eaeaea] transition-all">
            <a href="/jobs" className="text-xs font-semibold text-[#0a66c2]">
              Search all listings
            </a>
          </div>
        </div>

        {/* Live Index Statistics Card */}
        <div className="bg-white border border-[#e0e0e0] rounded-lg p-4 shadow-sm space-y-3">
          <h3 className="text-xs font-bold text-[#191919]">JobIntel Resource Links</h3>
          <div className="space-y-2 text-xs">
            <a href="/jobs" className="flex items-center space-x-2 text-[#5e5e5e] hover:text-[#0a66c2] font-semibold py-1">
              <Briefcase className="h-4 w-4" />
              <span>Job Postings Feed</span>
            </a>
            <a href="/benchmarks" className="flex items-center space-x-2 text-[#5e5e5e] hover:text-[#0a66c2] font-semibold py-1">
              <TrendingUp className="h-4 w-4" />
              <span>Global Benchmarks</span>
            </a>
          </div>
        </div>
      </aside>

      {/* MIDDLE COLUMN: Feed & Dashboard Charts */}
      <section className="lg:col-span-6 space-y-4">
        {/* Mock Share Feed Post Box */}
        <div className="bg-white border border-[#e0e0e0] rounded-lg p-4 shadow-sm space-y-3">
          <div className="flex items-center space-x-2">
            <div className="h-9 w-9 rounded-full bg-[#e0e0e0] flex items-center justify-center font-bold text-[#5e5e5e] text-xs">
              JI
            </div>
            <a
              href="/jobs"
              className="flex-1 bg-white border border-[#808080] hover:bg-[#f3f2f0] rounded-full px-4 py-2.5 text-xs font-semibold text-[#5e5e5e] text-left transition-colors"
            >
              Search 120k+ job market listings now...
            </a>
          </div>
          <div className="flex justify-between items-center text-[#5e5e5e] text-xs pt-1 font-semibold px-1">
            <div className="flex items-center space-x-2 hover:bg-[#f3f2f0] p-2 rounded cursor-pointer">
              <Compass className="h-5 w-5 text-[#378fe9]" />
              <span>Explore Analytics</span>
            </div>
            <div className="flex items-center space-x-2 hover:bg-[#f3f2f0] p-2 rounded cursor-pointer">
              <Layers className="h-5 w-5 text-[#5f9b41]" />
              <span>Filter Skills</span>
            </div>
            <div className="flex items-center space-x-2 hover:bg-[#f3f2f0] p-2 rounded cursor-pointer">
              <FileText className="h-5 w-5 text-[#e7a33c]" />
              <span>Salary Stats</span>
            </div>
          </div>
        </div>

        {/* FEED CARD 1: Top Hiring Industries (Recharts BarChart) */}
        <div className="bg-white border border-[#e0e0e0] rounded-lg shadow-sm">
          <div className="p-4 flex justify-between items-start">
            <div className="flex space-x-2">
              <div className="h-10 w-10 rounded bg-[#0a66c2] flex items-center justify-center font-bold text-lg text-white">
                JI
              </div>
              <div>
                <h3 className="text-sm font-bold text-[#191919]">JobIntel Platform Insight</h3>
                <p className="text-[11px] text-[#5e5e5e]">Aggregate Industry Demand Indexes • Just now</p>
              </div>
            </div>
            <button className="text-[#5e5e5e] hover:text-[#191919] p-1 rounded-full hover:bg-[#f3f2f0] transition-colors">
              <MoreHorizontal className="h-5 w-5" />
            </button>
          </div>
          <div className="px-4 pb-2 text-xs text-[#191919] leading-relaxed">
            Here are the top hiring sectors based on our total indexed job posting entries. The business services, tech, and engineering sectors show the highest job posting density.
          </div>
          <div className="p-4 border-t border-[#f3f2f0] min-w-0">
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                <BarChart data={data.top_industries} margin={{ bottom: 20 }}>
                  <XAxis dataKey="industry_name" stroke="#5e5e5e" fontSize={10} tickLine={false} axisLine={false} angle={-20} textAnchor="end" interval={0} />
                  <YAxis stroke="#5e5e5e" fontSize={10} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e0e0e0", borderRadius: "4px", fontSize: "11px" }} />
                  <Bar dataKey="job_count" fill="#0a66c2" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* FEED CARD 2: Mapped Skills Demand (Recharts BarChart) */}
        <div className="bg-white border border-[#e0e0e0] rounded-lg shadow-sm">
          <div className="p-4 flex justify-between items-start">
            <div className="flex space-x-2">
              <div className="h-10 w-10 rounded bg-[#00a0dc] flex items-center justify-center font-bold text-lg text-white">
                JS
              </div>
              <div>
                <h3 className="text-sm font-bold text-[#191919]">Technical Skills Demand Matrix</h3>
                <p className="text-[11px] text-[#5e5e5e]">Skills Frequency Index • Calculated live</p>
              </div>
            </div>
            <button className="text-[#5e5e5e] hover:text-[#191919] p-1 rounded-full hover:bg-[#f3f2f0] transition-colors">
              <MoreHorizontal className="h-5 w-5" />
            </button>
          </div>
          <div className="px-4 pb-2 text-xs text-[#191919] leading-relaxed">
            This graph highlights the relative frequency of technical skills requested across all job descriptions. Core languages like Python, SQL, and AWS infrastructure command the highest representation.
          </div>
          <div className="p-4 border-t border-[#f3f2f0] min-w-0">
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                <BarChart data={data.top_skills} layout="vertical" margin={{ left: 10 }}>
                  <XAxis type="number" stroke="#5e5e5e" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis dataKey="skill_name" type="category" stroke="#5e5e5e" fontSize={10} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e0e0e0", borderRadius: "4px", fontSize: "11px" }} />
                  <Bar dataKey="job_count" fill="#00a0dc" radius={[0, 3, 3, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* FEED CARD 3: Allocation Splits (Pie Charts) */}
        <div className="bg-white border border-[#e0e0e0] rounded-lg shadow-sm p-4 space-y-4">
          <h3 className="text-sm font-bold text-[#191919] pb-3 border-b border-[#f3f2f0]">Job Market Allocation Splits</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Experience Level */}
            <div className="flex flex-col items-center">
              <p className="text-xs font-semibold text-[#5e5e5e] mb-2 self-start">Experience Allocation</p>
              {experienceData.length > 0 ? (
                <div className="h-48 w-full">
                  <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                    <PieChart>
                      <Pie data={experienceData} innerRadius={45} outerRadius={60} paddingAngle={3} dataKey="value">
                        {experienceData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: "10px" }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="text-xs text-[#5e5e5e] py-16">No data</p>
              )}
            </div>

            {/* Work Type */}
            <div className="flex flex-col items-center">
              <p className="text-xs font-semibold text-[#5e5e5e] mb-2 self-start">Work Type Allocation</p>
              {workTypeData.length > 0 ? (
                <div className="h-48 w-full">
                  <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                    <PieChart>
                      <Pie data={workTypeData} innerRadius={45} outerRadius={60} paddingAngle={3} dataKey="value">
                        {workTypeData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[(index + 2) % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: "10px" }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="text-xs text-[#5e5e5e] py-16">No data</p>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* RIGHT COLUMN: Trending Stats / News Widget */}
      <aside className="lg:col-span-3 space-y-3">
        {/* Remote Ratio Stat Box */}
        <div className="bg-white border border-[#e0e0e0] rounded-lg p-4 shadow-sm">
          <h3 className="text-xs font-bold text-[#191919] mb-3">Remote Operations index</h3>
          <div className="space-y-2">
            <div className="flex justify-between items-baseline">
              <span className="text-2xl font-bold text-[#0a66c2]">{remoteRatio.toFixed(1)}%</span>
              <span className="text-[10px] text-[#5e5e5e] font-semibold uppercase tracking-wider">Remote Allowed</span>
            </div>
            <div className="h-1.5 w-full bg-[#f3f2f0] rounded-full overflow-hidden">
              <div className="h-full bg-[#0a66c2] rounded-full" style={{ width: `${remoteRatio}%` }} />
            </div>
            <p className="text-[11px] text-[#5e5e5e] mt-1">
              Based on {remoteCount.toLocaleString()} remote listings out of {data.total_jobs.toLocaleString()} total postings.
            </p>
          </div>
        </div>

        {/* Data Source Splitting Widget */}
        <div className="bg-white border border-[#e0e0e0] rounded-lg p-4 shadow-sm space-y-3">
          <h3 className="text-xs font-bold text-[#191919] border-b border-[#f3f2f0] pb-2">Data Ingestion Splitting</h3>
          <div className="space-y-3">
            {data.data_source_distribution.map((source) => {
              const percentage = data.total_jobs > 0 ? (source.count / data.total_jobs) * 100 : 0;
              return (
                <div key={source.data_source} className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-[#191919]">{source.data_source} Source</span>
                    <span className="text-[#5e5e5e]">{percentage.toFixed(1)}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-[#f3f2f0] rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        backgroundColor: source.data_source === "CSV" ? "#0a66c2" : "#00a0dc",
                        width: `${percentage}%`
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </aside>
    </div>
  );
}
