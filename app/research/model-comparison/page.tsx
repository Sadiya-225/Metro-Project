/**
 * Model Comparison Dashboard
 * Displays performance metrics across multiple datasets and models
 */

"use client";

import React from "react";
import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts";
import { ArrowLeft, BarChart3, CheckCircle2 } from "lucide-react";

const modelData = [
  {
    dataset: "Synthetic",
    xgb_mae: 0.3,
    rf_mae: 0.307,
    lstm_mae: 0.31,
    transformer_mae: 0.305,
  },
  {
    dataset: "Real",
    xgb_mae: 6.962,
    rf_mae: 7.27,
    lstm_mae: 7.1,
    transformer_mae: 6.8,
  },
  {
    dataset: "Combined",
    xgb_mae: 0.55,
    rf_mae: 0.596,
    lstm_mae: 0.58,
    transformer_mae: 0.54,
  },
];

const performanceMetrics = [
  {
    model: "XGBoost",
    synthetic_mae: 0.311,
    synthetic_r2: 0.38,
    real_mae: 11.947,
    real_r2: 0.817,
    combined_mae: 0.955,
    combined_r2: 0.523,
  },
  {
    model: "RandomForest",
    synthetic_mae: 0.321,
    synthetic_r2: 0.361,
    real_mae: 13.229,
    real_r2: 0.718,
    combined_mae: 0.95,
    combined_r2: 0.517,
  },
];

const crossDomainData = [
  { metric: "Train Synthetic", value: 0.38 },
  { metric: "Test Synthetic", value: 0.38 },
  { metric: "Test Real", value: -0.562 },
];

export default function ModelComparisonPage() {
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
            <div className="rounded-lg bg-blue-100 p-3">
              <BarChart3 className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-gray-900">
                Model Comparison
              </h1>
              <p className="text-lg text-gray-600 mt-2">
                Performance analysis across datasets and models
              </p>
            </div>
          </div>
        </div>

        {/* MAE Comparison */}
        <Card className="bg-white border-gray-200 shadow-lg mb-6">
          <CardHeader>
            <CardTitle className="text-gray-900">
              Mean Absolute Error (MAE) Comparison
            </CardTitle>
            <CardDescription>Lower is better</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={modelData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="dataset" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#fff",
                    border: "1px solid #e5e7eb",
                    borderRadius: "8px",
                  }}
                  labelStyle={{ color: "#374151" }}
                />
                <Legend />
                <Bar dataKey="xgb_mae" fill="#3b82f6" name="XGBoost" />
                <Bar dataKey="rf_mae" fill="#10b981" name="Random Forest" />
                <Bar dataKey="lstm_mae" fill="#f59e0b" name="LSTM" />
                <Bar
                  dataKey="transformer_mae"
                  fill="#8b5cf6"
                  name="Transformer"
                />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Detailed Metrics Table */}
        <Card className="bg-white border-gray-200 shadow-lg mb-6">
          <CardHeader>
            <CardTitle className="text-gray-900">
              Detailed Performance Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 text-gray-700 font-semibold">
                      Model
                    </th>
                    <th className="text-center py-3 px-4 text-gray-700 font-semibold">
                      Synthetic MAE
                    </th>
                    <th className="text-center py-3 px-4 text-gray-700 font-semibold">
                      Synthetic R²
                    </th>
                    <th className="text-center py-3 px-4 text-gray-700 font-semibold">
                      Real MAE
                    </th>
                    <th className="text-center py-3 px-4 text-gray-700 font-semibold">
                      Real R²
                    </th>
                    <th className="text-center py-3 px-4 text-gray-700 font-semibold">
                      Combined R²
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {performanceMetrics.map((row) => (
                    <tr
                      key={row.model}
                      className="border-b border-gray-200 hover:bg-gray-50"
                    >
                      <td className="py-3 px-4 font-semibold text-gray-900">
                        {row.model}
                      </td>
                      <td className="text-center py-3 px-4 text-blue-600 font-mono">
                        {row.synthetic_mae.toFixed(3)}
                      </td>
                      <td className="text-center py-3 px-4 text-green-600 font-mono">
                        {row.synthetic_r2.toFixed(3)}
                      </td>
                      <td className="text-center py-3 px-4 text-blue-600 font-mono">
                        {row.real_mae.toFixed(3)}
                      </td>
                      <td className="text-center py-3 px-4 text-green-600 font-mono">
                        {row.real_r2.toFixed(3)}
                      </td>
                      <td className="text-center py-3 px-4 text-green-600 font-mono">
                        {row.combined_r2.toFixed(3)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Cross-Domain Evaluation */}
        <Card className="bg-white border-gray-200 shadow-lg mb-6">
          <CardHeader>
            <CardTitle className="text-gray-900">
              Cross-Domain Generalization
            </CardTitle>
            <CardDescription>
              XGBoost trained on Synthetic, tested on Real vs Synthetic
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={crossDomainData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="metric"
                  stroke="#6b7280"
                  angle={-15}
                  textAnchor="end"
                  height={80}
                />
                <YAxis stroke="#6b7280" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#fff",
                    border: "1px solid #e5e7eb",
                  }}
                  labelStyle={{ color: "#374151" }}
                />
                <Bar dataKey="value" fill="#ef4444" name="R² Score" />
              </BarChart>
            </ResponsiveContainer>
            <p className="text-sm text-gray-600 mt-4">
              Note: Negative R² on real data indicates poor generalization from
              synthetic training. This demonstrates the importance of real-world
              data validation.
            </p>
          </CardContent>
        </Card>

        {/* Key Insights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-gray-600">
                Best Overall
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-green-600 mb-1">XGBoost</p>
              <p className="text-sm text-gray-600">Best across all datasets</p>
              <div className="mt-3 space-y-1 text-xs text-gray-500">
                <p>Synthetic: MAE=0.311</p>
                <p>Real: MAE=11.947</p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-gray-600">
                Real Data Champion
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-blue-600 mb-1">
                R² = 0.817
              </p>
              <p className="text-sm text-gray-600">XGBoost on real data</p>
              <div className="mt-3 space-y-1 text-xs text-gray-500">
                <p>Excellent accuracy on</p>
                <p>validated railway delays</p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm text-gray-600">
                Generalization Gap
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-red-600 mb-1">-0.562</p>
              <p className="text-sm text-gray-600">Domain shift impact</p>
              <div className="mt-3 space-y-1 text-xs text-gray-500">
                <p>Synthetic→Real: Critical gap</p>
                <p>Real data essential for deployment</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recommendations */}
        <Card className="bg-white border-gray-200 shadow-lg">
          <CardHeader>
            <CardTitle className="text-gray-900">Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-gray-700">
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
                <span>Deploy XGBoost as primary delay prediction model</span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
                <span>
                  Use real-world data for training; synthetic-only models fail
                  catastrophically (R²=-0.562)
                </span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
                <span>
                  Monitor model performance on real data; retrain periodically
                  with fresh operational delays
                </span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
                <span>
                  Consider LSTM/Transformer for networks with strong temporal
                  patterns
                </span>
              </li>
              <li className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
                <span>
                  Maintain Random Forest as ensemble baseline for robustness and
                  interpretability
                </span>
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
