"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  AlertTriangle,
  ArrowLeft,
  Clock,
  MapPin,
  TrendingUp,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useAlert } from "@/components/AlertProvider";
import {
  DashboardAnalyticsResponse,
  getBottlenecks,
  getDashboardAnalytics,
  getDelayStats,
  getODPairs,
} from "@/lib/api";

interface DelayStats {
  overall: {
    mean: number;
    median: number;
    max: number;
    std: number;
  };
}

interface BottleneckStation {
  station_name: string;
  avg_delay: number;
  congestion_score: number;
  importance_score: number;
  is_interchange: boolean;
  zone: string;
  line: string;
  risk_score: number;
}

interface ODPair {
  source: string;
  destination: string;
  shortest_path_time: number;
  scheduled_time: number;
  actual_delay_time: number;
  inefficiency_ratio: number;
  bottleneck_station: string;
  transfer_count: number;
}

const COLORS = ["#EF4444", "#F59E0B", "#10B981", "#6366F1", "#06B6D4"];

export default function BottlenecksPage() {
  const { showAlert } = useAlert();
  const [delayStats, setDelayStats] = useState<DelayStats | null>(null);
  const [bottlenecks, setBottlenecks] = useState<BottleneckStation[]>([]);
  const [analytics, setAnalytics] = useState<DashboardAnalyticsResponse | null>(
    null,
  );
  const [odPairs, setODPairs] = useState<ODPair[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const [delayStatsData, bottleneckData, analyticsData, odData] =
          await Promise.all([
            getDelayStats(),
            getBottlenecks(15),
            getDashboardAnalytics(),
            getODPairs(20),
          ]);
        setDelayStats(delayStatsData);
        setBottlenecks(bottleneckData.bottlenecks);
        setAnalytics(analyticsData);
        setODPairs(odData.inefficient_routes);
      } catch (error) {
        console.error("Error loading bottleneck analytics:", error);
        showAlert({
          title: "Data Loading Error",
          message:
            "Failed to load bottleneck analytics. Make sure the backend is running.",
          variant: "error",
        });
      } finally {
        setLoading(false);
      }
    };

    loadData().catch(console.error);
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-linear-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading Bottleneck Analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-linear-to-br from-blue-50 to-indigo-100">
      <header className="border-b bg-white shadow-sm">
        <div className="mx-auto flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div>
            <h1 className="flex items-center text-2xl sm:text-3xl font-bold text-gray-900">
              <AlertTriangle className="mr-2 sm:mr-3 h-6 w-6 sm:h-8 sm:w-8 text-orange-600" />
              Bottleneck Analytics
            </h1>
            <p className="mt-1 text-sm text-gray-600">
              Data-driven congestion hotspots and OD inefficiency analysis
            </p>
          </div>
          <Link href="/" className="w-full sm:w-auto">
            <Button className="w-full sm:w-auto bg-linear-to-r from-blue-500 to-cyan-500 text-white shadow-lg transition-all duration-200 hover:from-blue-600 hover:to-cyan-600 hover:shadow-xl active:scale-95">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Route Intelligence
            </Button>
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {delayStats && (
          <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
            <Card className="bg-white p-4">
              <p className="text-sm text-gray-600">Mean Delay</p>
              <p className="text-2xl font-bold text-blue-700">
                {delayStats.overall.mean.toFixed(2)} min
              </p>
            </Card>
            <Card className="bg-white p-4">
              <p className="text-sm text-gray-600">Median Delay</p>
              <p className="text-2xl font-bold text-green-700">
                {delayStats.overall.median.toFixed(2)} min
              </p>
            </Card>
            <Card className="bg-white p-4">
              <p className="text-sm text-gray-600">Max Delay</p>
              <p className="text-2xl font-bold text-red-700">
                {delayStats.overall.max.toFixed(2)} min
              </p>
            </Card>
            <Card className="bg-white p-4">
              <p className="text-sm text-gray-600">Std Deviation</p>
              <p className="text-2xl font-bold text-orange-700">
                {delayStats.overall.std.toFixed(2)} min
              </p>
            </Card>
          </div>
        )}

        <div className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Left Column - Top Delayed Stations */}
          <Card className="bg-white p-6 shadow-lg">
            <h2 className="mb-4 flex items-center text-xl font-semibold">
              <AlertTriangle className="mr-2 h-5 w-5 text-red-600" />
              Top Delayed Stations
            </h2>
            <div className="space-y-2">
              {bottlenecks.slice(0, 10).map((station, index) => (
                <div
                  key={station.station_name}
                  className="flex items-center justify-between rounded-lg bg-gray-50 p-3.75"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-6 text-lg font-bold text-gray-400">
                      {index + 1}
                    </span>
                    <div>
                      <p className="font-semibold text-gray-800">
                        {station.station_name}
                      </p>
                      <p className="text-sm text-gray-500">
                        {station.line} • {station.zone}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-red-600">
                      {station.avg_delay.toFixed(2)} min
                    </p>
                    <p className="text-sm text-gray-500">
                      Risk {station.risk_score.toFixed(2)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Right Column - Line Delay Comparison & Interchange Risk Ranking */}
          <div className="space-y-6">
            <Card className="bg-white p-6 shadow-lg">
              <h2 className="mb-4 flex items-center text-xl font-semibold">
                <TrendingUp className="mr-2 h-5 w-5 text-blue-600" />
                Line Delay Comparison
              </h2>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={analytics?.line_delay_comparison ?? []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="line" />
                  <YAxis
                    label={{
                      value: "Delay (min)",
                      angle: -90,
                      position: "insideLeft",
                    }}
                  />
                  <Tooltip />
                  <Legend />
                  <Bar
                    dataKey="avg_delay"
                    fill="#3B82F6"
                    name="Average Delay"
                  />
                </BarChart>
              </ResponsiveContainer>
            </Card>

            <Card className="bg-white p-6 shadow-lg">
              <h2 className="flex items-center text-xl font-semibold">
                <AlertTriangle className="mr-2 h-5 w-5 text-red-600" />
                Interchange Risk Ranking
              </h2>
              <div className="grid gap-4">
                {bottlenecks
                  .filter((station) => station.is_interchange)
                  .sort((a, b) => b.risk_score - a.risk_score)
                  .slice(0, 5)
                  .map((station, index) => (
                    <div
                      key={station.station_name}
                      className="p-4 rounded-xl border-2 border-gray-200 bg-linear-to-br from-white to-red-50 hover:shadow-lg hover:border-red-300 transition-all duration-200"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div
                            className={`flex h-8 w-8 items-center justify-center rounded-full font-bold text-white text-md shadow-md ${
                              index === 0
                                ? "bg-red-600"
                                : index === 1
                                  ? "bg-orange-600"
                                  : "bg-yellow-600"
                            }`}
                          >
                            {index + 1}
                          </div>
                          <div>
                            <p className="font-bold text-md text-gray-900">
                              {station.station_name}
                            </p>
                            <p className="text-sm text-gray-600 mt-0.5">
                              {station.line}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-2xl font-bold text-red-600">
                            {station.risk_score.toFixed(2)}
                          </p>
                          <p className="text-xs text-gray-500 font-semibold">
                            Risk Score
                          </p>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3 mt-1 pt-3 border-t border-gray-200">
                        <div className="bg-white p-3 rounded-lg shadow-sm">
                          <p className="text-xs text-gray-500 font-semibold mb-0.5">
                            Avg Delay
                          </p>
                          <p className="text-lg font-bold text-orange-600 leading-none">
                            {station.avg_delay.toFixed(2)} min
                          </p>
                        </div>

                        <div className="bg-white p-3 rounded-lg shadow-sm">
                          <p className="text-xs text-gray-500 font-semibold mb-0.5">
                            Congestion
                          </p>
                          <p className="text-lg font-bold text-purple-600 leading-none">
                            {station.congestion_score.toFixed(1)}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
              {bottlenecks.filter((s) => s.is_interchange).length === 0 && (
                <p className="text-center text-gray-500 py-8">
                  No Interchange Stations Found in the Data.
                </p>
              )}
            </Card>
          </div>
        </div>

        <div className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card className="bg-white p-6 shadow-lg">
            <h2 className="mb-4 flex items-center text-xl font-semibold">
              <MapPin className="mr-2 h-5 w-5 text-green-600" />
              Zone Congestion
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={analytics?.zone_congestion ?? []}
                  dataKey="avg_congestion"
                  nameKey="zone"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={(entry) =>
                    `${entry.zone}: ${entry.avg_congestion.toFixed(1)}`
                  }
                >
                  {(analytics?.zone_congestion ?? []).map((entry, index) => (
                    <Cell
                      key={`${entry.zone}-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Card>

          <Card className="bg-white p-6 shadow-lg">
            <h2 className="mb-4 flex items-center text-xl font-semibold">
              <Clock className="mr-2 h-5 w-5 text-purple-600" />
              Hourly Delay Profile
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analytics?.hourly_delay_profile ?? []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" />
                <YAxis
                  label={{
                    value: "Delay (min)",
                    angle: -90,
                    position: "insideLeft",
                  }}
                />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="avg_delay"
                  stroke="#8B5CF6"
                  strokeWidth={2}
                  name="Average Delay"
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </div>

        <Card className="bg-white p-6 shadow-lg">
          <h2 className="mb-4 flex items-center text-xl font-semibold">
            <TrendingUp className="mr-2 h-5 w-5 text-orange-600" />
            OD Inefficiency Leaderboard
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left">#</th>
                  <th className="px-4 py-3 text-left">Source</th>
                  <th className="px-4 py-3 text-left">Destination</th>
                  <th className="px-4 py-3 text-right">Shortest</th>
                  <th className="px-4 py-3 text-right">Scheduled</th>
                  <th className="px-4 py-3 text-right">Actual</th>
                  <th className="px-4 py-3 text-right">Inefficiency</th>
                  <th className="px-4 py-3 text-left">Bottleneck</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {odPairs.slice(0, 15).map((pair, index) => (
                  <tr
                    key={`${pair.source}-${pair.destination}`}
                    className="hover:bg-gray-50"
                  >
                    <td className="px-4 py-3 text-gray-500">{index + 1}</td>
                    <td className="px-4 py-3 font-medium">{pair.source}</td>
                    <td className="px-4 py-3 font-medium">
                      {pair.destination}
                    </td>
                    <td className="px-4 py-3 text-right text-green-600">
                      {pair.shortest_path_time.toFixed(1)} min
                    </td>
                    <td className="px-4 py-3 text-right text-blue-600">
                      {pair.scheduled_time.toFixed(1)} min
                    </td>
                    <td className="px-4 py-3 text-right text-red-600">
                      {pair.actual_delay_time.toFixed(1)} min
                    </td>
                    <td className="px-4 py-3 text-right font-bold text-orange-600">
                      {pair.inefficiency_ratio.toFixed(2)}x
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {pair.bottleneck_station}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </main>
    </div>
  );
}
