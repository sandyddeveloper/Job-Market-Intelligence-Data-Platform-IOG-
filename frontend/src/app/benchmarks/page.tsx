"use client";

import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  Legend,
  AreaChart,
  Area
} from "recharts";

interface DSTrend {
  work_year: number;
  experience_level: string;
  avg_salary_usd: number;
  count: number;
}

interface DAStat {
  sector: string;
  avg_rating: number;
  count: number;
}

interface SalaryHistory {
  month: string;
  category: string | null;
  avg_salary: number;
}

interface SalaryHistogram {
  salary_bracket: string;
  vacancy_count: number;
}

interface TopCompany {
  company_name: string;
  vacancy_count: number;
  average_salary: string | null;
}

const COLORS = ["#6366f1", "#a855f7", "#ec4899", "#10b981", "#f59e0b", "#3b82f6"];

export default function BenchmarksPage() {
  const [dsTrends, setDsTrends] = useState<DSTrend[]>([]);
  const [daStats, setDaStats] = useState<DAStat[]>([]);
  const [salaryHistory, setSalaryHistory] = useState<SalaryHistory[]>([]);
  const [histogram, setHistogram] = useState<SalaryHistogram[]>([]);
  const [topCompanies, setTopCompanies] = useState<TopCompany[]>([]);

  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    
    const urls = [
      "http://127.0.0.1:8000/api/v1/benchmarks/ds-trends/",
      "http://127.0.0.1:8000/api/v1/benchmarks/da-stats/",
      "http://127.0.0.1:8000/api/v1/benchmarks/history/",
      "http://127.0.0.1:8000/api/v1/benchmarks/histogram/",
      "http://127.0.0.1:8000/api/v1/benchmarks/top-companies/"
    ];

    Promise.all(urls.map(url => fetch(url).then(res => res.json())))
      .then(([ds, da, hist, brackets, comps]) => {
        setDsTrends(ds);
        setDaStats(da);
        setSalaryHistory(hist);
        setHistogram(brackets);
        setTopCompanies(comps);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching benchmarks", err);
        setLoading(false);
      });
  }, []);

  if (!mounted) return null;

  if (loading) {
    return (
      <div className="flex-1 bg-slate-950 p-8 space-y-6">
        <header className="flex justify-between items-center pb-4 border-b border-slate-800">
          <div className="h-8 w-64 bg-slate-800 rounded animate-pulse" />
        </header>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="h-96 bg-slate-900 border border-slate-800 rounded-xl animate-pulse" />
          <div className="h-96 bg-slate-900 border border-slate-800 rounded-xl animate-pulse" />
        </div>
      </div>
    );
  }

  // Format DS trends data for charts
  // dsTrends is list of {work_year, experience_level, avg_salary_usd}
  // Group by year: {year, EN: sal, MI: sal, SE: sal, EX: sal}
  const years = Array.from(new Set(dsTrends.map(d => d.work_year))).sort();
  const dsChartData = years.map(year => {
    const dataForYear = dsTrends.filter(d => d.work_year === year);
    const row: any = { year };
    dataForYear.forEach(d => {
      let label = d.experience_level;
      if (label === "EN") label = "Entry Level";
      if (label === "MI") label = "Mid Level";
      if (label === "SE") label = "Senior Level";
      if (label === "EX") label = "Executive";
      row[label] = Math.round(d.avg_salary_usd);
    });
    return row;
  });

  return (
    <div className="p-8 space-y-8 bg-slate-950 min-h-screen">
      {/* Header bar */}
      <header className="pb-6 border-b border-slate-800">
        <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
          Salary & Market Benchmarks
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Historical benchmark metrics compiled from global Data Science and Analyst reports compared against Adzuna vacancy tracking.
        </p>
      </header>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Data Science Salary Trends */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl min-w-0">
          <h3 className="text-lg font-semibold text-white mb-4">Data Science Salaries over Years (USD)</h3>
          {dsChartData.length > 0 ? (
            <div className="h-80 w-full min-w-0">
              <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                <LineChart data={dsChartData}>
                  <XAxis dataKey="year" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(tick) => `$${tick.toLocaleString()}`} />
                  <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px" }} labelClassName="text-white" />
                  <Legend verticalAlign="top" height={36} iconType="circle" />
                  <Line type="monotone" dataKey="Entry Level" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="Mid Level" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="Senior Level" stroke="#6366f1" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="Executive" stroke="#a855f7" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-80 flex items-center justify-center text-slate-500">No Data Science benchmark records found.</div>
          )}
        </div>

        {/* Data Analyst Sector Ratings */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl min-w-0">
          <h3 className="text-lg font-semibold text-white mb-4">Data Analyst Industry Sector Ratings</h3>
          {daStats.length > 0 ? (
            <div className="h-80 w-full min-w-0">
              <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                <BarChart data={daStats} margin={{ bottom: 20 }}>
                  <XAxis dataKey="sector" stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} angle={-30} textAnchor="end" interval={0} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} domain={[0, 5]} />
                  <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px" }} labelClassName="text-white" />
                  <Bar dataKey="avg_rating" fill="#a855f7" radius={[4, 4, 0, 0]}>
                    {daStats.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-80 flex items-center justify-center text-slate-500">No Analyst ratings found.</div>
          )}
        </div>

        {/* Adzuna MoM Salary History */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl min-w-0">
          <h3 className="text-lg font-semibold text-white mb-4">Adzuna MoM IT Jobs Average Salary (GBP)</h3>
          {salaryHistory.length > 0 ? (
            <div className="h-80 w-full min-w-0">
              <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                <AreaChart data={salaryHistory}>
                  <XAxis dataKey="month" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(tick) => `£${tick.toLocaleString()}`} />
                  <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px" }} labelClassName="text-white" />
                  <Area type="monotone" dataKey="avg_salary" stroke="#10b981" fillOpacity={0.1} fill="url(#colorEmerald)" strokeWidth={2} />
                  <defs>
                    <linearGradient id="colorEmerald" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-80 flex items-center justify-center text-slate-500">No MoM salary history found. Run API ingestion first.</div>
          )}
        </div>

        {/* Adzuna Salary Bracket Histogram */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl min-w-0">
          <h3 className="text-lg font-semibold text-white mb-4">Adzuna Salary Brackets Vacancies (GBP)</h3>
          {histogram.length > 0 ? (
            <div className="h-80 w-full min-w-0">
              <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                <BarChart data={histogram}>
                  <XAxis dataKey="salary_bracket" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(tick) => `£${parseFloat(tick).toLocaleString()}`} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px" }} labelClassName="text-white" />
                  <Bar dataKey="vacancy_count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-80 flex items-center justify-center text-slate-500">No vacancy distribution histogram found. Run API ingestion first.</div>
          )}
        </div>

      </div>


      {/* Standings Table area */}
      <section className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-white">Top Standings hiring companies</h3>
          <p className="text-slate-500 text-xs mt-1">Ranking of active employers by total job vacancies listed via Adzuna APIs.</p>
        </div>
        
        {topCompanies.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-medium">
                  <th className="py-3 px-4">Company Name</th>
                  <th className="py-3 px-4">Active Vacancies</th>
                  <th className="py-3 px-4">Average Offered Salary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                {topCompanies.map((company) => (
                  <tr key={company.company_name} className="hover:bg-slate-800/20 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-white">{company.company_name}</td>
                    <td className="py-3.5 px-4">
                      <span className="bg-indigo-500/10 text-indigo-400 font-semibold px-2.5 py-0.5 rounded border border-indigo-500/20">
                        {company.vacancy_count} roles
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-bold text-slate-300">
                      {company.average_salary
                        ? `£${parseFloat(company.average_salary).toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                        : "N/A"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center text-slate-500 text-sm">
            No top standings records found. Run API ingestion to gather standings data.
          </div>
        )}
      </section>
    </div>
  );
}
