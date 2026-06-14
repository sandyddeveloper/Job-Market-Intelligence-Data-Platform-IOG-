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
  Legend,
  AreaChart,
  Area
} from "recharts";

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

const COLORS = ["#6366f1", "#a855f7", "#ec4899", "#10b981", "#f59e0b", "#3b82f6"];

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
      <div className="flex-1 bg-slate-950 p-8 flex items-center justify-center">
        <div className="text-slate-400">Loading workspace...</div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex-1 bg-slate-950 p-8 space-y-6">
        <header className="flex justify-between items-center pb-4 border-b border-slate-800">
          <div className="h-8 w-64 bg-slate-800 rounded animate-pulse" />
        </header>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-slate-900 border border-slate-800 rounded-xl animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-96 bg-slate-900 border border-slate-800 rounded-xl animate-pulse" />
          <div className="h-96 bg-slate-900 border border-slate-800 rounded-xl animate-pulse" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex-1 bg-slate-950 p-8 flex flex-col items-center justify-center">
        <div className="bg-red-500/10 border border-red-500/20 p-6 rounded-xl text-center max-w-md">
          <h2 className="text-red-400 font-semibold text-lg mb-2">Failed to load Dashboard</h2>
          <p className="text-slate-400 text-sm mb-4">
            Could not retrieve data from the backend. Please confirm that the Django server is running.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  // Process Stats calculations
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
    <div className="p-8 space-y-8 bg-slate-950 min-h-screen">
      {/* Header bar */}
      <header className="flex flex-col md:flex-row justify-between md:items-center gap-4 pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
            Market Intelligence Overview
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Real-time analytics and parsing indexes collected from processed job files and Adzuna APIs.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="px-3 py-1 bg-slate-800 text-indigo-400 rounded-full border border-slate-700 text-xs font-semibold">
            Data Source: CSV & API
          </span>
        </div>
      </header>

      {/* KPI Cards Grid */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl relative overflow-hidden transition-all duration-300 hover:border-indigo-500/50 hover:shadow-indigo-500/5 group">
          <div className="absolute top-0 right-0 h-24 w-24 bg-indigo-500/5 rounded-full blur-xl transition-all group-hover:bg-indigo-500/10" />
          <p className="text-sm font-medium text-slate-400">Total Indexed Postings</p>
          <p className="text-3xl font-bold mt-2 text-white">{data.total_jobs.toLocaleString()}</p>
          <div className="mt-2 text-xs text-indigo-400 flex items-center gap-1">
            <span>Live indexed data entries</span>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl relative overflow-hidden transition-all duration-300 hover:border-purple-500/50 hover:shadow-purple-500/5 group">
          <div className="absolute top-0 right-0 h-24 w-24 bg-purple-500/5 rounded-full blur-xl transition-all group-hover:bg-purple-500/10" />
          <p className="text-sm font-medium text-slate-400">Average Annual Salary</p>
          <p className="text-3xl font-bold mt-2 text-white">
            ${data.average_salary_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </p>
          <div className="mt-2 text-xs text-purple-400">Normalized equivalent in USD</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl relative overflow-hidden transition-all duration-300 hover:border-emerald-500/50 hover:shadow-emerald-500/5 group">
          <div className="absolute top-0 right-0 h-24 w-24 bg-emerald-500/5 rounded-full blur-xl transition-all group-hover:bg-emerald-500/10" />
          <p className="text-sm font-medium text-slate-400">Remote Work Ratio</p>
          <p className="text-3xl font-bold mt-2 text-white">{remoteRatio.toFixed(1)}%</p>
          <div className="mt-2 text-xs text-emerald-400">
            {remoteCount} remote / {nonRemoteCount} on-site
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl relative overflow-hidden transition-all duration-300 hover:border-pink-500/50 hover:shadow-pink-500/5 group">
          <div className="absolute top-0 right-0 h-24 w-24 bg-pink-500/5 rounded-full blur-xl transition-all group-hover:bg-pink-500/10" />
          <p className="text-sm font-medium text-slate-400">Technical Skills Index</p>
          <p className="text-3xl font-bold mt-2 text-white">{data.top_skills.length}</p>
          <div className="mt-2 text-xs text-pink-400">Mapped skill classifications</div>
        </div>
      </section>

      {/* Main Charts area */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Top Industries */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl min-w-0">
          <h3 className="text-lg font-semibold text-white mb-4">Top 6 Hiring Industries</h3>
          <div className="h-80 w-full min-w-0">
            <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
              <BarChart data={data.top_industries} margin={{ bottom: 20 }}>
                <XAxis dataKey="industry_name" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} angle={-25} textAnchor="end" interval={0} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px" }} labelClassName="text-white" />
                <Bar dataKey="job_count" fill="url(#colorIndigo)" radius={[4, 4, 0, 0]}>
                  {data.top_industries.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
                <defs>
                  <linearGradient id="colorIndigo" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#4f46e5" stopOpacity={0.2} />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Mapped Skills Demand */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl min-w-0">
          <h3 className="text-lg font-semibold text-white mb-4">Top 10 Mapped Skills Demand</h3>
          <div className="h-80 w-full min-w-0">
            <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
              <BarChart data={data.top_skills} layout="vertical" margin={{ left: 20 }}>
                <XAxis type="number" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis dataKey="skill_name" type="category" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px" }} labelClassName="text-white" />
                <Bar dataKey="job_count" fill="#a855f7" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      {/* Sub Distributions area */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Experience Levels */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex flex-col items-center min-w-0">
          <h3 className="text-md font-semibold text-white mb-4 w-full text-left">Experience Level Allocation</h3>
          {experienceData.length > 0 ? (
            <div className="h-64 w-full flex items-center justify-center min-w-0">
              <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                <PieChart>
                  <Pie data={experienceData} innerRadius={60} outerRadius={80} paddingAngle={4} dataKey="value">
                    {experienceData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px" }} />
                  <Legend verticalAlign="bottom" height={36} iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="text-slate-500 text-sm py-20">No experience level data available.</div>
          )}
        </div>

        {/* Work Types */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex flex-col items-center min-w-0">
          <h3 className="text-md font-semibold text-white mb-4 w-full text-left">Work Types Distribution</h3>
          {workTypeData.length > 0 ? (
            <div className="h-64 w-full flex items-center justify-center min-w-0">
              <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                <PieChart>
                  <Pie data={workTypeData} innerRadius={60} outerRadius={80} paddingAngle={4} dataKey="value">
                    {workTypeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[(index + 3) % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px" }} />
                  <Legend verticalAlign="bottom" height={36} iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="text-slate-500 text-sm py-20">No work type data available.</div>
          )}
        </div>


        {/* Data Ingestion Splitting */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex flex-col">
          <h3 className="text-md font-semibold text-white mb-4">Ingestion Data Splitting</h3>
          <div className="flex-1 flex flex-col justify-center space-y-4">
            {data.data_source_distribution.map((source, index) => {
              const percentage = data.total_jobs > 0 ? (source.count / data.total_jobs) * 100 : 0;
              return (
                <div key={source.data_source} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="font-semibold text-slate-300">{source.data_source} Dataset</span>
                    <span className="text-slate-400">
                      {source.count.toLocaleString()} jobs ({percentage.toFixed(1)}%)
                    </span>
                  </div>
                  <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        backgroundColor: source.data_source === "CSV" ? "#6366f1" : "#10b981",
                        width: `${percentage}%`
                      }}
                    />
                  </div>
                </div>
              );
            })}
            {data.data_source_distribution.length === 0 && (
              <div className="text-slate-500 text-sm py-12 text-center">No data source breakdown available.</div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
