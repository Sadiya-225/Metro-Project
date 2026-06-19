"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ArrowLeft, Zap, TrendingUp } from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface ScalabilityResult {
  num_nodes: number;
  num_edges: number;
  density: number;
  algorithms: {
    dijkstra: {
      algorithm: string;
      mean_time_ms: number;
      std_time_ms: number;
      max_time_ms: number;
      mean_nodes_explored: number;
      queries_executed: number;
    };
    astar: {
      algorithm: string;
      mean_time_ms: number;
      std_time_ms: number;
      max_time_ms: number;
      mean_nodes_explored: number;
      queries_executed: number;
    };
  };
  speedup: {
    astar_vs_dijkstra: number;
  };
}

export default function ScalabilityPage() {
  const [data, setData] = useState<ScalabilityResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const response = await fetch(
          "/data/processed/scalability_results.json",
        );
        if (!response.ok) throw new Error("Failed to load scalability data");
        const jsonData = await response.json();
        setData(jsonData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-linear-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-gray-900 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Loading Scalability Analysis...</p>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const chartData = data.map((d) => ({
    nodes: d.num_nodes,
    dijkstra: parseFloat(d.algorithms.dijkstra.mean_time_ms.toFixed(3)),
    astar: parseFloat(d.algorithms.astar.mean_time_ms.toFixed(3)),
    speedup: parseFloat(d.speedup.astar_vs_dijkstra.toFixed(2)),
  }));

  const nodesExploredData = data.map((d) => ({
    nodes: d.num_nodes,
    dijkstra: Math.round(d.algorithms.dijkstra.mean_nodes_explored),
    astar: Math.round(d.algorithms.astar.mean_nodes_explored),
  }));

  const avgSpeedup = (
    data.reduce((sum, d) => sum + d.speedup.astar_vs_dijkstra, 0) / data.length
  ).toFixed(2);

  return (
    <div className="min-h-screen bg-linear-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/research"
            className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-4 font-medium"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Research
          </Link>
          <div className="flex items-center gap-3 mb-4">
            <div className="rounded-lg bg-yellow-100 p-3">
              <Zap className="w-6 h-6 text-yellow-600" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900">
                Scalability Analysis
              </h1>
              <p className="text-lg text-gray-600 mt-2">
                Algorithm performance benchmarks on networks up to 500 nodes
              </p>
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-12">
          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Network Sizes Tested
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">
                {data.length}
              </div>
              <p className="text-xs text-gray-500 mt-1">57 to 500 nodes</p>
            </CardContent>
          </Card>

          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Average A* Speedup
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">
                {avgSpeedup}x
              </div>
              <p className="text-xs text-gray-500 mt-1">vs Dijkstra</p>
            </CardContent>
          </Card>

          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Best Speedup
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-600">
                {Math.max(
                  ...data.map((d) => d.speedup.astar_vs_dijkstra),
                ).toFixed(2)}
                x
              </div>
              <p className="text-xs text-gray-500 mt-1">
                at {data[data.length - 1].num_nodes} nodes
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Largest Network
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-orange-600">
                {data[data.length - 1].num_nodes}
              </div>
              <p className="text-xs text-gray-500 mt-1">nodes tested</p>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-12">
          {/* Execution Time Chart */}
          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader>
              <CardTitle className="text-gray-900 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-600" />
                Execution Time (ms)
              </CardTitle>
              <CardDescription>
                Mean execution time vs network size
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="nodes" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#fff",
                      border: "1px solid #e5e7eb",
                    }}
                    labelStyle={{ color: "#374151" }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="dijkstra"
                    stroke="#3b82f6"
                    dot={{ fill: "#3b82f6" }}
                    name="Dijkstra"
                  />
                  <Line
                    type="monotone"
                    dataKey="astar"
                    stroke="#10b981"
                    dot={{ fill: "#10b981" }}
                    name="A*"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Speedup Chart */}
          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader>
              <CardTitle className="text-gray-900 flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-600" />
                A* Speedup vs Dijkstra
              </CardTitle>
              <CardDescription>
                Performance gain across network sizes
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="nodes" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#fff",
                      border: "1px solid #e5e7eb",
                    }}
                    labelStyle={{ color: "#374151" }}
                  />
                  <Bar dataKey="speedup" fill="#f59e0b" name="Speedup (x)" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Nodes Explored Chart */}
        <Card className="bg-white border-gray-200 shadow-lg mb-12">
          <CardHeader>
            <CardTitle className="text-gray-900">
              Nodes Explored by Algorithm
            </CardTitle>
            <CardDescription>
              Graph search efficiency comparison
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={nodesExploredData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="nodes" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#fff",
                    border: "1px solid #e5e7eb",
                  }}
                  labelStyle={{ color: "#374151" }}
                />
                <Legend />
                <Bar dataKey="dijkstra" fill="#3b82f6" name="Dijkstra" />
                <Bar dataKey="astar" fill="#10b981" name="A*" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Detailed Results Table */}
        <Card className="bg-white border-gray-200 shadow-lg mb-12">
          <CardHeader>
            <CardTitle className="text-gray-900">
              Detailed Benchmark Results
            </CardTitle>
            <CardDescription>
              Complete performance metrics for each network size
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 text-gray-700 font-semibold">
                      Network
                    </th>
                    <th className="text-right py-3 px-4 text-gray-700 font-semibold">
                      Dijkstra (ms)
                    </th>
                    <th className="text-right py-3 px-4 text-gray-700 font-semibold">
                      A* (ms)
                    </th>
                    <th className="text-right py-3 px-4 text-gray-700 font-semibold">
                      Speedup
                    </th>
                    <th className="text-right py-3 px-4 text-gray-700 font-semibold">
                      Nodes Explored
                    </th>
                    <th className="text-right py-3 px-4 text-gray-700 font-semibold">
                      Edges
                    </th>
                    <th className="text-right py-3 px-4 text-gray-700 font-semibold">
                      Density
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((result, idx) => (
                    <tr
                      key={idx}
                      className="border-b border-gray-200 hover:bg-gray-50 transition-colors"
                    >
                      <td className="py-3 px-4 text-gray-900 font-medium">
                        {result.num_nodes} nodes
                      </td>
                      <td className="text-right py-3 px-4 text-blue-600 font-mono">
                        {result.algorithms.dijkstra.mean_time_ms.toFixed(3)}
                      </td>
                      <td className="text-right py-3 px-4 text-green-600 font-mono">
                        {result.algorithms.astar.mean_time_ms.toFixed(3)}
                      </td>
                      <td className="text-right py-3 px-4">
                        <span
                          className={`px-2 py-1 rounded text-sm font-medium ${
                            result.speedup.astar_vs_dijkstra > 1.5
                              ? "bg-green-100 text-green-700"
                              : result.speedup.astar_vs_dijkstra < 1
                                ? "bg-yellow-100 text-yellow-700"
                                : "bg-blue-100 text-blue-700"
                          }`}
                        >
                          {result.speedup.astar_vs_dijkstra.toFixed(2)}x
                        </span>
                      </td>
                      <td className="text-right py-3 px-4 text-gray-700">
                        {Math.round(
                          result.algorithms.dijkstra.mean_nodes_explored,
                        )}{" "}
                        /{" "}
                        {Math.round(
                          result.algorithms.astar.mean_nodes_explored,
                        )}
                      </td>
                      <td className="text-right py-3 px-4 text-gray-600">
                        {result.num_edges}
                      </td>
                      <td className="text-right py-3 px-4 text-gray-600">
                        {result.density.toFixed(3)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Key Findings */}
        <Card className="bg-white border-gray-200 shadow-lg">
          <CardHeader>
            <CardTitle className="text-gray-900">Key Findings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm font-semibold text-blue-700 mb-2">
                Average Performance
              </p>
              <p className="text-gray-700">
                A* achieves an average speedup of{" "}
                <span className="font-bold text-blue-700">{avgSpeedup}x</span>{" "}
                over Dijkstra across all network sizes, demonstrating consistent
                optimization benefits through heuristic-guided search.
              </p>
            </div>

            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <p className="text-sm font-semibold text-green-700 mb-2">
                Scalability Insight
              </p>
              <p className="text-gray-700">
                A* speedup improves with larger networks (1.29x at 57 nodes →
                2.45x at 500 nodes), indicating that the heuristic guidance
                becomes more effective as the search space grows, making A*
                ideal for real-world transit networks.
              </p>
            </div>

            <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <p className="text-sm font-semibold text-yellow-700 mb-2">
                Graph Density Impact
              </p>
              <p className="text-gray-700">
                Performance varies inversely with graph density. Sparser graphs
                (density 0.02-0.05) benefit more from A*'s pruning, while denser
                graphs show smaller speedups, suggesting algorithm selection
                should consider network topology.
              </p>
            </div>

            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
              <p className="text-sm font-semibold text-purple-700 mb-2">
                Research Implication
              </p>
              <p className="text-gray-700">
                These benchmarks validate that informed heuristic-based search
                (A*) significantly outperforms exhaustive search (Dijkstra) in
                realistic metro networks, justifying the additional algorithmic
                complexity for production route optimization systems.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
