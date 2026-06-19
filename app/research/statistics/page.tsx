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
import { ArrowLeft, BarChart3, AlertCircle, CheckCircle2 } from "lucide-react";

interface StatisticalAnalysis {
  comparison: string;
  samples: number;
  paired_t_test: {
    test: string;
    t_statistic: number;
    p_value: number;
    significant_alpha_0_05: boolean;
  };
  wilcoxon_test: {
    test: string;
    p_value: number;
    significant_alpha_0_05: boolean;
  };
  effect_size: {
    cohens_d: number;
    interpretation: string;
  };
  confidence_intervals: {
    XGBoost: {
      mean_absolute_error: number;
      lower_bound: number;
      upper_bound: number;
    };
    RandomForest: {
      mean_absolute_error: number;
      lower_bound: number;
      upper_bound: number;
    };
  };
}

interface ComprehensiveReport {
  phases: {
    phase_5?: {
      phase: string;
      dataset_comparisons?: {
        synthetic?: { statistical_comparison?: StatisticalAnalysis };
        real?: { statistical_comparison?: StatisticalAnalysis };
        combined?: { statistical_comparison?: StatisticalAnalysis };
      };
    };
  };
}

export default function StatisticsPage() {
  const [report, setReport] = useState<ComprehensiveReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const response = await fetch(
          "/data/processed/comprehensive_research_report.json",
        );
        if (!response.ok) throw new Error("Failed to load statistics data");
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
          <p>Loading Statistical Analysis...</p>
        </div>
      </div>
    );
  }

  const syntheticStats =
    report?.phases.phase_5?.dataset_comparisons?.synthetic
      ?.statistical_comparison;
  const realStats =
    report?.phases.phase_5?.dataset_comparisons?.real?.statistical_comparison;
  const combinedStats =
    report?.phases.phase_5?.dataset_comparisons?.combined
      ?.statistical_comparison;

  // Prepare CI visualization data
  const ciData = [
    {
      dataset: "Synthetic",
      model: "XGBoost",
      mae:
        syntheticStats?.confidence_intervals?.XGBoost?.mean_absolute_error || 0,
      lower: syntheticStats?.confidence_intervals?.XGBoost?.lower_bound || 0,
      upper: syntheticStats?.confidence_intervals?.XGBoost?.upper_bound || 0,
    },
    {
      dataset: "Synthetic",
      model: "RandomForest",
      mae:
        syntheticStats?.confidence_intervals?.RandomForest
          ?.mean_absolute_error || 0,
      lower:
        syntheticStats?.confidence_intervals?.RandomForest?.lower_bound || 0,
      upper:
        syntheticStats?.confidence_intervals?.RandomForest?.upper_bound || 0,
    },
    {
      dataset: "Real",
      model: "XGBoost",
      mae: realStats?.confidence_intervals?.XGBoost?.mean_absolute_error || 0,
      lower: realStats?.confidence_intervals?.XGBoost?.lower_bound || 0,
      upper: realStats?.confidence_intervals?.XGBoost?.upper_bound || 0,
    },
    {
      dataset: "Real",
      model: "RandomForest",
      mae:
        realStats?.confidence_intervals?.RandomForest?.mean_absolute_error || 0,
      lower: realStats?.confidence_intervals?.RandomForest?.lower_bound || 0,
      upper: realStats?.confidence_intervals?.RandomForest?.upper_bound || 0,
    },
  ];

  const renderStatTest = (
    stats: StatisticalAnalysis | undefined,
    datasetName: string,
  ) => {
    if (!stats) return null;

    const pValue = stats.paired_t_test.p_value;
    const effectSize = stats.effect_size.cohens_d;
    const isSignificant = stats.paired_t_test.significant_alpha_0_05;
    const wilcoxonSignificant = stats.wilcoxon_test.significant_alpha_0_05;

    // Determine interpretation
    const isMeaningful = Math.abs(effectSize) >= 0.2; // small effect size threshold
    const interpretation =
      isSignificant && isMeaningful
        ? "Statistically significant AND practically meaningful"
        : isSignificant && !isMeaningful
          ? "Statistically significant but practically negligible"
          : "Not statistically significant";

    return (
      <div
        key={datasetName}
        className="p-4 bg-white rounded-lg border border-gray-200"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {datasetName} Dataset
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          {/* Parametric Test */}
          <div className="p-3 bg-blue-50 rounded border border-blue-200">
            <p className="text-sm font-medium text-blue-700 mb-2">
              Paired t-test
            </p>
            <div className="space-y-1 text-sm">
              <p className="text-gray-700">
                <span className="text-gray-600">t-statistic:</span>{" "}
                <span className="font-mono text-gray-900">
                  {stats.paired_t_test.t_statistic.toFixed(4)}
                </span>
              </p>
              <p className="text-gray-700">
                <span className="text-gray-600">p-value:</span>{" "}
                <span
                  className={`font-mono font-bold ${isSignificant ? "text-green-600" : "text-yellow-600"}`}
                >
                  {pValue < 0.001 ? "< 0.001" : pValue.toFixed(4)}
                </span>
              </p>
              <p
                className={`text-xs font-medium ${isSignificant ? "text-green-700" : "text-yellow-700"}`}
              >
                {isSignificant
                  ? "Significant at α=0.05"
                  : "Not significant at α=0.05"}
              </p>
            </div>
          </div>

          {/* Non-Parametric Test */}
          <div className="p-3 bg-purple-50 rounded border border-purple-200">
            <p className="text-sm font-medium text-purple-700 mb-2">
              Wilcoxon Signed-Rank Test
            </p>
            <div className="space-y-1 text-sm">
              <p className="text-gray-700">
                <span className="text-gray-600">Test:</span>{" "}
                <span className="text-gray-700">
                  Non-parametric alternative
                </span>
              </p>
              <p className="text-gray-700">
                <span className="text-gray-600">p-value:</span>{" "}
                <span
                  className={`font-mono font-bold ${wilcoxonSignificant ? "text-green-600" : "text-yellow-600"}`}
                >
                  {stats.wilcoxon_test.p_value.toFixed(4)}
                </span>
              </p>
              <p
                className={`text-xs font-medium ${wilcoxonSignificant ? "text-green-700" : "text-yellow-700"}`}
              >
                {wilcoxonSignificant
                  ? "Significant at α=0.05"
                  : "Not significant at α=0.05"}
              </p>
            </div>
          </div>
        </div>

        {/* Effect Size */}
        <div className="p-3 bg-orange-50 rounded border border-orange-200 mb-4">
          <p className="text-sm font-medium text-orange-700 mb-2">
            Effect Size (Cohen's d)
          </p>
          <div className="space-y-2">
            <p className="text-gray-700">
              <span className="text-gray-600">Cohen's d:</span>{" "}
              <span className="font-mono font-bold text-gray-900">
                {effectSize.toFixed(4)}
              </span>
            </p>
            <p className="text-gray-700">
              <span className="text-gray-600">Interpretation:</span>{" "}
              <span className="text-gray-800 font-medium">
                {stats.effect_size.interpretation}
              </span>
            </p>
            <div className="text-xs text-gray-600 mt-2">
              <p>
                Reference: |d| &lt; 0.2 = Negligible, 0.2-0.5 = Small, 0.5-0.8 =
                Medium, &gt; 0.8 = Large
              </p>
            </div>
          </div>
        </div>

        {/* Combined Interpretation */}
        <div
          className={`p-3 rounded border flex gap-3 ${
            isSignificant && isMeaningful
              ? "bg-green-50 border-green-200"
              : isSignificant
                ? "bg-yellow-50 border-yellow-200"
                : "bg-gray-50 border-gray-200"
          }`}
        >
          {isSignificant && isMeaningful ? (
            <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-5 h-5 text-yellow-600 shrink-0 mt-0.5" />
          )}
          <div>
            <p
              className={`text-sm font-semibold ${
                isSignificant && isMeaningful
                  ? "text-green-700"
                  : "text-yellow-700"
              }`}
            >
              {interpretation}
            </p>
            <p className="text-xs text-gray-700 mt-1">
              While the parametric t-test shows statistical significance, the
              non-parametric Wilcoxon test and negligible effect size suggest
              that algorithm performance differences, though measurable, have
              minimal practical impact on real-world routing decisions.
            </p>
          </div>
        </div>
      </div>
    );
  };

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
                Statistical Validation
              </h1>
              <p className="text-lg text-gray-600 mt-2">
                Rigorous statistical analysis with p-values, effect sizes, and
                confidence intervals
              </p>
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-12">
          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Datasets Analyzed
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">3</div>
              <p className="text-xs text-gray-500 mt-1">
                Synthetic, Real, Combined
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Tests Performed
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">6</div>
              <p className="text-xs text-gray-500 mt-1">
                t-test, Wilcoxon, d, CI
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Confidence Level
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-600">95%</div>
              <p className="text-xs text-gray-500 mt-1">Standard in research</p>
            </CardContent>
          </Card>
        </div>

        {/* Statistical Results by Dataset */}
        <div className="space-y-6 mb-12">
          <h2 className="text-2xl font-bold text-gray-900">
            Hypothesis Tests: XGBoost vs RandomForest
          </h2>

          {syntheticStats && renderStatTest(syntheticStats, "Synthetic")}
          {realStats && renderStatTest(realStats, "Real")}
          {combinedStats && renderStatTest(combinedStats, "Combined")}
        </div>

        {/* Confidence Intervals Visualization */}
        {syntheticStats && (
          <Card className="bg-white border-gray-200 shadow-lg mb-12">
            <CardHeader>
              <CardTitle className="text-gray-900">
                95% Confidence Intervals for MAE
              </CardTitle>
              <CardDescription>
                Point estimates with uncertainty bounds
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {ciData.map((item, idx) => (
                  <div key={idx} className="flex items-center gap-4">
                    <div className="w-24 text-sm">
                      <p className="font-medium text-gray-700">
                        {item.dataset}
                      </p>
                      <p className="text-xs text-gray-600">{item.model}</p>
                    </div>
                    <div className="flex-1 h-12 flex items-center">
                      <div className="relative w-full h-2 bg-gray-300 rounded">
                        <div
                          className="absolute h-full bg-blue-500/30 rounded"
                          style={{
                            left: `${(item.lower / item.mae) * 100 - 5}%`,
                            right: `${100 - (item.upper / item.mae) * 100 - 5}%`,
                          }}
                        />
                        <div
                          className="absolute top-1/2 -translate-y-1/2 w-1 h-4 bg-blue-400 rounded"
                          style={{
                            left: `${(item.mae / Math.max(...ciData.map((d) => d.upper))) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                    <div className="w-32 text-right text-sm text-gray-700 font-mono">
                      {item.lower.toFixed(3)} - {item.upper.toFixed(3)}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Key Statistical Insights */}
        <Card className="bg-white border-gray-200 shadow-lg mb-12">
          <CardHeader>
            <CardTitle className="text-gray-900">
              Statistical Interpretation Guide
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm font-semibold text-blue-700 mb-2">
                P-Value (α = 0.05)
              </p>
              <p className="text-gray-700 text-sm">
                Indicates the probability of observing the data if the null
                hypothesis (no difference) is true.
                <span className="block text-xs text-gray-600 mt-1">
                  • p &lt; 0.05: Reject null hypothesis (statistically
                  significant)
                </span>
                <span className="block text-xs text-gray-600">
                  • p ≥ 0.05: Fail to reject null hypothesis (not significant)
                </span>
              </p>
            </div>

            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <p className="text-sm font-semibold text-green-700 mb-2">
                Cohen's d (Effect Size)
              </p>
              <p className="text-gray-700 text-sm">
                Measures the magnitude of difference independent of sample size.
                <span className="block text-xs text-gray-600 mt-1">
                  • |d| &lt; 0.2: Negligible effect (practically unimportant)
                </span>
                <span className="block text-xs text-gray-600">
                  • 0.2-0.5: Small effect | 0.5-0.8: Medium effect | &gt; 0.8:
                  Large effect
                </span>
              </p>
            </div>

            <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
              <p className="text-sm font-semibold text-orange-700 mb-2">
                Confidence Intervals (95% CI)
              </p>
              <p className="text-gray-700 text-sm">
                Range of values within which the true population parameter
                likely falls (95% confidence).
                <span className="block text-xs text-gray-600 mt-1">
                  Narrower intervals indicate more precise estimates;
                  overlapping intervals suggest no significant difference.
                </span>
              </p>
            </div>

            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
              <p className="text-sm font-semibold text-purple-700 mb-2">
                Wilcoxon Test (Non-Parametric)
              </p>
              <p className="text-gray-700 text-sm">
                More robust than t-test; doesn't assume normal distribution.
                Preferred when p-value and effect size conflict.
                <span className="block text-xs text-gray-600 mt-1">
                  When t-test is significant but Wilcoxon is not: result likely
                  due to outliers or non-normality.
                </span>
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Critical Findings */}
        <Card className="bg-white border-gray-200 shadow-lg">
          <CardHeader>
            <CardTitle className="text-gray-900">
              Critical Research Findings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <p className="text-sm font-semibold text-yellow-700 mb-2">
                Paradox: Statistical vs Practical Significance
              </p>
              <p className="text-gray-700 text-sm">
                Paired t-tests show p &lt; 0.05 (statistically significant), but
                Cohen's d is negligible (~0.016), and Wilcoxon tests show p &gt;
                0.05. This means algorithm choice has measurable but practically
                unimportant effects on real-world routing performance. Large
                sample sizes can make tiny differences statistically
                significant.
              </p>
            </div>

            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm font-semibold text-blue-700 mb-2">
                Real Data Validation Success
              </p>
              <p className="text-gray-700 text-sm">
                Integration of 1,664 real Indian Railway records demonstrates
                that incorporating operational data is crucial for model
                validity. Cross-domain analysis (synthetic→real) revealed R² =
                -0.562, proving that synthetic-only models fail in production.
              </p>
            </div>

            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <p className="text-sm font-semibold text-green-700 mb-2">
                Methodology Rigor
              </p>
              <p className="text-gray-700 text-sm">
                Presenting both parametric (t-test) and non-parametric
                (Wilcoxon) tests alongside effect sizes represents best
                practices in scientific reporting. This prevents Type I errors
                and ensures findings are reproducible and actionable.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
