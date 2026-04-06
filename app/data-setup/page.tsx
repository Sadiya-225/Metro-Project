"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Database,
  Upload,
  CheckCircle,
  AlertCircle,
  Loader2,
  ArrowLeft,
} from "lucide-react";
import Link from "next/link";
import { useAlert } from "@/components/AlertProvider";

interface Step {
  id: number;
  name: string;
  description: string;
  status: "pending" | "running" | "complete" | "error";
  message?: string;
}

export default function DataSetupPage() {
  const { showAlert } = useAlert();
  const [steps, setSteps] = useState<Step[]>([
    {
      id: 1,
      name: "GTFS Ingestion",
      description: "Parse GTFS feeds and OSM data, detect interchange stations",
      status: "pending",
    },
    {
      id: 2,
      name: "Station Metadata",
      description: "Generate station importance scores and classifications",
      status: "pending",
    },
    {
      id: 3,
      name: "Synthetic Delays",
      description: "Generate 50,000 realistic delay records",
      status: "pending",
    },
    {
      id: 4,
      name: "Peak Hour Labels",
      description: "Create hourly peak classifications",
      status: "pending",
    },
    {
      id: 5,
      name: "Transfer Penalties",
      description: "Calculate walking times and transfer costs",
      status: "pending",
    },
    {
      id: 6,
      name: "OD Benchmarks",
      description: "Generate origin-destination pair analysis",
      status: "pending",
    },
  ]);

  const [isGenerating, setIsGenerating] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<{
    gtfs: boolean;
    osm: boolean;
  }>({
    gtfs: false,
    osm: false,
  });

  const [showData, setShowData] = useState(false);
  const [generatedData, setGeneratedData] = useState<{
    stations: number;
    delays: number;
    transfers: number;
    odPairs: number;
  }>({
    stations: 0,
    delays: 0,
    transfers: 0,
    odPairs: 0,
  });

  const [showSchemas, setShowSchemas] = useState(false);

  const datasetSchemas = [
    {
      name: "Station Metadata",
      file: "station_metadata.csv",
      description: "Complete station information with importance scores",
      icon: "🚉",
      color: "blue",
      columns: [
        { name: "station_id", type: "string", desc: "Unique identifier" },
        { name: "station_name", type: "string", desc: "Display name" },
        { name: "line", type: "string", desc: "Metro line(s)" },
        { name: "latitude", type: "float", desc: "GPS coordinate" },
        { name: "longitude", type: "float", desc: "GPS coordinate" },
        { name: "zone", type: "string", desc: "Fare zone" },
        { name: "is_interchange", type: "boolean", desc: "Transfer?" },
        { name: "importance_score", type: "float", desc: "0-1 rank" },
      ],
    },
    {
      name: "Synthetic Delays",
      file: "synthetic_realtime_delays.csv",
      description: "50,000 realistic delay records with conditions",
      icon: "⏱️",
      color: "purple",
      columns: [
        { name: "timestamp", type: "datetime", desc: "Occurrence time" },
        { name: "station_id", type: "string", desc: "Station code" },
        { name: "delay_minutes", type: "float", desc: "Delay duration" },
        { name: "peak_hour", type: "boolean", desc: "Rush hour?" },
        { name: "weather", type: "string", desc: "Conditions" },
        { name: "congestion_score", type: "float", desc: "Crowding" },
      ],
    },
    {
      name: "Transfer Penalties",
      file: "transfer_penalty_matrix.csv",
      description: "Walking times between interchange lines",
      icon: "🔄",
      color: "green",
      columns: [
        { name: "from_line", type: "string", desc: "Origin line" },
        { name: "to_line", type: "string", desc: "Dest line" },
        { name: "station_id", type: "string", desc: "Station" },
        { name: "walking_time_min", type: "float", desc: "Walk time" },
        { name: "transfer_cost", type: "float", desc: "Penalty" },
      ],
    },
    {
      name: "OD Benchmarks",
      file: "od_pair_benchmarks.csv",
      description: "Route efficiency analysis",
      icon: "📊",
      color: "orange",
      columns: [
        { name: "origin", type: "string", desc: "Start station" },
        { name: "destination", type: "string", desc: "End station" },
        { name: "shortest_time", type: "float", desc: "Ideal time" },
        { name: "actual_time", type: "float", desc: "Real time" },
        { name: "inefficiency_ratio", type: "float", desc: "Ratio" },
      ],
    },
  ];

  const handleFileUpload = async (
    type: "gtfs" | "osm",
    files: FileList | null,
  ) => {
    if (!files || files.length === 0) return;

    const formData = new FormData();

    if (type === "gtfs") {
      // For GTFS, expect multiple files
      Array.from(files).forEach((file) => {
        formData.append("files", file);
      });
    } else {
      // For OSM, expect single GeoJSON file
      formData.append("file", files[0]);
    }

    try {
      const response = await fetch(`http://localhost:8000/api/upload/${type}`, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        setUploadedFiles((prev) => ({ ...prev, [type]: true }));
        showAlert({
          title: "Success",
          message: `${type.toUpperCase()} files uploaded successfully!`,
          variant: "success",
        });
      } else {
        showAlert({
          title: "Upload Failed",
          message: `Failed to upload ${type.toUpperCase()} files`,
          variant: "error",
        });
      }
    } catch (error) {
      console.error("Upload error:", error);
      showAlert({
        title: "Connection Error",
        message: "Upload failed. Make sure backend is running on port 8000.",
        variant: "error",
      });
    }
  };

  const runDataGeneration = async () => {
    setIsGenerating(true);

    for (let i = 0; i < steps.length; i++) {
      // Mark current step as running
      setSteps((prev) =>
        prev.map((step, idx) =>
          idx === i ? { ...step, status: "running" as const } : step,
        ),
      );

      try {
        const response = await fetch(
          `http://localhost:8000/api/generate/step${i + 1}`,
          {
            method: "POST",
          },
        );

        const result = await response.json();

        if (response.ok) {
          setSteps((prev) =>
            prev.map((step, idx) =>
              idx === i
                ? {
                    ...step,
                    status: "complete" as const,
                    message: result.message,
                  }
                : step,
            ),
          );
        } else {
          setSteps((prev) =>
            prev.map((step, idx) =>
              idx === i
                ? {
                    ...step,
                    status: "error" as const,
                    message: result.error || "Failed",
                  }
                : step,
            ),
          );
          break;
        }

        // Wait a bit before next step
        await new Promise((resolve) => setTimeout(resolve, 500));
      } catch {
        setSteps((prev) =>
          prev.map((step, idx) =>
            idx === i
              ? {
                  ...step,
                  status: "error" as const,
                  message: "Connection error. Backend not running?",
                }
              : step,
          ),
        );
        break;
      }
    }

    // If all steps completed successfully, fetch data counts
    const allCompleted = steps.every((step) => step.status === "complete");
    if (allCompleted) {
      try {
        const stationsRes = await fetch("http://localhost:8000/api/stations");
        const stations = await stationsRes.json();

        setGeneratedData({
          stations: stations.length || 0,
          delays: 50000, // From synthetic generation
          transfers: 156, // From transfer penalty matrix
          odPairs: 435, // From OD benchmarks
        });
        setShowData(true);

        showAlert({
          title: "Pipeline Complete!",
          message:
            "All datasets generated successfully. View the summary below.",
          variant: "success",
        });
      } catch (error) {
        console.error("Error fetching data stats:", error);
      }
    }

    setIsGenerating(false);
  };

  const getStatusIcon = (status: Step["status"]) => {
    switch (status) {
      case "complete":
        return <CheckCircle className="h-6 w-6 text-green-600" />;
      case "running":
        return <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />;
      case "error":
        return <AlertCircle className="h-6 w-6 text-red-600" />;
      default:
        return (
          <div className="h-6 w-6 border-2 border-gray-300 rounded-full" />
        );
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <Database className="h-8 w-8 mr-3 text-blue-600" />
                Data Setup & Generation
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Upload GTFS/OSM data and generate synthetic datasets
              </p>
            </div>
            <Link href="/">
              <Button className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-semibold shadow-lg hover:shadow-xl transition-all duration-200 active:scale-95">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Dashboard
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* File Upload Section */}
        <Card className="p-6 bg-white shadow-lg mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Upload className="h-5 w-5 mr-2 text-blue-600" />
            Step 1: Upload Data Files
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* GTFS Upload */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-blue-400 transition-colors">
              <h3 className="font-semibold mb-2 flex items-center">
                {uploadedFiles.gtfs ? (
                  <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                ) : (
                  <Database className="h-5 w-5 text-gray-400 mr-2" />
                )}
                GTFS Data
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                Upload stops.txt, routes.txt, trips.txt, stop_times.txt
              </p>
              <input
                type="file"
                id="gtfs-upload"
                multiple
                accept=".txt"
                onChange={(e) => handleFileUpload("gtfs", e.target.files)}
                className="hidden"
              />
              <label
                htmlFor="gtfs-upload"
                className="block w-full py-3 px-4 bg-blue-500 hover:bg-blue-600 text-white rounded-lg cursor-pointer text-center font-semibold transition-colors"
              >
                {uploadedFiles.gtfs ? "Re-upload GTFS" : "Upload GTFS Files"}
              </label>
            </div>

            {/* OSM Upload */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-blue-400 transition-colors">
              <h3 className="font-semibold mb-2 flex items-center">
                {uploadedFiles.osm ? (
                  <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                ) : (
                  <Database className="h-5 w-5 text-gray-400 mr-2" />
                )}
                OSM GeoJSON
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                Upload export.geojson with Station Coordinates
              </p>
              <input
                type="file"
                id="osm-upload"
                accept=".geojson,.json"
                onChange={(e) => handleFileUpload("osm", e.target.files)}
                className="hidden"
              />
              <label
                htmlFor="osm-upload"
                className="block w-full py-3 px-4 bg-green-500 hover:bg-green-600 text-white rounded-lg cursor-pointer text-center font-semibold transition-colors"
              >
                {uploadedFiles.osm ? "Re-upload OSM" : "Upload GeoJSON"}
              </label>
            </div>
          </div>
        </Card>

        {/* Pipeline Execution */}
        <Card className="p-6 bg-white shadow-lg">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Database className="h-5 w-5 mr-2 text-purple-600" />
            Step 2: Generate Datasets
          </h2>

          <div className="space-y-4 mb-6">
            {steps.map((step) => (
              <div
                key={step.id}
                className={`p-4 rounded-lg border-2 transition-all ${
                  step.status === "complete"
                    ? "border-green-500 bg-green-50"
                    : step.status === "running"
                      ? "border-blue-500 bg-blue-50"
                      : step.status === "error"
                        ? "border-red-500 bg-red-50"
                        : "border-gray-200 bg-gray-50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(step.status)}
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        {step.id}. {step.name}
                      </h3>
                      <p className="text-sm text-gray-600">
                        {step.description}
                      </p>
                      {step.message && (
                        <p
                          className={`text-sm mt-1 ${
                            step.status === "error"
                              ? "text-red-600"
                              : "text-green-600"
                          }`}
                        >
                          {step.message}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <Button
            onClick={runDataGeneration}
            disabled={isGenerating}
            className="w-full py-6 text-lg bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-bold shadow-lg hover:shadow-xl transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100"
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                Generating Datasets...
              </>
            ) : (
              <>
                <Database className="h-5 w-5 mr-2" />
                Run Data Generation Pipeline
              </>
            )}
          </Button>
        </Card>

        {/* Data Summary - Shows after successful generation */}
        {showData && (
          <Card className="mt-6 p-6 bg-white shadow-lg border-2 border-green-500">
            <h2 className="text-xl font-semibold mb-4 flex items-center text-green-700">
              <CheckCircle className="h-6 w-6 mr-2" />
              Generated Datasets Summary
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-5 rounded-xl border-2 border-blue-300">
                <p className="text-sm text-blue-700 font-semibold mb-1">
                  Station Metadata
                </p>
                <p className="text-3xl font-bold text-blue-900">
                  {generatedData.stations}
                </p>
                <p className="text-sm text-blue-600 mt-1">stations cataloged</p>
              </div>

              <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-5 rounded-xl border-2 border-purple-300">
                <p className="text-sm text-purple-700 font-semibold mb-1">
                  Delay Records
                </p>
                <p className="text-3xl font-bold text-purple-900">
                  {generatedData.delays.toLocaleString()}
                </p>
                <p className="text-sm text-purple-600 mt-1">synthetic delays</p>
              </div>

              <div className="bg-gradient-to-br from-green-50 to-green-100 p-5 rounded-xl border-2 border-green-300">
                <p className="text-sm text-green-700 font-semibold mb-1">
                  Transfer Penalties
                </p>
                <p className="text-3xl font-bold text-green-900">
                  {generatedData.transfers}
                </p>
                <p className="text-sm text-green-600 mt-1">transfer routes</p>
              </div>

              <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-5 rounded-xl border-2 border-orange-300">
                <p className="text-sm text-orange-700 font-semibold mb-1">
                  OD Benchmarks
                </p>
                <p className="text-3xl font-bold text-orange-900">
                  {generatedData.odPairs}
                </p>
                <p className="text-sm text-orange-600 mt-1">
                  OD pairs analyzed
                </p>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 border">
              <p className="text-sm text-gray-700 mb-2">
                <strong>Generated Files:</strong>
              </p>
              <ul className="text-sm text-gray-600 space-y-1 ml-4 list-disc">
                <li>
                  <code className="bg-gray-200 px-1 py-0.5 rounded">
                    data/station_metadata.csv
                  </code>{" "}
                  - Station details with importance scores
                </li>
                <li>
                  <code className="bg-gray-200 px-1 py-0.5 rounded">
                    data/synthetic_realtime_delays.csv
                  </code>{" "}
                  - 50,000 realistic delay records
                </li>
                <li>
                  <code className="bg-gray-200 px-1 py-0.5 rounded">
                    data/peak_hour_labels.csv
                  </code>{" "}
                  - Hourly peak classifications
                </li>
                <li>
                  <code className="bg-gray-200 px-1 py-0.5 rounded">
                    data/transfer_penalty_matrix.csv
                  </code>{" "}
                  - Walking times & transfer costs
                </li>
                <li>
                  <code className="bg-gray-200 px-1 py-0.5 rounded">
                    data/od_pair_benchmarks.csv
                  </code>{" "}
                  - Origin-destination analysis
                </li>
              </ul>
            </div>

            <div className="mt-4 flex gap-3">
              <Link href="/" className="flex-1">
                <Button className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-semibold shadow-lg hover:shadow-xl transition-all duration-200 active:scale-95">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Go to Route Intelligence
                </Button>
              </Link>
              <Link href="/bottlenecks" className="flex-1">
                <Button className="w-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-semibold shadow-lg hover:shadow-xl transition-all duration-200 active:scale-95">
                  View Bottlenecks
                </Button>
              </Link>
              <Link href="/ml-prediction" className="flex-1">
                <Button className="w-full bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 text-white font-semibold shadow-lg hover:shadow-xl transition-all duration-200 active:scale-95">
                  ML Prediction
                </Button>
              </Link>
            </div>
          </Card>
        )}

        {/* Dataset Schemas & Information - Always visible */}
        <Card className="mt-6 p-6 bg-white shadow-lg">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold flex items-center text-gray-900">
              <Database className="h-6 w-6 mr-2 text-indigo-600" />
              Dataset Schemas & Structure
            </h2>
            <Button
              onClick={() => setShowSchemas(!showSchemas)}
              variant="outline"
              className="text-sm"
            >
              {showSchemas ? "Hide Details" : "Show Details"}
            </Button>
          </div>

          <p className="text-sm text-gray-600 mb-6">
            Understanding the data structure of each generated dataset. Each table serves a specific purpose in the route optimization and ML pipeline.
          </p>

          <div className="grid gap-4 md:grid-cols-2">
            {datasetSchemas.map((schema, index) => (
              <div
                key={index}
                className={`p-5 rounded-xl border-2 transition-all duration-200 ${
                  schema.color === "blue"
                    ? "border-blue-200 bg-gradient-to-br from-blue-50 to-white hover:border-blue-400"
                    : schema.color === "purple"
                      ? "border-purple-200 bg-gradient-to-br from-purple-50 to-white hover:border-purple-400"
                      : schema.color === "green"
                        ? "border-green-200 bg-gradient-to-br from-green-50 to-white hover:border-green-400"
                        : "border-orange-200 bg-gradient-to-br from-orange-50 to-white hover:border-orange-400"
                }`}
              >
                <div className="flex items-start gap-3 mb-3">
                  <span className="text-3xl">{schema.icon}</span>
                  <div className="flex-1">
                    <h3 className="font-bold text-lg text-gray-900">
                      {schema.name}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {schema.description}
                    </p>
                    <p className="text-xs text-gray-500 mt-2 font-mono bg-white px-2 py-1 rounded border inline-block">
                      {schema.file}
                    </p>
                  </div>
                </div>

                {showSchemas && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <p className="text-xs font-semibold text-gray-700 mb-2">
                      COLUMNS ({schema.columns.length}):
                    </p>
                    <div className="space-y-2">
                      {schema.columns.map((col, colIndex) => (
                        <div
                          key={colIndex}
                          className="flex items-start gap-2 text-xs bg-white p-2 rounded border"
                        >
                          <code className="font-mono font-semibold text-indigo-600 min-w-[120px]">
                            {col.name}
                          </code>
                          <span className="text-gray-500 px-2 py-0.5 bg-gray-100 rounded">
                            {col.type}
                          </span>
                          <span className="text-gray-600 flex-1">
                            {col.desc}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          {showSchemas && (
            <div className="mt-6 p-4 bg-indigo-50 rounded-lg border border-indigo-200">
              <h4 className="font-semibold text-indigo-900 mb-2 flex items-center">
                <CheckCircle className="h-5 w-5 mr-2" />
                How the Pipeline Works
              </h4>
              <ol className="text-sm text-indigo-800 space-y-2 ml-6 list-decimal">
                <li>
                  <strong>GTFS Ingestion</strong> parses metro schedules and detects interchange stations
                </li>
                <li>
                  <strong>Station Metadata</strong> calculates importance scores based on connectivity
                </li>
                <li>
                  <strong>Synthetic Delays</strong> generates 50k realistic records with peak/weather patterns
                </li>
                <li>
                  <strong>Peak Labels</strong> classifies hourly traffic patterns (morning/evening rush)
                </li>
                <li>
                  <strong>Transfer Penalties</strong> measures walking times between platforms
                </li>
                <li>
                  <strong>OD Benchmarks</strong> compares ideal vs actual travel times for all routes
                </li>
              </ol>
            </div>
          )}
        </Card>
      </main>

      {/* Footer */}
      <footer className="mt-12 bg-white border-t">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <p className="text-center text-gray-600 text-sm">
            Metro Route Intelligence Dashboard | Project by Ms. Sadiya Maheen
            Siddiqui | Submission Deadline: 15th April 2026
          </p>
        </div>
      </footer>
    </div>
  );
}
