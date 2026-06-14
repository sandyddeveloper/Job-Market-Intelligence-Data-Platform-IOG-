"use client";

import { useEffect, useState, useCallback } from "react";
import { 
  Briefcase, 
  MapPin, 
  Search, 
  Globe, 
  Award, 
  Clock, 
  Calendar,
  ExternalLink,
  SlidersHorizontal,
  Bookmark,
  CheckCircle2,
  Users
} from "lucide-react";

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

  // Detailed view (selected job)
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
        // Automatically select the first job if none is selected
        if (data.results.length > 0 && !selectedJob) {
          setSelectedJob(data.results[0]);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [offset, query, location, remoteOnly, workType, experienceLevel, minSalary, selectedJob]);

  useEffect(() => {
    fetchJobs();
  }, [offset]); // Run when page offset changes

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
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
    // Let the direct fetch reset it
    setTimeout(() => fetchJobs(), 50);
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
    if (!timestamp) return "Just now";
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
  };

  // Helper to generate a placeholder color based on company name
  const getAvatarColor = (name: string) => {
    const colors = ["bg-red-600", "bg-emerald-600", "bg-indigo-600", "bg-amber-600", "bg-purple-600", "bg-cyan-600"];
    const hash = name.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
    return colors[hash % colors.length];
  };

  return (
    <div className="space-y-4">
      {/* 1. LinkedIn Search Bar Panel */}
      <div className="bg-white border border-[#e0e0e0] rounded-lg p-4 shadow-sm">
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
          <div className="md:col-span-5 relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-[#5e5e5e]" />
            <input
              type="text"
              placeholder="Search job titles, skills, or keywords"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full bg-[#f3f2f0] border border-transparent rounded-[4px] py-1.5 pl-9 pr-3 text-sm text-[#191919] placeholder-[#5e5e5e] focus:outline-none focus:bg-white focus:border-[#0a66c2] focus:ring-1 focus:ring-[#0a66c2]"
            />
          </div>
          <div className="md:col-span-4 relative">
            <MapPin className="absolute left-3 top-2.5 h-4 w-4 text-[#5e5e5e]" />
            <input
              type="text"
              placeholder="City, state, or country"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full bg-[#f3f2f0] border border-transparent rounded-[4px] py-1.5 pl-9 pr-3 text-sm text-[#191919] placeholder-[#5e5e5e] focus:outline-none focus:bg-white focus:border-[#0a66c2] focus:ring-1 focus:ring-[#0a66c2]"
            />
          </div>
          <div className="md:col-span-3 flex gap-2">
            <button
              type="submit"
              className="flex-1 py-1.5 bg-[#0a66c2] hover:bg-[#004182] text-white font-semibold text-sm rounded-full transition-all shadow-sm"
            >
              Search
            </button>
            <button
              type="button"
              onClick={handleClearFilters}
              className="px-3 py-1.5 bg-white border border-[#e0e0e0] hover:bg-[#f3f2f0] text-[#5e5e5e] font-semibold text-xs rounded-full transition-all"
            >
              Reset
            </button>
          </div>
        </form>

        {/* Filters Quick bar */}
        <div className="flex flex-wrap items-center gap-2 pt-3 mt-3 border-t border-[#f3f2f0] text-xs">
          <div className="flex items-center space-x-1">
            <input
              type="checkbox"
              id="remote"
              checked={remoteOnly}
              onChange={(e) => {
                setRemoteOnly(e.target.checked);
                setOffset(0);
              }}
              className="h-3.5 w-3.5 rounded border-[#e0e0e0] text-[#0a66c2] focus:ring-[#0a66c2]"
            />
            <label htmlFor="remote" className="font-semibold text-[#5e5e5e] select-none cursor-pointer">
              Remote Only
            </label>
          </div>

          <select
            value={workType}
            onChange={(e) => {
              setWorkType(e.target.value);
              setOffset(0);
            }}
            className="bg-[#f3f2f0] hover:bg-[#e4ebf2] text-[#5e5e5e] font-semibold rounded-full px-2.5 py-1 focus:outline-none cursor-pointer"
          >
            <option value="">Work Type</option>
            <option value="FULL_TIME">Full-Time</option>
            <option value="CONTRACT">Contract</option>
            <option value="PART_TIME">Part-Time</option>
            <option value="OTHER">Internship</option>
          </select>

          <select
            value={experienceLevel}
            onChange={(e) => {
              setExperienceLevel(e.target.value);
              setOffset(0);
            }}
            className="bg-[#f3f2f0] hover:bg-[#e4ebf2] text-[#5e5e5e] font-semibold rounded-full px-2.5 py-1 focus:outline-none cursor-pointer"
          >
            <option value="">Experience Level</option>
            <option value="Entry level">Entry Level</option>
            <option value="Associate">Associate</option>
            <option value="Mid-Senior level">Mid-Senior</option>
            <option value="Director">Director</option>
            <option value="Executive">Executive</option>
          </select>

          <input
            type="number"
            placeholder="Min Salary ($/yr)"
            value={minSalary}
            onChange={(e) => {
              setMinSalary(e.target.value);
              setOffset(0);
            }}
            className="bg-[#f3f2f0] text-[#5e5e5e] font-semibold rounded-full px-3 py-1 focus:outline-none w-28 placeholder-[#888]"
          />
          
          <button
            type="button"
            onClick={() => {
              setOffset(0);
              fetchJobs();
            }}
            className="ml-auto py-1 px-3 bg-white border border-[#0a66c2] hover:bg-[#f0f7ff] text-[#0a66c2] font-bold rounded-full transition-all"
          >
            Apply Active Filters
          </button>
        </div>
      </div>

      {/* 2. Split Screen Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        
        {/* Left Side: Job Cards List (5 columns) */}
        <div className="lg:col-span-5 space-y-3">
          <div className="bg-white border border-[#e0e0e0] rounded-lg shadow-sm overflow-hidden flex flex-col justify-between min-h-[500px]">
            <div>
              <div className="p-4 border-b border-[#f3f2f0] flex justify-between items-center bg-[#f9fafb]">
                <h2 className="text-sm font-bold text-[#191919]">Job Results</h2>
                <span className="text-xs text-[#5e5e5e]">
                  {count.toLocaleString()} vacancies found
                </span>
              </div>

              {loading ? (
                <div className="divide-y divide-[#f3f2f0]">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="p-4 space-y-2 animate-pulse">
                      <div className="h-4 w-3/4 bg-[#e0e0e0] rounded" />
                      <div className="h-3 w-1/2 bg-[#e0e0e0] rounded" />
                      <div className="h-3 w-1/4 bg-[#e0e0e0] rounded" />
                    </div>
                  ))}
                </div>
              ) : jobs.length === 0 ? (
                <div className="p-8 text-center text-[#5e5e5e] text-sm">
                  No postings match your current filter parameters.
                </div>
              ) : (
                <div className="divide-y divide-[#f3f2f0]">
                  {jobs.map((job) => {
                    const companyName = job.company_name || (job.company ? job.company.name : "Unknown Company");
                    const isSelected = selectedJob?.job_id === job.job_id;
                    return (
                      <div
                        key={job.job_id}
                        onClick={() => setSelectedJob(job)}
                        className={`p-4 transition-all cursor-pointer flex space-x-3 text-left ${
                          isSelected ? "bg-[#f0f7ff] border-l-4 border-[#0a66c2]" : "hover:bg-[#f3f2f0]/60"
                        }`}
                      >
                        {/* Company Logo Initials */}
                        <div className={`h-11 w-11 rounded-[4px] flex items-center justify-center font-bold text-white text-base shadow-sm shrink-0 uppercase ${getAvatarColor(companyName)}`}>
                          {companyName.substring(0, 2)}
                        </div>
                        
                        <div className="flex-1 min-w-0 space-y-1">
                          <h4 className="font-bold text-sm text-[#0a66c2] hover:underline leading-snug truncate">
                            {job.title}
                          </h4>
                          <p className="text-xs font-semibold text-[#191919] truncate">{companyName}</p>
                          <p className="text-xs text-[#5e5e5e] truncate">{job.location || "N/A"}</p>
                          
                          <div className="flex flex-wrap items-center gap-1.5 pt-1.5">
                            <span className="text-[10px] font-semibold bg-[#e8e8e8] text-[#5e5e5e] px-1.5 py-0.5 rounded-[3px]">
                              {job.data_source}
                            </span>
                            {job.remote_allowed && (
                              <span className="text-[10px] font-semibold bg-[#e1f0fe] text-[#0a66c2] px-1.5 py-0.5 rounded-[3px]">
                                Remote
                              </span>
                            )}
                            {job.normalized_salary && (
                              <span className="text-[10px] font-semibold bg-[#e6f4ea] text-[#0f5132] px-1.5 py-0.5 rounded-[3px]">
                                ${parseFloat(job.normalized_salary).toLocaleString(undefined, { maximumFractionDigits: 0 })}/yr
                              </span>
                            )}
                          </div>
                        </div>
                        
                        <div className="text-[10px] text-[#5e5e5e] shrink-0 self-start">
                          {getRelativeTimeString(job.listed_time)}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Pagination footer */}
            <div className="p-3 border-t border-[#f3f2f0] flex justify-between items-center bg-[#f9fafb]">
              <button
                onClick={handlePrevPage}
                disabled={offset === 0 || loading}
                className="px-3 py-1 bg-white border border-[#e0e0e0] hover:bg-[#f3f2f0] disabled:opacity-50 text-[#5e5e5e] text-xs font-semibold rounded-full transition-all cursor-pointer"
              >
                Prev
              </button>
              <span className="text-[11px] text-[#5e5e5e] font-semibold">
                Page {Math.floor(offset / limit) + 1} of {Math.max(1, Math.ceil(count / limit))}
              </span>
              <button
                onClick={handleNextPage}
                disabled={offset + limit >= count || loading}
                className="px-3 py-1 bg-white border border-[#e0e0e0] hover:bg-[#f3f2f0] disabled:opacity-50 text-[#5e5e5e] text-xs font-semibold rounded-full transition-all cursor-pointer"
              >
                Next
              </button>
            </div>
          </div>
        </div>

        {/* Right Side: Detailed View Pane (7 columns) */}
        <div className="lg:col-span-7">
          <div className="bg-white border border-[#e0e0e0] rounded-lg shadow-sm min-h-[500px] flex flex-col justify-between overflow-hidden">
            {selectedJob ? (
              <div className="flex-1 flex flex-col justify-between">
                <div>
                  {/* Detailed Header Area */}
                  <div className="p-6 border-b border-[#f3f2f0] bg-white space-y-4">
                    <div className="flex items-start space-x-4">
                      {/* Avatar */}
                      <div className={`h-14 w-14 rounded-[4px] flex items-center justify-center font-bold text-white text-xl shadow uppercase shrink-0 ${
                        getAvatarColor(selectedJob.company_name || (selectedJob.company ? selectedJob.company.name : "Unknown"))
                      }`}>
                        {(selectedJob.company_name || (selectedJob.company ? selectedJob.company.name : "Unknown")).substring(0, 2)}
                      </div>
                      
                      <div className="flex-1 min-w-0 space-y-1">
                        <h2 className="text-xl font-bold text-[#191919] leading-tight">
                          {selectedJob.title}
                        </h2>
                        <p className="text-sm font-semibold text-[#0a66c2] hover:underline cursor-pointer">
                          {selectedJob.company_name || (selectedJob.company ? selectedJob.company.name : "Unknown Company")}
                        </p>
                        <p className="text-xs text-[#5e5e5e] flex items-center gap-1">
                          <span>{selectedJob.location || "N/A"}</span>
                          <span>•</span>
                          <span className="text-[#057642] font-semibold">
                            {selectedJob.remote_allowed ? "Remote" : "On-site / Hybrid"}
                          </span>
                        </p>
                        <p className="text-[11px] text-[#5e5e5e] flex items-center space-x-1.5 pt-0.5">
                          <Clock className="h-3 w-3" />
                          <span>Posted on {getRelativeTimeString(selectedJob.listed_time)}</span>
                          <span>•</span>
                          <Users className="h-3 w-3" />
                          <span>{selectedJob.views || 0} views • {selectedJob.applies || 0} applicants</span>
                        </p>
                      </div>
                    </div>

                    {/* Action buttons */}
                    <div className="flex items-center space-x-2 pt-2">
                      {selectedJob.application_url ? (
                        <a
                          href={selectedJob.application_url}
                          target="_blank"
                          rel="noreferrer"
                          className="px-6 py-2 bg-[#0a66c2] hover:bg-[#004182] text-white text-sm font-semibold rounded-full transition-colors flex items-center space-x-1 shadow-sm"
                        >
                          <span>Apply</span>
                          <ExternalLink className="h-3.5 w-3.5" />
                        </a>
                      ) : selectedJob.job_posting_url ? (
                        <a
                          href={selectedJob.job_posting_url}
                          target="_blank"
                          rel="noreferrer"
                          className="px-6 py-2 bg-[#0a66c2] hover:bg-[#004182] text-white text-sm font-semibold rounded-full transition-colors flex items-center space-x-1 shadow-sm"
                        >
                          <span>Apply on Company Site</span>
                          <ExternalLink className="h-3.5 w-3.5" />
                        </a>
                      ) : (
                        <button className="px-6 py-2 bg-gray-300 text-gray-500 text-sm font-semibold rounded-full cursor-not-allowed" disabled>
                          Apply Unavailable
                        </button>
                      )}
                      
                      <button className="px-4 py-2 bg-white border border-[#0a66c2] hover:bg-[#f0f7ff] text-[#0a66c2] text-sm font-semibold rounded-full transition-colors flex items-center space-x-1">
                        <Bookmark className="h-4 w-4" />
                        <span>Save</span>
                      </button>
                    </div>
                  </div>

                  {/* Attributes Section */}
                  <div className="p-6 border-b border-[#f3f2f0] grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs bg-[#f9fafb]">
                    <div>
                      <p className="text-[#5e5e5e] font-medium">Job Salary</p>
                      <p className="font-bold text-[#191919] mt-0.5">
                        {selectedJob.normalized_salary
                          ? `$${parseFloat(selectedJob.normalized_salary).toLocaleString(undefined, { maximumFractionDigits: 0 })} / year`
                          : "Undisclosed"}
                      </p>
                    </div>
                    <div>
                      <p className="text-[#5e5e5e] font-medium">Work Type</p>
                      <p className="font-bold text-[#191919] mt-0.5">
                        {selectedJob.formatted_work_type || selectedJob.work_type || "N/A"}
                      </p>
                    </div>
                    <div>
                      <p className="text-[#5e5e5e] font-medium">Experience level</p>
                      <p className="font-bold text-[#191919] mt-0.5">
                        {selectedJob.formatted_experience_level || "Associate"}
                      </p>
                    </div>
                  </div>

                  {/* Body Content Description */}
                  <div className="p-6 space-y-6">
                    {/* Skills required */}
                    {selectedJob.skills.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="text-xs font-bold text-[#191919] uppercase tracking-wider">Required Skills</h4>
                        <div className="flex flex-wrap gap-1.5">
                          {selectedJob.skills.map((skill) => (
                            <span key={skill.skill_abr} className="text-xs bg-[#e1f0fe] text-[#0a66c2] font-semibold px-3 py-1 rounded-full border border-[#b3dbff]">
                              {skill.skill_name}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Industries */}
                    {selectedJob.industries.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="text-xs font-bold text-[#191919] uppercase tracking-wider">Industries</h4>
                        <div className="flex flex-wrap gap-1.5">
                          {selectedJob.industries.map((ind) => (
                            <span key={ind.industry_id} className="text-xs bg-gray-100 text-[#5e5e5e] font-semibold px-3 py-1 rounded-full border border-gray-200">
                              {ind.industry_name}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Main Description */}
                    <div className="space-y-2 border-t border-[#f3f2f0] pt-6">
                      <h4 className="text-xs font-bold text-[#191919] uppercase tracking-wider mb-3">Job Description</h4>
                      <div className="text-sm text-[#191919] leading-relaxed whitespace-pre-wrap font-normal">
                        {selectedJob.description}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Footer close option for smaller viewports */}
                <div className="p-4 bg-gray-50 border-t border-[#f3f2f0] text-right">
                  <span className="text-xs text-[#5e5e5e] font-medium">Job Index ID: {selectedJob.job_id}</span>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center p-12 text-[#5e5e5e] text-center space-y-3">
                <Briefcase className="h-16 w-16 text-[#e0e0e0]" />
                <div>
                  <h3 className="font-bold text-base text-[#191919]">Select a Job Posting</h3>
                  <p className="text-xs max-w-xs mx-auto mt-1">
                    Click on any job listing in the left panel to display its full description, salary details, and application portal links.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
