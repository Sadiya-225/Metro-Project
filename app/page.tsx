"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  Database,
  GitCompareArrows,
  MapPin,
  TrendingUp,
} from "lucide-react";
import StationAutocomplete from "@/components/StationAutocomplete";
import RouteMap from "@/components/RouteMap";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useAlert } from "@/components/AlertProvider";
import { RouteResponse, Station, getStations, optimizeRoute } from "@/lib/api";

export default function Home() {
  const { showAlert } = useAlert();
  const [source, setSource] = useState<Station | null>(null);
  const [destination, setDestination] = useState<Station | null>(null);
  const [algorithm, setAlgorithm] = useState("dijkstra");
  const [route, setRoute] = useState<RouteResponse | null>(null);
  const [stations, setStations] = useState<Station[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getStations().then(setStations).catch(console.error);
  }, []);

  const handleOptimize = async () => {
    if (!source || !destination) {
      showAlert({
        title: "Validation Error",
        message: "Please select both source and destination stations.",
        variant: "warning",
      });
      return;
    }

    setLoading(true);
    try {
      const result = await optimizeRoute({
        source: source.station_name,
        destination: destination.station_name,
        algorithm,
        k_paths: 3,
      });
      setRoute(result);
    } catch (error) {
      console.error("Error optimizing route:", error);
      showAlert({
        title: "Connection Error",
        message:
          "Failed to optimize route. Make sure the backend is running on port 8000.",
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  const renderPath = (path: string[], highlights: string[]) => (
    <div className="flex flex-wrap gap-2">
      {path.map((station, index) => (
        <div key={`${station}-${index}`} className="flex items-center">
          <span
            className={`rounded-full px-3 py-1 text-sm ${
              highlights.includes(station)
                ? "bg-red-100 font-semibold text-red-700"
                : "bg-white text-gray-700"
            }`}
          >
            {station}
          </span>
          {index < path.length - 1 && (
            <ArrowRight className="mx-1 h-4 w-4 text-gray-400" />
          )}
        </div>
      ))}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <header className="border-b bg-white shadow-sm">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
                Metro Route Intelligence
              </h1>
              <p className="mt-1 text-sm sm:text-sm text-gray-600">
                Shortest Path vs Real Time in Public Transport System
              </p>
            </div>
            <div className="flex flex-wrap gap-2 sm:gap-3">
              <Link href="/data-setup">
                <Button className="bg-gradient-to-r from-green-500 to-teal-500 text-white shadow-lg transition-all duration-200 hover:from-green-600 hover:to-teal-600 hover:shadow-xl active:scale-95 text-sm sm:text-sm px-3 py-2 font-semibold">
                  <Database className="mr-1.5 h-3.5 w-3.5 sm:h-4 sm:w-4" />
                  <span className="hidden sm:inline">Data Setup</span>
                  <span className="sm:hidden">Data</span>
                </Button>
              </Link>
              <Link href="/bottlenecks">
                <Button className="bg-gradient-to-r from-orange-500 to-red-500 text-white shadow-lg transition-all duration-200 hover:from-orange-600 hover:to-red-600 hover:shadow-xl active:scale-95 text-sm sm:text-sm px-3 py-2 font-semibold">
                  <AlertTriangle className="mr-1.5 h-3.5 w-3.5 sm:h-4 sm:w-4" />
                  <span className="hidden sm:inline">Bottlenecks</span>
                  <span className="sm:hidden">Delays</span>
                </Button>
              </Link>
              <Link href="/ml-prediction">
                <Button className="bg-gradient-to-r from-purple-500 to-indigo-600 text-white shadow-lg transition-all duration-200 hover:from-purple-600 hover:to-indigo-700 hover:shadow-xl active:scale-95 text-sm sm:text-sm px-3 py-2 font-semibold">
                  <TrendingUp className="mr-1.5 h-3.5 w-3.5 sm:h-4 sm:w-4" />
                  <span className="hidden sm:inline">ML Prediction</span>
                  <span className="sm:hidden">ML</span>
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="space-y-6 lg:col-span-1">
            <Card className="bg-white p-6 shadow-lg">
              <h2 className="mb-4 flex items-center text-xl font-semibold">
                <MapPin className="mr-2 h-5 w-5 text-blue-600" />
                Route Selection
              </h2>

              <div className="space-y-4">
                <StationAutocomplete
                  onSelect={setSource}
                  placeholder="Select Source Station"
                  label="From"
                />
                <div className="flex justify-center -mb-4">
                  <ArrowRight className="h-6 w-6 text-gray-400" />
                </div>
                <StationAutocomplete
                  onSelect={setDestination}
                  placeholder="Select Destination Station"
                  label="To"
                />
                <div>
                  <label className="mb-2 block text-sm font-medium">
                    Algorithm
                  </label>
                  <select
                    value={algorithm}
                    onChange={(event) => setAlgorithm(event.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="dijkstra">Dijkstra</option>
                    <option value="astar">A*</option>
                    <option value="yen">Yen&apos;s K-Shortest Paths</option>
                  </select>
                </div>
                <Button
                  onClick={handleOptimize}
                  disabled={loading || !source || !destination}
                  className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 py-6 text-lg font-bold text-white shadow-lg transition-all duration-200 hover:from-blue-600 hover:to-cyan-600 hover:shadow-xl active:scale-95"
                >
                  {loading ? "Optimizing..." : "Find Optimal Route"}
                </Button>
              </div>
            </Card>

            {route && (
              <Card className="bg-white p-6 shadow-lg">
                <h3 className="mb-4 text-lg font-semibold">
                  Route Intelligence
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between rounded-lg bg-green-50 p-3">
                    <span className="text-sm font-medium">
                      Shortest Distance
                    </span>
                    <span className="text-lg font-bold text-green-700">
                      {route.distance.toFixed(2)} km
                    </span>
                  </div>
                  <div className="flex items-center justify-between rounded-lg bg-blue-50 p-3">
                    <span className="text-sm font-medium">Scheduled ETA</span>
                    <span className="text-lg font-bold text-blue-700">
                      {route.estimated_time.toFixed(1)} min
                    </span>
                  </div>
                  <div className="flex items-center justify-between rounded-lg bg-red-50 p-3">
                    <span className="text-sm font-medium">Delay-Aware ETA</span>
                    <span className="text-lg font-bold text-red-700">
                      {route.actual_time.toFixed(1)} min
                    </span>
                  </div>
                  <div className="flex items-center justify-between rounded-lg bg-orange-50 p-3">
                    <span className="text-sm font-medium">ETA Deviation</span>
                    <span className="text-lg font-bold text-orange-700">
                      +{route.eta_deviation.toFixed(1)} min
                    </span>
                  </div>
                  <div className="flex items-center justify-between rounded-lg bg-purple-50 p-3">
                    <span className="text-sm font-medium">
                      Route Divergence
                    </span>
                    <span className="text-lg font-bold text-purple-700">
                      {(route.route_divergence_score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between rounded-lg bg-yellow-50 p-3">
                    <span className="text-sm font-medium">Transfer Count</span>
                    <span className="text-lg font-bold text-yellow-700">
                      {route.transfer_count}
                    </span>
                  </div>
                </div>

                {route.bottleneck_stations.length > 0 && (
                  <div className="mt-4 rounded-lg border border-yellow-200 bg-yellow-50 p-3">
                    <div className="flex items-start">
                      <AlertTriangle className="mr-2 mt-0.5 h-5 w-5 text-yellow-600" />
                      <div>
                        <p className="text-sm font-medium text-yellow-800">
                          Transfer Bottleneck Alerts
                        </p>
                        <p className="mt-1 text-sm text-yellow-700">
                          {route.bottleneck_stations.join(", ")}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </Card>
            )}
          </div>

          <div className="lg:col-span-2">
            <Card className="bg-white p-6 shadow-lg">
              <h2 className="mb-4 flex items-center text-xl font-semibold">
                <GitCompareArrows className="mr-2 h-5 w-5 text-blue-600" />
                Route Visualization
              </h2>

              {route && (
                <div className="mb-4 space-y-4">
                  <div className="rounded-lg bg-green-50 p-4">
                    <h3 className="mb-2 font-semibold text-green-900">
                      Shortest Path
                    </h3>
                    {renderPath(route.shortest_path, route.bottleneck_stations)}
                  </div>
                  <div className="rounded-lg bg-red-50 p-4">
                    <h3 className="mb-2 font-semibold text-red-900">
                      Delay-Aware Actual Route
                    </h3>
                    {renderPath(route.actual_path, route.bottleneck_stations)}
                  </div>
                </div>
              )}

              <RouteMap
                source={source}
                destination={destination}
                route={route}
                stations={stations}
              />

              <div className="mt-4 grid grid-cols-2 gap-4 text-sm md:grid-cols-5">
                <div className="flex items-center">
                  <div className="mr-2 h-4 w-4 rounded-full bg-blue-500"></div>
                  <span>Regular Station</span>
                </div>
                <div className="flex items-center">
                  <div className="mr-2 h-4 w-4 rounded-full bg-red-500"></div>
                  <span>Interchange</span>
                </div>
                <div className="flex items-center">
                  <div className="mr-2 h-4 w-4 rounded-full bg-green-600"></div>
                  <span>Shortest Path</span>
                </div>
                <div className="flex items-center">
                  <div className="mr-2 h-4 w-4 rounded-full bg-red-600"></div>
                  <span>Actual Route</span>
                </div>
                <div className="flex items-center">
                  <div className="mr-2 h-4 w-4 rounded-full bg-yellow-500"></div>
                  <span>Transfer/Congestion</span>
                </div>
              </div>
            </Card>
          </div>
        </div>

        {route && route.alternative_routes.length > 0 && (
          <Card className="mt-6 bg-white p-6 shadow-lg rounded-xl">
            <h3 className="mb-4 text-xl font-bold text-gray-900 flex items-center">
              <GitCompareArrows className="mr-2 h-5 w-5 text-purple-600" />
              Alternative K-Paths
            </h3>
            <div className="grid gap-4 sm:grid-cols-1 lg:grid-cols-2">
              {route.alternative_routes.map((alternative, index) => (
                <div
                  key={index}
                  className="rounded-xl border-2 border-gray-200 p-5 hover:border-purple-400 hover:shadow-md transition-all duration-200 bg-gradient-to-br from-white to-purple-50"
                >
                  <div className="flex items-center justify-between mb-3">
                    <p className="font-bold text-lg text-purple-700">
                      Alternative {index + 1}
                    </p>
                    {index === 0 && (
                      <span className="text-sm bg-green-100 text-green-700 px-2 py-1 rounded-full font-semibold">
                        Recommended
                      </span>
                    )}
                  </div>
                  <div className="mt-3 mb-4">
                    {renderPath(alternative.path, [])}
                  </div>
                  <div className="flex flex-wrap gap-3 text-sm border-t pt-3">
                    <span className="flex items-center bg-white px-3 py-1.5 rounded-lg shadow-sm">
                      <MapPin className="mr-1.5 h-4 w-4 text-blue-600" />
                      <strong className="mr-1">Distance:</strong>
                      {alternative.distance.toFixed(2)} km
                    </span>
                    <span className="flex items-center bg-white px-3 py-1.5 rounded-lg shadow-sm">
                      <ArrowRight className="mr-1.5 h-4 w-4 text-green-600" />
                      <strong className="mr-1">Time:</strong>
                      {alternative.time.toFixed(1)} min
                    </span>
                    <span className="flex items-center bg-white px-3 py-1.5 rounded-lg shadow-sm">
                      <GitCompareArrows className="mr-1.5 h-4 w-4 text-orange-600" />
                      <strong className="mr-1">Transfers:</strong>
                      {alternative.transfer_count}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        <Card className="mt-6 bg-white p-6 shadow-lg">
          <h3 className="mb-3 text-lg font-semibold">Algorithm Information</h3>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="rounded-lg border p-4">
              <h4 className="font-semibold text-blue-700">Dijkstra</h4>
              <p className="mt-2 text-sm text-gray-600">
                Optimizes the route on scheduled edge weights derived from GTFS
                travel times.
              </p>
            </div>
            <div className="rounded-lg border p-4">
              <h4 className="font-semibold text-green-700">A*</h4>
              <p className="mt-2 text-sm text-gray-600">
                Uses straight-line travel-time heuristics to accelerate search
                on the generated graph.
              </p>
            </div>
            <div className="rounded-lg border p-4">
              <h4 className="font-semibold text-purple-700">
                Yen&apos;s K-Shortest Paths
              </h4>
              <p className="mt-2 text-sm text-gray-600">
                Surfaces alternative itineraries to compare bottlenecks,
                divergence, and transfer risk.
              </p>
            </div>
          </div>
        </Card>
      </main>

      <footer className="mt-12 border-t bg-white">
        <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-600">
            Metro Route Intelligence Dashboard | Project by Ms. Sadiya Maheen
            Siddiqui
          </p>
        </div>
      </footer>
    </div>
  );
}
