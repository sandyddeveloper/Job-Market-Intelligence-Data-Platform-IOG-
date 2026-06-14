"use client";

import { useEffect, useState, useCallback } from "react";

interface Company {
  company_id: number;
  name: string;
  company_size: number | null;
  state: string | null;
  country: string | null;
  city: string | null;
  url: string | null;
}

interface Industry {
  industry_id: number;
  industry_name: string;
}

interface Skill {
  skill_abr: string;
  skill_name: string;
}

interface JobPosting {
  job_id: number;
  company: Company | null;
  company_name: string | null;
  title: string;
  description: string;
  min_salary: string | null;
  max_salary: string | null;
  med_salary: string | null;
  pay_period: string | null;
  location: string | null;
  views: number | null;
  applies: number | null;
  original_listed_time: number | null;
  listed_time: number | null;
  expiry: number | null;
  closed_time: number | null;
  remote_allowed: boolean | null;
  job_posting_url: string | null;
  application_url: string | null;
  application_type: string | null;
  formatted_work_type: string | null;
  work_type: string | null;
  formatted_experience_level: string | null;
  skills_desc: string | null;
  posting_domain: string | null;
  sponsored: boolean;
  currency: string | null;
  compensation_type: string | null;
  normalized_salary: string | null;
  zip_code: string | null;
  fips: string | null;
  data_source: string;
  industries: Industry[];
  skills: Skill[];
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobPosting[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [offset, setOffset] = useState(0);
  const limit = 10;

  // Filters state
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [workType, setWorkType] = useState("");
  const [experienceLevel, setExperienceLevel] = useState("");
  const [minSalary, setMinSalary] = useState("");

  // Detailed view
  const [selectedJob, setSelectedJob] = useState<JobPosting | null>(null);

  const fetchJobs = useCallback(() => {
    setLoading(true);
    let url = `http://127.0.0.1:8000/api/v1/jobs/?limit=${limit}&offset=${offset}`;

    if (query) url += `&q=${encodeURIComponent(query)}`;
    if (location) url += `&location=${encodeURIComponent(location)}`;
    if (remoteOnly) url += `&remote_allowed=true`;
    if (workType) url += `&work_type=${encodeURIComponent(workType)}`;
    if (experienceLevel) url += `&experience_level=${encodeURIComponent(experienceLevel)}`;
    if (minSalary) url += `&min_salary=${minSalary}`;

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch jobs");
        return res.json();
      })
      .then((data) => {
        setJobs(data.results);
        setCount(data.count);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [offset, query, location, remoteOnly, workType, experienceLevel, minSalary]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0); // reset page
    fetchJobs();
  };

  const handleClearFilters = () => {
    setQuery("");
    setLocation("");
    setRemoteOnly(false);
    setWorkType("");
    setExperienceLevel("");
    setMinSalary("");
    setOffset(0);
  };

  const handleNextPage = () => {
    if (offset + limit < count) {
      setOffset(offset + limit);
    }
  };

  const handlePrevPage = () => {
    if (offset - limit >= 0) {
      setOffset(offset - limit);
    }
  };

  const getRelativeTimeString = (timestamp: number | null) => {
    if (!timestamp) return "N/A";
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  };

  return (
    <div className="flex-1 flex flex-col md:flex-row bg-slate-950 min-h-screen">
      {/* Filters Sidebar */}
      <aside className="w-full md:w-80 bg-slate-900 border-r border-slate-800 p-6 space-y-6 md:h-screen md:overflow-y-auto shrink-0">
        <div className="flex justify-between items-center pb-4 border-b border-slate-800">
          <h2 className="font-bold text-lg text-white">Filter Postings</h2>
          <button
            onClick={handleClearFilters}
            className="text-xs text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
          >
            Clear All
          </button>
        </div>

        {/* Search Input */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Keywords</label>
          <form onSubmit={handleSearchSubmit} className="flex gap-2">
            <input
              type="text"
              placeholder="Title, Company, Skills..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </form>
        </div>

        {/* Location Input */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Location</label>
          <input
            type="text"
            placeholder="City, State, Country..."
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        {/* Remote Checkbox */}
        <div className="flex items-center space-x-3 bg-slate-950/60 p-3 rounded-lg border border-slate-800/40">
          <input
            type="checkbox"
            id="remote"
            checked={remoteOnly}
            onChange={(e) => setRemoteOnly(e.target.checked)}
            className="h-4 w-4 rounded border-slate-800 text-indigo-600 focus:ring-indigo-500 bg-slate-950"
          />
          <label htmlFor="remote" className="text-sm font-medium text-slate-300 select-none cursor-pointer">
            Remote Only allowed
          </label>
        </div>

        {/* Work Type Selection */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Work Type</label>
          <select
            value={workType}
            onChange={(e) => setWorkType(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors cursor-pointer"
          >
            <option value="">Any Work Type</option>
            <option value="FULL_TIME">Full-Time</option>
            <option value="CONTRACT">Contract</option>
            <option value="PART_TIME">Part-Time</option>
            <option value="OTHER">Internship</option>
          </select>
        </div>

        {/* Experience Level Selection */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Experience Level</label>
          <select
            value={experienceLevel}
            onChange={(e) => setExperienceLevel(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors cursor-pointer"
          >
            <option value="">Any Experience</option>
            <option value="Entry level">Entry Level</option>
            <option value="Associate">Associate</option>
            <option value="Mid-Senior level">Mid-Senior</option>
            <option value="Director">Director</option>
            <option value="Executive">Executive</option>
          </select>
        </div>

        {/* Minimum Salary Input */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Min Salary (Annual USD)</label>
          <input
            type="number"
            placeholder="Min Salary..."
            value={minSalary}
            onChange={(e) => setMinSalary(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        <button
          onClick={() => {
            setOffset(0);
            fetchJobs();
          }}
          className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold text-sm transition-all duration-300 shadow-md shadow-indigo-500/10"
        >
          Apply Filters
        </button>
      </aside>

      {/* Jobs Listing Workspace */}
      <section className="flex-1 p-8 space-y-6 flex flex-col justify-between">
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-white">Job Search Portal</h1>
              <p className="text-xs text-slate-400 mt-1">
                Showing {offset + 1} - {Math.min(offset + limit, count)} of {count.toLocaleString()} matching jobs
              </p>
            </div>
          </div>

          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-28 bg-slate-900 border border-slate-800 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : jobs.length === 0 ? (
            <div className="bg-slate-905 border border-slate-800/40 p-12 text-center rounded-2xl">
              <p className="text-slate-400 text-sm">No postings match your current filter parameters.</p>
              <button
                onClick={handleClearFilters}
                className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-lg transition-colors"
              >
                Clear All Filters
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {jobs.map((job) => (
                <div
                  key={job.job_id}
                  onClick={() => setSelectedJob(job)}
                  className="bg-slate-900 border border-slate-800 hover:border-indigo-500/50 hover:shadow-indigo-500/5 transition-all duration-300 p-5 rounded-2xl cursor-pointer flex justify-between items-start group"
                >
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-semibold bg-indigo-500/10 text-indigo-400 px-2 py-0.5 rounded border border-indigo-500/20">
                        {job.data_source}
                      </span>
                      {job.remote_allowed && (
                        <span className="text-xs font-semibold bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/20">
                          Remote
                        </span>
                      )}
                      {job.sponsored && (
                        <span className="text-xs font-semibold bg-purple-500/10 text-purple-400 px-2 py-0.5 rounded border border-purple-500/20">
                          Sponsored
                        </span>
                      )}
                    </div>
                    <div>
                      <h3 className="font-bold text-white text-md group-hover:text-indigo-400 transition-colors">
                        {job.title}
                      </h3>
                      <p className="text-sm text-slate-400 font-medium">
                        {job.company_name || (job.company ? job.company.name : "Unknown Company")}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2 pt-1">
                      {job.skills.slice(0, 5).map((skill) => (
                        <span key={skill.skill_abr} className="text-xs bg-slate-950 text-slate-400 px-2 py-0.5 rounded">
                          {skill.skill_name}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="text-right flex flex-col justify-between h-full space-y-4 shrink-0">
                    <p className="font-bold text-white text-sm">
                      {job.normalized_salary
                        ? `$${parseFloat(job.normalized_salary).toLocaleString(undefined, { maximumFractionDigits: 0 })}/yr`
                        : "Salary Undisclosed"}
                    </p>
                    <div className="text-xs text-slate-500">
                      <p>{job.location || "N/A"}</p>
                      <p className="mt-1">Listed: {getRelativeTimeString(job.listed_time)}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pagination controls */}
        <div className="flex justify-between items-center pt-6 border-t border-slate-800">
          <button
            onClick={handlePrevPage}
            disabled={offset === 0 || loading}
            className="px-4 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-50 text-slate-300 text-sm font-semibold rounded-lg transition-colors cursor-pointer"
          >
            ← Previous
          </button>
          <span className="text-xs text-slate-500">
            Page {Math.floor(offset / limit) + 1} of {Math.max(1, Math.ceil(count / limit))}
          </span>
          <button
            onClick={handleNextPage}
            disabled={offset + limit >= count || loading}
            className="px-4 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-50 text-slate-300 text-sm font-semibold rounded-lg transition-colors cursor-pointer"
          >
            Next →
          </button>
        </div>
      </section>

      {/* Detailed view Modal Drawer */}
      {selectedJob && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-end">
          <div
            className="w-full max-w-2xl bg-slate-900 border-l border-slate-800 h-full p-8 flex flex-col justify-between overflow-y-auto animate-slide-in shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="space-y-6">
              {/* Close row */}
              <div className="flex justify-between items-center border-b border-slate-800 pb-4">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-semibold bg-indigo-500/10 text-indigo-400 px-2.5 py-0.5 rounded border border-indigo-500/20">
                    ID: {selectedJob.job_id}
                  </span>
                  <span className="text-xs font-semibold bg-slate-800 text-slate-300 px-2.5 py-0.5 rounded">
                    Source: {selectedJob.data_source}
                  </span>
                </div>
                <button
                  onClick={() => setSelectedJob(null)}
                  className="text-slate-400 hover:text-white font-bold text-lg cursor-pointer"
                >
                  ✕
                </button>
              </div>

              {/* Title / Company */}
              <div>
                <h2 className="text-2xl font-bold text-white">{selectedJob.title}</h2>
                <p className="text-indigo-400 font-semibold mt-1">
                  {selectedJob.company_name || (selectedJob.company ? selectedJob.company.name : "Unknown")}
                </p>
                {selectedJob.company?.url && (
                  <a
                    href={selectedJob.company.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-indigo-500 hover:underline mt-1 block"
                  >
                    Visit company website
                  </a>
                )}
              </div>

              {/* Attributes Grid */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 bg-slate-950/60 p-4 rounded-xl border border-slate-800/50 text-sm">
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Salary Estimate</p>
                  <p className="font-bold text-white mt-1">
                    {selectedJob.normalized_salary
                      ? `$${parseFloat(selectedJob.normalized_salary).toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                      : "Undisclosed"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Location</p>
                  <p className="font-semibold text-slate-200 mt-1">{selectedJob.location || "N/A"}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Remote Allowed</p>
                  <p className="font-semibold text-slate-200 mt-1">
                    {selectedJob.remote_allowed ? "Yes (Allowed)" : "No (On-Site/Hybrid)"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Work Type</p>
                  <p className="font-semibold text-slate-200 mt-1">
                    {selectedJob.formatted_work_type || selectedJob.work_type || "N/A"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Experience Level</p>
                  <p className="font-semibold text-slate-200 mt-1">
                    {selectedJob.formatted_experience_level || "Associate"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider">Listed Date</p>
                  <p className="font-semibold text-slate-200 mt-1">
                    {getRelativeTimeString(selectedJob.listed_time)}
                  </p>
                </div>
              </div>

              {/* Skills */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Required Skills</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedJob.skills.map((skill) => (
                    <span key={skill.skill_abr} className="text-xs bg-slate-850 border border-slate-800/80 text-slate-300 px-3 py-1 rounded-full">
                      {skill.skill_name}
                    </span>
                  ))}
                  {selectedJob.skills.length === 0 && <span className="text-xs text-slate-500">None mapped</span>}
                </div>
              </div>

              {/* Industries */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Relevant Industries</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedJob.industries.map((ind) => (
                    <span key={ind.industry_id} className="text-xs bg-indigo-500/5 border border-indigo-500/10 text-indigo-400 px-3 py-1 rounded-full">
                      {ind.industry_name}
                    </span>
                  ))}
                  {selectedJob.industries.length === 0 && <span className="text-xs text-slate-500">None mapped</span>}
                </div>
              </div>

              {/* Description */}
              <div className="space-y-2 border-t border-slate-800 pt-6">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Job Description</h4>
                <div className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">
                  {selectedJob.description}
                </div>
              </div>
            </div>

            {/* Application link */}
            <div className="border-t border-slate-800 pt-6 mt-8 flex gap-4">
              {selectedJob.application_url ? (
                <a
                  href={selectedJob.application_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex-1 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-center font-bold text-sm transition-colors"
                >
                  Apply Directly
                </a>
              ) : selectedJob.job_posting_url ? (
                <a
                  href={selectedJob.job_posting_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex-1 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-center font-bold text-sm transition-colors"
                >
                  Apply via Posting
                </a>
              ) : null}
              <button
                onClick={() => setSelectedJob(null)}
                className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-semibold text-sm transition-colors cursor-pointer"
              >
                Close Details
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
