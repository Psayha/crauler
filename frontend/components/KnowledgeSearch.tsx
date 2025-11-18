"use client";

import { useState } from "react";
import { Search, Filter, X } from "lucide-react";

interface KnowledgeEntry {
  id: string;
  title: string;
  content: string;
  content_type: string;
  source_type: string | null;
  source_id: string | null;
  agent_type: string | null;
  tags: string[];
  metadata: Record<string, any>;
  token_count: number;
  relevance_score: number;
  created_at: string;
}

interface SearchFilters {
  content_type?: string;
  agent_type?: string;
  tags?: string[];
}

export default function KnowledgeSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<KnowledgeEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({});
  const [selectedEntry, setSelectedEntry] = useState<KnowledgeEntry | null>(
    null
  );

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/knowledge/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          top_k: 10,
          ...filters,
        }),
      });

      if (!response.ok) {
        throw new Error("Search failed");
      }

      const data = await response.json();
      setResults(data.results || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const getRelevanceColor = (score: number) => {
    if (score >= 0.8) return "text-green-600";
    if (score >= 0.6) return "text-yellow-600";
    return "text-gray-600";
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Knowledge Base Search</h1>
        <p className="text-gray-600">
          Search through past tasks, projects, and agent outputs
        </p>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="mb-6">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search knowledge base..."
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-3 border rounded-lg flex items-center gap-2 ${
              showFilters
                ? "bg-blue-50 border-blue-500 text-blue-700"
                : "border-gray-300 text-gray-700"
            }`}
          >
            <Filter className="w-5 h-5" />
            Filters
          </button>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="mt-4 p-4 border border-gray-200 rounded-lg bg-gray-50">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Content Type
                </label>
                <select
                  value={filters.content_type || ""}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      content_type: e.target.value || undefined,
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="">All Types</option>
                  <option value="task_result">Task Results</option>
                  <option value="project_output">Project Outputs</option>
                  <option value="documentation">Documentation</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Agent Type
                </label>
                <select
                  value={filters.agent_type || ""}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      agent_type: e.target.value || undefined,
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="">All Agents</option>
                  <option value="marketing">Marketing</option>
                  <option value="frontend">Frontend Developer</option>
                  <option value="backend">Backend Developer</option>
                  <option value="data_analyst">Data Analyst</option>
                  <option value="ux_designer">UX Designer</option>
                  <option value="content_writer">Content Writer</option>
                  <option value="mobile_developer">Mobile Developer</option>
                  <option value="devops">DevOps Engineer</option>
                  <option value="project_manager">Project Manager</option>
                  <option value="qa_engineer">QA Engineer</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </form>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Results */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Results List */}
        <div className="space-y-4">
          {results.length === 0 && !loading && query && (
            <div className="text-center py-12 text-gray-500">
              No results found. Try a different search query.
            </div>
          )}

          {results.map((entry) => (
            <div
              key={entry.id}
              onClick={() => setSelectedEntry(entry)}
              className={`p-4 border rounded-lg cursor-pointer transition-all ${
                selectedEntry?.id === entry.id
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-200 hover:border-gray-300 bg-white"
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-semibold text-lg">{entry.title}</h3>
                <span
                  className={`text-sm font-medium ${getRelevanceColor(
                    entry.relevance_score
                  )}`}
                >
                  {(entry.relevance_score * 100).toFixed(0)}%
                </span>
              </div>

              <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                {entry.content}
              </p>

              <div className="flex flex-wrap gap-2 mb-2">
                {entry.tags.slice(0, 3).map((tag, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                  >
                    {tag}
                  </span>
                ))}
                {entry.tags.length > 3 && (
                  <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                    +{entry.tags.length - 3} more
                  </span>
                )}
              </div>

              <div className="flex justify-between items-center text-xs text-gray-500">
                <span>{entry.content_type}</span>
                <span>{formatDate(entry.created_at)}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Detail Panel */}
        <div className="lg:sticky lg:top-6 h-fit">
          {selectedEntry ? (
            <div className="border border-gray-200 rounded-lg bg-white p-6">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-2xl font-bold">{selectedEntry.title}</h2>
                <button
                  onClick={() => setSelectedEntry(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="mb-4 pb-4 border-b">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Type:</span>{" "}
                    <span className="font-medium">
                      {selectedEntry.content_type}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Agent:</span>{" "}
                    <span className="font-medium">
                      {selectedEntry.agent_type || "N/A"}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Source:</span>{" "}
                    <span className="font-medium">
                      {selectedEntry.source_type || "N/A"}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Tokens:</span>{" "}
                    <span className="font-medium">
                      {selectedEntry.token_count.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              <div className="mb-4">
                <h3 className="font-semibold mb-2">Content</h3>
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 p-4 rounded">
                    {selectedEntry.content}
                  </pre>
                </div>
              </div>

              <div className="mb-4">
                <h3 className="font-semibold mb-2">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {selectedEntry.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              {Object.keys(selectedEntry.metadata).length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2">Metadata</h3>
                  <pre className="text-xs text-gray-600 bg-gray-50 p-3 rounded overflow-x-auto">
                    {JSON.stringify(selectedEntry.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div className="border border-gray-200 rounded-lg bg-gray-50 p-12 text-center text-gray-500">
              Select a result to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
