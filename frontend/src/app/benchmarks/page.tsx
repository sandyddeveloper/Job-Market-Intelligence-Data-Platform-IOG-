"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
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
import { TrendingUp, Users, Award, ShieldAlert, BarChart3, Building } from "lucide-react";

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

const COLORS = ["#0a66c2", "#00a0dc", "#0073b1", "#33a0fc", "#70b5f9", "#b3dbff"];

function BenchmarksPage() {
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
      <div className="w-full max-w-6xl mx-auto space-y-6 animate-pulse">
        <div className="h-12 bg-white border border-[#e0e0e0] rounded-lg" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-96 bg-white border border-[#e0e0e0] rounded-lg" />
          <div className="h-96 bg-white border border-[#e0e0e0] rounded-lg" />
        </div>
      </div>
    );
  }

  // Format DS trends data for charts
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
    <div className="space-y-6">
      {/* Header bar */}
      <div className="bg-white border border-[#e0e0e0] rounded-lg p-5 shadow-sm">
        <h1 className="text-xl font-bold text-[#191919] flex items-center space-x-2">
          <TrendingUp className="h-6 w-6 text-[#0a66c2]" />
          <span>Salary & Market Benchmarks</span>
        </h1>
        <p className="text-xs text-[#5e5e5e] mt-1.5 leading-relaxed">
          Historical benchmark metrics compiled from global Data Science and Analyst reports compared against Adzuna vacancy tracking. Use these points to benchmark industry salary standards.
        </p>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        
        {/* Data Science Salary Trends */}
        <div className="bg-white border border-[#e0e0e0] p-5 rounded-lg shadow-sm">
          <div className="flex items-center space-x-2 mb-4 border-b border-[#f3f2f0] pb-2">
            <Award className="h-5 w-5 text-[#0a66c2]" />
            <h3 className="text-sm font-bold text-[#191919]">Data Science Salaries over Years (USD)</h3>
          </div>
          {dsChartData.length > 0 ? (
            <div className="h-72 w-full">
              <ResponsiveContainer id="ds-salary-chart" width="100%" height="100%">
                <LineChart data={dsChartData}>
                  <XAxis dataKey="year" stroke="#5e5e5e" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="#5e5e5e" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(tick) => `$${tick.toLocaleString()}`} />
                  <Tooltip contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e0e0e0", borderRadius: "4px", fontSize: "11px" }} />
                  <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: "10px" }} />
                  <Line type="monotone" dataKey="Entry Level" stroke="#70b5f9" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="Mid Level" stroke="#00a0dc" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="Senior Level" stroke="#0a66c2" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="Executive" stroke="#004182" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-72 flex items-center justify-center text-xs text-[#5e5e5e]">No Data Science benchmark records found.</div>
          )}
        </div>

        {/* Data Analyst Sector Ratings */}
        <div className="bg-white border border-[#e0e0e0] p-5 rounded-lg shadow-sm">
          <div className="flex items-center space-x-2 mb-4 border-b border-[#f3f2f0] pb-2">
            <Users className="h-5 w-5 text-[#0a66c2]" />
            <h3 className="text-sm font-bold text-[#191919]">Data Analyst Industry Sector Ratings</h3>
          </div>
          {daStats.length > 0 ? (
            <div className="h-72 w-full">
              <ResponsiveContainer id="da-sector-chart" width="100%" height="100%">
                <BarChart data={daStats} margin={{ bottom: 20 }}>
                  <XAxis dataKey="sector" stroke="#5e5e5e" fontSize={9} tickLine={false} axisLine={false} angle={-25} textAnchor="end" interval={0} />
                  <YAxis stroke="#5e5e5e" fontSize={10} tickLine={false} axisLine={false} domain={[0, 5]} />
                  <Tooltip contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e0e0e0", borderRadius: "4px", fontSize: "11px" }} />
                  <Bar dataKey="avg_rating" fill="#0a66c2" radius={[3, 3, 0, 0]}>
                    {daStats.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-72 flex items-center justify-center text-xs text-[#5e5e5e]">No Analyst ratings found.</div>
          )}
        </div>

        {/* Adzuna MoM Salary History */}
        <div className="bg-white border border-[#e0e0e0] p-5 rounded-lg shadow-sm">
          <div className="flex items-center space-x-2 mb-4 border-b border-[#f3f2f0] pb-2">
            <BarChart3 className="h-5 w-5 text-[#0a66c2]" />
            <h3 className="text-sm font-bold text-[#191919]">Adzuna MoM IT Jobs Average Salary (GBP)</h3>
          </div>
          {salaryHistory.length > 0 ? (
            <div className="h-72 w-full">
              <ResponsiveContainer id="adzuna-salary-history-chart" width="100%" height="100%">
                <AreaChart data={salaryHistory}>
                  <XAxis dataKey="month" stroke="#5e5e5e" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="#5e5e5e" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(tick) => `£${tick.toLocaleString()}`} />
                  <Tooltip contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e0e0e0", borderRadius: "4px", fontSize: "11px" }} />
                  <Area type="monotone" dataKey="avg_salary" stroke="#0a66c2" fillOpacity={0.1} fill="url(#colorBlue)" strokeWidth={2} />
                  <defs>
                    <linearGradient id="colorBlue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0a66c2" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#0a66c2" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-72 flex items-center justify-center text-xs text-[#5e5e5e] text-center p-6 bg-[#f9fafb] border border-dashed border-[#e0e0e0] rounded-[4px]">
              <ShieldAlert className="h-8 w-8 text-amber-500 mb-2" />
              <span>No MoM salary history found. Confirm your Adzuna App ID and App Key are active in Space secrets, then wait for your 12:40 PM cron trigger!</span>
            </div>
          )}
        </div>

        {/* Adzuna Salary Bracket Histogram */}
        <div className="bg-white border border-[#e0e0e0] p-5 rounded-lg shadow-sm">
          <div className="flex items-center space-x-2 mb-4 border-b border-[#f3f2f0] pb-2">
            <TrendingUp className="h-5 w-5 text-[#0a66c2]" />
            <h3 className="text-sm font-bold text-[#191919]">Adzuna Salary Brackets Vacancies (GBP)</h3>
          </div>
          {histogram.length > 0 ? (
            <div className="h-72 w-full">
              <ResponsiveContainer id="adzuna-salary-brackets-chart" width="100%" height="100%">
                <BarChart data={histogram}>
                  <XAxis dataKey="salary_bracket" stroke="#5e5e5e" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(tick) => `£${parseFloat(tick).toLocaleString()}`} />
                  <YAxis stroke="#5e5e5e" fontSize={10} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e0e0e0", borderRadius: "4px", fontSize: "11px" }} />
                  <Bar dataKey="vacancy_count" fill="#00a0dc" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-72 flex items-center justify-center text-xs text-[#5e5e5e] text-center p-6 bg-[#f9fafb] border border-dashed border-[#e0e0e0] rounded-[4px]">
              <ShieldAlert className="h-8 w-8 text-amber-500 mb-2" />
              <span>No vacancy distribution histogram found. Confirm your Adzuna API credentials are active!</span>
            </div>
          )}
        </div>

      </div>

      {/* Standings Table area */}
      <section className="bg-white border border-[#e0e0e0] p-5 rounded-lg shadow-sm space-y-4">
        <div className="border-b border-[#f3f2f0] pb-3">
          <h3 className="text-sm font-bold text-[#191919] flex items-center space-x-2">
            <Building className="h-5 w-5 text-[#0a66c2]" />
            <span>Top Hiring Companies Standings</span>
          </h3>
          <p className="text-[#5e5e5e] text-xs mt-1">Ranking of active employers by total job vacancies listed via Adzuna APIs.</p>
        </div>
        
        {topCompanies.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#e0e0e0] text-[#5e5e5e] font-semibold bg-[#f9fafb]">
                  <th className="py-2.5 px-4">Company Name</th>
                  <th className="py-2.5 px-4">Active Vacancies</th>
                  <th className="py-2.5 px-4">Average Offered Salary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#e0e0e0] text-[#191919] font-medium">
                {topCompanies.map((company) => (
                  <tr key={company.company_name} className="hover:bg-[#f0f7ff]/40 transition-colors">
                    <td className="py-3 px-4 font-bold text-[#0a66c2] hover:underline cursor-pointer">{company.company_name}</td>
                    <td className="py-3 px-4">
                      <span className="bg-[#e6f4ea] text-[#0f5132] font-semibold px-2.5 py-0.5 rounded-[4px] border border-[#d1e7dd]">
                        {company.vacancy_count} roles active
                      </span>
                    </td>
                    <td className="py-3 px-4 font-bold text-[#191919]">
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
          <div className="py-12 text-center text-[#5e5e5e] text-xs">
            No top standings records found. Verify your Adzuna Space secrets to collect standings data.
          </div>
        )}
      </section>
    </div>
  );
}

export default dynamic(() => Promise.resolve(BenchmarksPage), { ssr: false });

