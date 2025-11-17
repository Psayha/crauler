"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Database, FileText, Bot, Tag } from "lucide-react";

interface KnowledgeStats {
  total_entries: number;
  by_content_type: Record<string, number>;
  by_agent_type: Record<string, number>;
  total_tokens: number;
}

export default function KnowledgeStats() {
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const data = await api.getKnowledgeStats();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load stats");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="bg-white rounded-lg shadow p-6 animate-pulse"
          >
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        {error}
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat().format(num);
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <Database className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <div className="text-2xl font-bold mb-1">
            {formatNumber(stats.total_entries)}
          </div>
          <div className="text-sm text-gray-600">Total Entries</div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <FileText className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <div className="text-2xl font-bold mb-1">
            {Object.keys(stats.by_content_type).length}
          </div>
          <div className="text-sm text-gray-600">Content Types</div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Bot className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <div className="text-2xl font-bold mb-1">
            {Object.keys(stats.by_agent_type).length}
          </div>
          <div className="text-sm text-gray-600">Active Agents</div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-orange-100 rounded-lg">
              <Tag className="w-6 h-6 text-orange-600" />
            </div>
          </div>
          <div className="text-2xl font-bold mb-1">
            {formatNumber(stats.total_tokens)}
          </div>
          <div className="text-sm text-gray-600">Total Tokens</div>
        </div>
      </div>

      {/* Detailed Breakdowns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* By Content Type */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">By Content Type</h3>
          <div className="space-y-3">
            {Object.entries(stats.by_content_type).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-sm font-medium capitalize">
                    {type.replace(/_/g, " ")}
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{
                        width: `${(count / stats.total_entries) * 100}%`,
                      }}
                    ></div>
                  </div>
                  <span className="text-sm font-semibold w-12 text-right">
                    {count}
                  </span>
                </div>
              </div>
            ))}
            {Object.keys(stats.by_content_type).length === 0 && (
              <div className="text-sm text-gray-500 text-center py-4">
                No entries yet
              </div>
            )}
          </div>
        </div>

        {/* By Agent Type */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">By Agent Type</h3>
          <div className="space-y-3">
            {Object.entries(stats.by_agent_type)
              .sort((a, b) => b[1] - a[1])
              .slice(0, 10)
              .map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                    <span className="text-sm font-medium capitalize">
                      {type.replace(/_/g, " ")}
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-purple-500 h-2 rounded-full"
                        style={{
                          width: `${(count / stats.total_entries) * 100}%`,
                        }}
                      ></div>
                    </div>
                    <span className="text-sm font-semibold w-12 text-right">
                      {count}
                    </span>
                  </div>
                </div>
              ))}
            {Object.keys(stats.by_agent_type).length === 0 && (
              <div className="text-sm text-gray-500 text-center py-4">
                No agent data yet
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
