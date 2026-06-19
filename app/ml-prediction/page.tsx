"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AlertCircle, ArrowLeft, Brain, TrendingUp, Zap } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useAlert } from "@/components/AlertProvider";
import {
  DelayPredictionResponse,
  ImportanceScore,
  Station,
  getMLMetrics,
  getStationImportance,
  getStations,
  predictDelay,
} from "@/lib/api";

interface MLMetrics {
  xgboost: {
    MAE: number;
    RMSE: number;
    R2: number;
  };
  random_forest: {
    MAE: number;
    RMSE: number;
    R2: number;
  };
  feature_importance: Record<string, number>;
}

interface ForecastPoint {
  hour: string;
  delay: number;
  risk: string;
}

export default function MLPredictionPage() {
  const { showAlert } = useAlert();
  const [stations, setStations] = useState<Station[]>([]);
  const [importanceScores, setImportanceScores] = useState<ImportanceScore[]>(
    [],
  );
  const [selectedStation, setSelectedStation] = useState("");
  const [hour, setHour] = useState(9);
  const [isPeak, setIsPeak] = useState(true);
  const [isWeekday, setIsWeekday] = useState(true);
  const [weather, setWeather] = useState("clear");
  const [prediction, setPrediction] = useState<DelayPredictionResponse | null>(
    null,
  );
  const [metrics, setMetrics] = useState<MLMetrics | null>(null);
  const [hourlyForecast, setHourlyForecast] = useState<ForecastPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [predicting, setPredicting] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const [stationsData, metricsData, importanceData] = await Promise.all([
          getStations(),
          getMLMetrics(),
          getStationImportance(),
        ]);
        setStations(stationsData);
        setMetrics(metricsData);
        setImportanceScores(importanceData);
        if (stationsData.length > 0) {
          setSelectedStation(stationsData[0].station_id);
        }
      } catch (error) {
        console.error("Error loading ML data:", error);
        showAlert({
          title: "Data Loading Error",
          message: "Failed to load ML data. Make sure the backend is running.",
          variant: "error",
        });
      } finally {
        setLoading(false);
      }
    };

    loadData().catch(console.error);
  }, []);

  const handlePredict = async () => {
    if (!selectedStation) return;
    setPredicting(true);
    try {
      const result = await predictDelay({
        station_id: selectedStation,
        hour,
        is_peak: isPeak,
        weekday: isWeekday,
        weather,
      });
      setPrediction(result);

      const forecastResults = await Promise.all(
        Array.from({ length: 24 }, (_, value) => value).map(
          async (forecastHour) => {
            const forecastPrediction = await predictDelay({
              station_id: selectedStation,
              hour: forecastHour,
              is_peak:
                (forecastHour >= 8 && forecastHour < 10) ||
                (forecastHour >= 17 && forecastHour < 20),
              weekday: isWeekday,
              weather,
            });
            return {
              hour: `${forecastHour}:00`,
              delay: forecastPrediction.predicted_delay,
              risk: forecastPrediction.risk_level,
            };
          },
        ),
      );
      setHourlyForecast(forecastResults);
    } catch (error) {
      console.error("Prediction error:", error);
      showAlert({
        title: "Prediction Error",
        message: "Failed to predict delay. Check backend logs for details.",
        variant: "error",
      });
    } finally {
      setPredicting(false);
    }
  };

  const featureImportanceData =
    metrics == null
      ? []
      : Object.entries(metrics.feature_importance)
          .map(([feature, importance]) => ({
            feature: feature
              .replace(/_/g, " ")
              .replace(/\b\w/g, (letter) => letter.toUpperCase()),
            importance: Number((importance * 100).toFixed(2)),
          }))
          .sort((a, b) => b.importance - a.importance)
          .slice(0, 10);

  const errorMetricsData =
    metrics == null
      ? []
      : [
          {
            metric: "MAE",
            XGBoost: metrics.xgboost.MAE,
            RandomForest: metrics.random_forest.MAE,
          },
          {
            metric: "RMSE",
            XGBoost: metrics.xgboost.RMSE,
            RandomForest: metrics.random_forest.RMSE,
          },
        ];

  const r2MetricsData =
    metrics == null
      ? []
      : [
          {
            model: "XGBoost",
            "R² Score": metrics.xgboost.R2 * 100,
          },
          {
            model: "RandomForest",
            "R² Score": metrics.random_forest.R2 * 100,
          },
        ];

  const selectedStationName =
    stations.find((station) => station.station_id === selectedStation)
      ?.station_name ?? "N/A";

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-linear-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading ML Models...</p>
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
              <Brain className="mr-2 sm:mr-3 h-6 w-6 sm:h-8 sm:w-8 text-purple-600" />
              ML Delay Prediction
            </h1>
            <p className="mt-1 text-sm text-gray-600">
              XGBoost and Random Forest forecasting from the generated metro
              data pipeline
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
        {metrics && (
          <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
            <Card className="bg-white p-6">
              <p className="text-sm text-gray-600">XGBoost MAE</p>
              <p className="text-3xl font-bold text-purple-700">
                {metrics.xgboost.MAE.toFixed(3)}
              </p>
            </Card>
            <Card className="bg-white p-6">
              <p className="text-sm text-gray-600">XGBoost RMSE</p>
              <p className="text-3xl font-bold text-blue-700">
                {metrics.xgboost.RMSE.toFixed(3)}
              </p>
            </Card>
            <Card className="bg-white p-6">
              <p className="text-sm text-gray-600">XGBoost R2</p>
              <p className="text-3xl font-bold text-green-700">
                {(metrics.xgboost.R2 * 100).toFixed(1)}%
              </p>
            </Card>
          </div>
        )}

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="space-y-6 lg:col-span-1">
            <Card className="bg-white p-6 shadow-lg">
              <h2 className="mb-4 flex items-center text-xl font-semibold">
                <Brain className="mr-2 h-5 w-5 text-purple-600" />
                Predict Delay
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="mb-2 block text-sm font-medium">
                    Select Station
                  </label>
                  <select
                    value={selectedStation}
                    onChange={(event) => setSelectedStation(event.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    {stations.map((station) => (
                      <option
                        key={station.station_id}
                        value={station.station_id}
                      >
                        {station.station_name} ({station.line})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium">
                    Hour of Day
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="23"
                    value={hour}
                    onChange={(event) =>
                      setHour(parseInt(event.target.value, 10))
                    }
                    className="w-full"
                  />
                  <p className="text-center text-lg font-bold text-purple-600">
                    {hour}:00
                  </p>
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium">
                    Peak Hour
                  </label>
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      onClick={() => setIsPeak(true)}
                      className={
                        isPeak
                          ? "flex-1 bg-purple-600 text-white"
                          : "flex-1 bg-gray-100 text-gray-700"
                      }
                    >
                      Yes
                    </Button>
                    <Button
                      type="button"
                      onClick={() => setIsPeak(false)}
                      className={
                        !isPeak
                          ? "flex-1 bg-purple-600 text-white"
                          : "flex-1 bg-gray-100 text-gray-700"
                      }
                    >
                      No
                    </Button>
                  </div>
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium">
                    Day Type
                  </label>
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      onClick={() => setIsWeekday(true)}
                      className={
                        isWeekday
                          ? "flex-1 bg-purple-600 text-white"
                          : "flex-1 bg-gray-100 text-gray-700"
                      }
                    >
                      Weekday
                    </Button>
                    <Button
                      type="button"
                      onClick={() => setIsWeekday(false)}
                      className={
                        !isWeekday
                          ? "flex-1 bg-purple-600 text-white"
                          : "flex-1 bg-gray-100 text-gray-700"
                      }
                    >
                      Weekend
                    </Button>
                  </div>
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium">
                    Weather
                  </label>
                  <select
                    value={weather}
                    onChange={(event) => setWeather(event.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="clear">Clear</option>
                    <option value="rain">Rain</option>
                    <option value="fog">Fog</option>
                    <option value="storm">Storm</option>
                  </select>
                </div>
                <Button
                  onClick={handlePredict}
                  disabled={predicting || !selectedStation}
                  className="w-full bg-linear-to-r from-purple-500 to-pink-500 py-6 text-lg font-bold text-white shadow-lg transition-all duration-200 hover:from-purple-600 hover:to-pink-600 hover:shadow-xl active:scale-95"
                >
                  {predicting ? "Predicting..." : "Predict Delay"}
                </Button>
              </div>
            </Card>

            {prediction && (
              <Card className="bg-white p-6 shadow-lg">
                <h3 className="mb-4 text-lg font-semibold">
                  Prediction Result
                </h3>
                <div className="space-y-3">
                  <div className="rounded-lg bg-purple-50 p-4">
                    <p className="text-sm text-gray-600">Predicted Delay</p>
                    <p className="text-3xl font-bold text-purple-700">
                      {prediction.predicted_delay.toFixed(2)} min
                    </p>
                  </div>
                  <div className="rounded-lg bg-blue-50 p-4">
                    <p className="text-sm text-gray-600">Confidence</p>
                    <p className="text-2xl font-bold text-blue-700">
                      {prediction.confidence.toFixed(1)}%
                    </p>
                  </div>
                  <div className="rounded-lg bg-yellow-50 p-4">
                    <p className="text-sm text-gray-600">Risk Level</p>
                    <p className="text-2xl font-bold uppercase text-yellow-700">
                      {prediction.risk_level}
                    </p>
                  </div>
                </div>
              </Card>
            )}
          </div>

          <div className="space-y-6 lg:col-span-2">
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <Card className="bg-white p-6 shadow-lg">
                <h2 className="mb-4 flex items-center text-xl font-semibold">
                  <TrendingUp className="mr-2 h-5 w-5 text-red-600" />
                  Error Metrics (Lower is Better)
                </h2>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={errorMetricsData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="metric" />
                    <YAxis
                      domain={[0, "auto"]}
                      label={{
                        value: "Minutes",
                        angle: -90,
                        position: "insideLeft",
                      }}
                    />
                    <Tooltip formatter={(value: number) => value.toFixed(4)} />
                    <Legend />
                    <Bar
                      dataKey="XGBoost"
                      fill="#8B5CF6"
                      radius={[8, 8, 0, 0]}
                    />
                    <Bar
                      dataKey="RandomForest"
                      fill="#10B981"
                      radius={[8, 8, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
                <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                  <div className="rounded bg-purple-50 p-2">
                    <p className="font-semibold text-purple-700">XGBoost MAE</p>
                    <p className="text-lg font-bold text-purple-900">
                      {metrics?.xgboost.MAE.toFixed(4)}
                    </p>
                  </div>
                  <div className="rounded bg-green-50 p-2">
                    <p className="font-semibold text-green-700">RF MAE</p>
                    <p className="text-lg font-bold text-green-900">
                      {metrics?.random_forest.MAE.toFixed(4)}
                    </p>
                  </div>
                </div>
              </Card>

              <Card className="bg-white p-6 shadow-lg">
                <h2 className="mb-4 flex items-center text-xl font-semibold">
                  <TrendingUp className="mr-2 h-5 w-5 text-green-600" />
                  R² Score (Higher is Better)
                </h2>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={r2MetricsData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="model" />
                    <YAxis
                      domain={[
                        Math.min(
                          metrics?.xgboost.R2 ?? 0,
                          metrics?.random_forest.R2 ?? 0,
                        ) *
                          100 -
                          5,
                        100,
                      ]}
                      label={{
                        value: "Percentage (%)",
                        angle: -90,
                        position: "insideLeft",
                      }}
                    />
                    <Tooltip
                      formatter={(value: number) => `${value.toFixed(2)}%`}
                    />
                    <Bar
                      dataKey="R² Score"
                      fill="#3B82F6"
                      radius={[8, 8, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
                <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                  <div className="rounded bg-purple-50 p-2">
                    <p className="font-semibold text-purple-700">XGBoost R²</p>
                    <p className="text-lg font-bold text-purple-900">
                      {((metrics?.xgboost.R2 ?? 0) * 100).toFixed(2)}%
                    </p>
                  </div>
                  <div className="rounded bg-green-50 p-2">
                    <p className="font-semibold text-green-700">RF R²</p>
                    <p className="text-lg font-bold text-green-900">
                      {((metrics?.random_forest.R2 ?? 0) * 100).toFixed(2)}%
                    </p>
                  </div>
                </div>
              </Card>
            </div>

            <Card className="bg-white p-6 shadow-lg">
              <h2 className="mb-4 flex items-center text-xl font-semibold">
                <Zap className="mr-2 h-5 w-5 text-yellow-600" />
                Feature Importance
              </h2>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={featureImportanceData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="feature" type="category" width={150} />
                  <Tooltip />
                  <Bar
                    dataKey="importance"
                    fill="#F59E0B"
                    name="Importance (%)"
                  />
                </BarChart>
              </ResponsiveContainer>
            </Card>

            {hourlyForecast.length > 0 && (
              <Card className="bg-white p-6 shadow-lg">
                <h2 className="mb-4 flex items-center text-xl font-semibold">
                  <AlertCircle className="mr-2 h-5 w-5 text-orange-600" />
                  24-Hour Delay Forecast
                </h2>
                <p className="mb-4 text-sm text-gray-600">
                  Station: {selectedStationName}
                </p>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={hourlyForecast}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="hour" interval={2} />
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
                      dataKey="delay"
                      stroke="#8B5CF6"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            )}

            <Card className="bg-white p-6 shadow-lg">
              <h2 className="mb-4 text-xl font-semibold">
                Station Risk Scores
              </h2>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                {importanceScores.slice(0, 10).map((station) => (
                  <div
                    key={station.station_id}
                    className="rounded-lg border p-4"
                  >
                    <p className="font-semibold text-gray-800">
                      {station.station_name}
                    </p>
                    <p className="text-sm text-gray-500">
                      Importance {station.importance_score} • routes{" "}
                      {station.route_count}
                    </p>
                    <p className="mt-2 text-sm text-gray-600">
                      Activity {station.activity_score.toFixed(2)} • Betweenness{" "}
                      {station.betweenness_centrality.toFixed(2)}
                    </p>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
