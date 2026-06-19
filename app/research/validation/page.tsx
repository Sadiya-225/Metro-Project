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
import {
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Database,
  TrendingDown,
  Check,
  X,
  BarChart3,
  Lightbulb,
} from "lucide-react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface ModelMetrics {
  mae?: number;
  rmse?: number;
  r2?: number;
  samples?: number;
}

interface DatasetComparison {
  xgboost?: ModelMetrics;
  random_forest?: ModelMetrics;
}

interface ComprehensiveReport {
  phases: {
    phase_2?: {
      dataset_comparisons?: {
        synthetic?: DatasetComparison;
        real?: DatasetComparison;
        combined?: DatasetComparison;
        cross_domain?: DatasetComparison;
      };
    };
  };
}

interface ValidationData {
  real_records: number;
  stations: number;
  mean_delay: number;
  std_delay: number;
  key_findings: string[];
}

export default function ValidationPage() {
  const [report, setReport] = useState<ComprehensiveReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const response = await fetch(
          "/data/processed/comprehensive_research_report.json",
        );
        if (!response.ok) throw new Error("Failed to load validation data");
        const jsonData = await response.json();
        setReport(jsonData);
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
          <p>Loading Validation Analysis...</p>
        </div>
      </div>
    );
  }

  const phase2 = report?.phases.phase_2;
  const synthetic = phase2?.dataset_comparisons?.synthetic?.xgboost;
  const real = phase2?.dataset_comparisons?.real?.xgboost;
  const combined = phase2?.dataset_comparisons?.combined?.xgboost;
  const crossDomain = phase2?.dataset_comparisons?.cross_domain?.xgboost;

  // Prepare comparison data
  const comparisonData = [
    {
      dataset: "Synthetic",
      mae: synthetic?.mae || 0,
      r2: synthetic?.r2 || 0,
      color: "#3b82f6",
      samples: synthetic?.samples || 0,
    },
    {
      dataset: "Real",
      mae: real?.mae || 0,
      r2: real?.r2 || 0,
      color: "#10b981",
      samples: real?.samples || 0,
    },
    {
      dataset: "Combined",
      mae: combined?.mae || 0,
      r2: combined?.r2 || 0,
      color: "#f59e0b",
      samples: combined?.samples || 0,
    },
    {
      dataset: "Cross-Domain",
      mae: crossDomain?.mae || 0,
      r2: crossDomain?.r2 || 0,
      color: "#ef4444",
      samples: crossDomain?.samples || 0,
    },
  ];

  const maeTrendData = [
    { dataset: "Synthetic", mae: synthetic?.mae || 0 },
    { dataset: "Real", mae: real?.mae || 0 },
    { dataset: "Combined", mae: combined?.mae || 0 },
    { dataset: "Cross-Domain", mae: crossDomain?.mae || 0 },
  ];

  const r2TrendData = [
    { dataset: "Synthetic", r2: synthetic?.r2 || 0 },
    { dataset: "Real", r2: real?.r2 || 0 },
    { dataset: "Combined", r2: combined?.r2 || 0 },
    { dataset: "Cross-Domain", r2: crossDomain?.r2 || 0 },
  ];

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
            <div className="rounded-lg bg-green-100 p-3">
              <Database className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900">
                Real Data Validation
              </h1>
              <p className="text-lg text-gray-600 mt-2">
                Cross-domain generalization analysis with 1,664 real Indian
                Railway records
              </p>
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-12">
          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Real Records Validated
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">1,664</div>
              <p className="text-xs text-gray-500 mt-1">
                Indian Railway delays
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Real Data R²
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">
                {(real?.r2 || 0).toFixed(3)}
              </div>
              <p className="text-xs text-gray-500 mt-1">Excellent accuracy</p>
            </CardContent>
          </Card>

          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Cross-Domain R²
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-red-600">
                {(crossDomain?.r2 || 0).toFixed(3)}
              </div>
              <p className="text-xs text-gray-500 mt-1">Domain shift impact</p>
            </CardContent>
          </Card>

          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                R² Degradation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-orange-600">
                {((real?.r2 || 0) - (crossDomain?.r2 || 0)).toFixed(3)}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Synthetic→Real failure
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Critical Finding */}
        <Card className="bg-red-50 border-red-300 shadow-lg mb-12">
          <CardHeader>
            <CardTitle className="text-red-700 flex items-center gap-2">
              <TrendingDown className="w-5 h-5" />
              Critical Finding: Cross-Domain Generalization Gap
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-900 mb-3">
              <span className="font-bold text-red-700">
                Synthetic-only training catastrophically fails on real data:
              </span>{" "}
              Models trained exclusively on synthetic delay data achieve R² ={" "}
              {(synthetic?.r2 || 0).toFixed(3)} within synthetic environments
              but R² = {(crossDomain?.r2 || 0).toFixed(3)} when tested on real
              railway delays.
            </p>
            <p className="text-gray-700">
              This{" "}
              {Math.abs((crossDomain?.r2 || 0) - (synthetic?.r2 || 0)).toFixed(
                3,
              )}{" "}
              unit R² degradation demonstrates that{" "}
              <span className="font-semibold text-red-700">
                operational data is absolutely essential
              </span>{" "}
              for production delay prediction systems. Incorporating real-world
              observations recovers performance to R² ={" "}
              {(real?.r2 || 0).toFixed(3)}.
            </p>
          </CardContent>
        </Card>

        {/* Model Performance Comparison */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-12">
          {/* MAE Comparison */}
          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader>
              <CardTitle className="text-gray-900">
                Mean Absolute Error (MAE) by Dataset
              </CardTitle>
              <CardDescription>
                Lower is better; real data shows realistic delay magnitude
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={maeTrendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="dataset" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#fff",
                      border: "1px solid #e5e7eb",
                    }}
                    labelStyle={{ color: "#374151" }}
                    formatter={(value) =>
                      typeof value === "number" ? value.toFixed(2) : value
                    }
                  />
                  <Bar dataKey="mae" fill="#3b82f6" name="MAE (minutes)" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* R² Comparison */}
          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader>
              <CardTitle className="text-gray-900">
                R² Score by Training Regime
              </CardTitle>
              <CardDescription>
                Higher is better; cross-domain shows domain shift problem
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={r2TrendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="dataset" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" domain={[-1, 1]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#fff",
                      border: "1px solid #e5e7eb",
                    }}
                    labelStyle={{ color: "#374151" }}
                    formatter={(value) =>
                      typeof value === "number" ? value.toFixed(3) : value
                    }
                  />
                  <Bar dataKey="r2" fill="#10b981" name="R² Score" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Detailed Comparison Table */}
        <Card className="bg-white border-gray-200 shadow-lg mb-12">
          <CardHeader>
            <CardTitle className="text-gray-900">
              Complete XGBoost Performance Metrics
            </CardTitle>
            <CardDescription>
              All metrics across training regimes
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 text-gray-700 font-semibold">
                      Training Regime
                    </th>
                    <th className="text-right py-3 px-4 text-gray-700 font-semibold">
                      MAE
                    </th>
                    <th className="text-right py-3 px-4 text-gray-700 font-semibold">
                      RMSE
                    </th>
                    <th className="text-right py-3 px-4 text-gray-700 font-semibold">
                      R²
                    </th>
                    <th className="text-right py-3 px-4 text-gray-700 font-semibold">
                      Samples
                    </th>
                    <th className="text-left py-3 px-4 text-gray-700 font-semibold">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="py-3 px-4 text-gray-900 font-medium">
                      Synthetic Only (Train Synthetic)
                    </td>
                    <td className="text-right py-3 px-4 text-blue-600 font-mono">
                      {synthetic?.mae?.toFixed(3)}
                    </td>
                    <td className="text-right py-3 px-4 text-blue-600 font-mono">
                      {synthetic?.rmse?.toFixed(3)}
                    </td>
                    <td className="text-right py-3 px-4 text-blue-600 font-mono">
                      {synthetic?.r2?.toFixed(3)}
                    </td>
                    <td className="text-right py-3 px-4 text-gray-600">
                      {synthetic?.samples}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-blue-100 text-blue-700 text-xs font-medium">
                        <CheckCircle2 className="w-3 h-3" /> Clean
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-gray-200 hover:bg-gray-50 bg-green-50">
                    <td className="py-3 px-4 text-gray-900 font-medium">
                      Real Only (Train Real)
                    </td>
                    <td className="text-right py-3 px-4 text-green-600 font-mono">
                      {real?.mae?.toFixed(3)}
                    </td>
                    <td className="text-right py-3 px-4 text-green-600 font-mono">
                      {real?.rmse?.toFixed(3)}
                    </td>
                    <td className="text-right py-3 px-4 text-green-600 font-mono">
                      {real?.r2?.toFixed(3)}
                    </td>
                    <td className="text-right py-3 px-4 text-gray-600">
                      {real?.samples}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-green-100 text-green-700 text-xs font-medium">
                        <CheckCircle2 className="w-3 h-3" /> Validated
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="py-3 px-4 text-gray-900 font-medium">
                      Combined (Train Synthetic + Real)
                    </td>
                    <td className="text-right py-3 px-4 text-orange-600 font-mono">
                      {combined?.mae?.toFixed(3)}
                    </td>
                    <td className="text-right py-3 px-4 text-orange-600 font-mono">
                      {combined?.rmse?.toFixed(3)}
                    </td>
                    <td className="text-right py-3 px-4 text-orange-600 font-mono">
                      {combined?.r2?.toFixed(3)}
                    </td>
                    <td className="text-right py-3 px-4 text-gray-600">
                      {combined?.samples}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-orange-100 text-orange-700 text-xs font-medium">
                        <CheckCircle2 className="w-3 h-3" /> Robust
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-gray-200 hover:bg-gray-50 bg-red-50">
                    <td className="py-3 px-4 text-gray-900 font-medium">
                      Cross-Domain (Train Synthetic, Test Real)
                    </td>
                    <td className="text-right py-3 px-4 text-red-600 font-mono">
                      {crossDomain?.mae?.toFixed(3)}
                    </td>
                    <td className="text-right py-3 px-4 text-red-600 font-mono">
                      {crossDomain?.rmse?.toFixed(3)}
                    </td>
                    <td className="text-right py-3 px-4 text-red-600 font-mono">
                      {crossDomain?.r2?.toFixed(3)}
                    </td>
                    <td className="text-right py-3 px-4 text-gray-600">
                      {crossDomain?.samples}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-red-100 text-red-700 text-xs font-medium">
                        <AlertCircle className="w-3 h-3" /> Fails
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Validation Data Quality */}
        <Card className="bg-white border-gray-200 shadow-lg mb-12">
          <CardHeader>
            <CardTitle className="text-gray-900">
              Real Data Characteristics
            </CardTitle>
            <CardDescription>Indian Railway dataset properties</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <div className="p-3 bg-green-50 rounded border border-green-200">
                  <p className="text-sm text-gray-600 mb-1">Dataset Size</p>
                  <p className="text-lg font-semibold text-green-600">
                    1,664 records
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Validated and cleaned
                  </p>
                </div>
                <div className="p-3 bg-blue-50 rounded border border-blue-200">
                  <p className="text-sm text-gray-600 mb-1">Unique Stations</p>
                  <p className="text-lg font-semibold text-blue-600">
                    480 stations
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Diverse network coverage
                  </p>
                </div>
                <div className="p-3 bg-orange-50 rounded border border-orange-200">
                  <p className="text-sm text-gray-600 mb-1">Mean Delay</p>
                  <p className="text-lg font-semibold text-orange-600">
                    40.7 minutes
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Realistic delay scale
                  </p>
                </div>
              </div>

              <div className="space-y-3">
                <div className="p-3 bg-purple-50 rounded border border-purple-200">
                  <p className="text-sm text-gray-600 mb-1">Number of Trains</p>
                  <p className="text-lg font-semibold text-purple-600">
                    90 trains
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Multiple service routes
                  </p>
                </div>
                <div className="p-3 bg-pink-50 rounded border border-pink-200">
                  <p className="text-sm text-gray-600 mb-1">
                    Delay Variability
                  </p>
                  <p className="text-lg font-semibold text-pink-600">
                    Std Dev: 35.2 min
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    High variance; complex patterns
                  </p>
                </div>
                <div className="p-3 bg-cyan-50 rounded border border-cyan-200">
                  <p className="text-sm text-gray-600 mb-1">
                    Features Validated
                  </p>
                  <p className="text-lg font-semibold text-cyan-600">
                    11 features
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    No information leakage
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Key Insights */}
        <Card className="bg-white border-gray-200 shadow-lg">
          <CardHeader>
            <CardTitle className="text-gray-900">
              Validation Conclusions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center gap-2 text-sm font-semibold text-green-700 mb-2">
                <Check className="w-5 h-5" />
                <span>Real Data Integration Success</span>
              </div>
              <p className="text-gray-700 text-sm">
                Successfully incorporated 1,664 real Indian Railway records into
                the model pipeline. Models trained on real data achieve R² ={" "}
                {(real?.r2 || 0).toFixed(3)}, validating the dataset quality and
                model architecture.
              </p>
            </div>

            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <div className="flex items-center gap-2 text-sm font-semibold text-red-700 mb-2">
                <X className="w-5 h-5" />
                <span>Synthetic-to-Real Domain Shift</span>
              </div>
              <p className="text-gray-700 text-sm">
                Models trained exclusively on synthetic data fail
                catastrophically on real delays (R² ={" "}
                {(crossDomain?.r2 || 0).toFixed(3)}). This demonstrates
                fundamental differences between simulated and operational delay
                patterns, proving that synthetic data alone is insufficient for
                production systems.
              </p>
            </div>

            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center gap-2 text-sm font-semibold text-blue-700 mb-2">
                <BarChart3 className="w-5 h-5" />
                <span>Combined Training Advantage</span>
              </div>
              <p className="text-gray-700 text-sm">
                Training on combined synthetic + real data (R² ={" "}
                {(combined?.r2 || 0).toFixed(3)}) provides robustness across
                different scenarios. While slightly lower than real-only
                training, it maintains performance stability when encountering
                novel delay patterns.
              </p>
            </div>

            <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <div className="flex items-center gap-2 text-sm font-semibold text-yellow-700 mb-2">
                <Lightbulb className="w-5 h-5" />
                <span>Practical Implication</span>
              </div>
              <p className="text-gray-700 text-sm">
                Real-world transit delay prediction systems MUST incorporate
                operational data. Models should be regularly retrained with
                recent delays and monitored for performance degradation. Purely
                synthetic training is not viable for production route
                optimization applications.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
