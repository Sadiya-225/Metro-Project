/**
 * Research Dashboard - Overview Page
 * Comprehensive analysis of all research phases (1-7)
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowRight, BarChart3, TrendingUp, Shield, Database, Brain, Zap, LineChart, Activity, CheckCircle } from 'lucide-react';

const researchPhases = [
  {
    phase: 1,
    title: 'Real Data Validation',
    icon: Database,
    description: 'Loaded 1,664 real Indian Railway delay records for cross-domain evaluation',
    key_metric: '40.7 min avg delay',
    link: '/research/validation'
  },
  {
    phase: 2,
    title: 'Multi-Dataset Framework',
    icon: Brain,
    description: 'Modular ML architecture supporting synthetic, real, and combined datasets',
    key_metric: 'R² = 0.817 (real)',
    link: '/research/model-comparison'
  },
  {
    phase: 3,
    title: 'LSTM Temporal Model',
    icon: TrendingUp,
    description: 'Deep learning temporal model with 24-hour sequence windows',
    key_metric: '2-layer LSTM',
    link: '/research/model-comparison'
  },
  {
    phase: 4,
    title: 'Transformer Model',
    icon: Brain,
    description: 'Attention-based architecture with multi-head attention',
    key_metric: '4-head attention',
    link: '/research/model-comparison'
  },
  {
    phase: 5,
    title: 'Statistical Analysis',
    icon: BarChart3,
    description: 'T-tests, Wilcoxon signed-rank, Cohen\'s d, confidence intervals',
    key_metric: 'p < 0.001',
    link: '/research/statistics'
  },
  {
    phase: 6,
    title: 'Scalability Benchmarks',
    icon: Zap,
    description: 'Algorithm performance on networks up to 500 nodes',
    key_metric: '1.87x A* speedup',
    link: '/research/scalability'
  },
  {
    phase: 7,
    title: 'Robustness Analysis',
    icon: Shield,
    description: 'Station closures, line failures, congestion, and weather scenarios',
    key_metric: '1.0x detour ratio',
    link: '/research'
  },
];

export default function ResearchPage() {
  return (
    <div className="min-h-screen bg-linear-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Research Enhancement Report
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl">
            Comprehensive analysis addressing all reviewer feedback with real-world validation,
            statistical rigor, and production-ready implementation.
          </p>
        </div>

        {/* Key Metrics Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-12">
          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Real Data Records
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">1,664</div>
              <p className="text-xs text-gray-500 mt-1">Indian Railway data</p>
            </CardContent>
          </Card>

          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                ML Models
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">4</div>
              <p className="text-xs text-gray-500 mt-1">XGB, RF, LSTM, Transformer</p>
            </CardContent>
          </Card>

          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Network Sizes Tested
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-600">500</div>
              <p className="text-xs text-gray-500 mt-1">nodes maximum</p>
            </CardContent>
          </Card>

          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                A* Speedup
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-orange-600">1.38x</div>
              <p className="text-xs text-gray-500 mt-1">vs Dijkstra (avg)</p>
            </CardContent>
          </Card>
        </div>

        {/* Research Phases Grid */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Research Phases</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-7 gap-4">
            {researchPhases.map((phase) => {
              const Icon = phase.icon;
              return (
                <Link key={phase.phase} href={phase.link}>
                  <Card className="bg-white border-gray-200 hover:border-blue-500 hover:shadow-xl transition-all cursor-pointer h-full shadow-lg">
                    <CardHeader>
                      <div className="flex items-start justify-between mb-2">
                        <div className="rounded-lg bg-blue-50 p-2">
                          <Icon className="w-4 h-4 text-blue-600" />
                        </div>
                        <span className="text-xs font-bold text-blue-700 bg-blue-100 px-2 py-1 rounded">
                          Phase {phase.phase}
                        </span>
                      </div>
                      <CardTitle className="text-sm text-gray-900">
                        {phase.title}
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-xs text-gray-600 mb-3 line-clamp-2">
                        {phase.description}
                      </p>
                      <div className="text-xs font-semibold text-green-700">
                        {phase.key_metric}
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Key Findings */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader>
              <CardTitle className="text-gray-900">Model Performance</CardTitle>
              <CardDescription>Comparative analysis across datasets</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="p-3 bg-blue-50 rounded border border-blue-100">
                <p className="text-sm font-semibold text-gray-900 mb-1">Synthetic Data</p>
                <p className="text-sm text-gray-700">XGBoost: MAE=0.311 min, R²=0.380</p>
              </div>
              <div className="p-3 bg-green-50 rounded border border-green-100">
                <p className="text-sm font-semibold text-gray-900 mb-1">Real Data</p>
                <p className="text-sm text-gray-700">XGBoost: MAE=11.947 min, R²=0.817</p>
              </div>
              <div className="p-3 bg-orange-50 rounded border border-orange-100">
                <p className="text-sm font-semibold text-gray-900 mb-1">Combined Data</p>
                <p className="text-sm text-gray-700">XGBoost: MAE=0.955 min, R²=0.523</p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white border-gray-200 shadow-lg">
            <CardHeader>
              <CardTitle className="text-gray-900">Statistical Findings</CardTitle>
              <CardDescription>Significance tests and effect sizes</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="p-3 bg-blue-50 rounded border border-blue-100">
                <p className="text-sm font-semibold text-gray-900 mb-1">Paired t-test</p>
                <p className="text-sm text-gray-700">p &lt; 0.001 (Significant)</p>
              </div>
              <div className="p-3 bg-purple-50 rounded border border-purple-100">
                <p className="text-sm font-semibold text-gray-900 mb-1">Wilcoxon Test</p>
                <p className="text-sm text-gray-700">p = 0.596 (Not significant)</p>
              </div>
              <div className="p-3 bg-orange-50 rounded border border-orange-100">
                <p className="text-sm font-semibold text-gray-900 mb-1">Cohen's d</p>
                <p className="text-sm text-gray-700">-0.016 (Negligible effect)</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Reviewer Feedback */}
        <Card className="bg-white border-gray-200 shadow-lg mb-12">
          <CardHeader>
            <CardTitle className="text-gray-900">Reviewer Feedback Addressed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                { issue: 'Synthetic data only', solution: 'Real Indian Railway dataset (1,664 records)', phase: 1 },
                { issue: 'No deep learning models', solution: 'LSTM and Transformer implemented', phase: '3-4' },
                { issue: 'Limited scalability', solution: 'Networks up to 500 nodes tested', phase: 6 },
                { issue: 'No statistical tests', solution: 't-test, Wilcoxon, Cohen\'s d', phase: 5 },
                { issue: 'Single metro only', solution: 'Real-world + synthetic networks', phase: '1,6' },
                { issue: 'No robustness eval', solution: '11 disruption scenarios', phase: 7 },
              ].map((item, idx) => (
                <div key={idx} className="p-4 border border-gray-200 rounded-lg bg-gray-50">
                  <p className="text-sm font-semibold text-red-600 mb-2">{item.issue}</p>
                  <p className="text-sm text-gray-700 mb-2">{item.solution}</p>
                  <span className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded font-medium">
                    Phase {item.phase}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quick Navigation */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { title: 'Model Comparison', href: '/research/model-comparison', Icon: BarChart3 },
            { title: 'Scalability', href: '/research/scalability', Icon: TrendingUp },
            { title: 'Statistics', href: '/research/statistics', Icon: Activity },
            { title: 'Validation', href: '/research/validation', Icon: CheckCircle },
          ].map((item) => (
            <Link key={item.href} href={item.href}>
              <Card className="bg-white border-gray-200 hover:border-blue-500 transition-colors cursor-pointer h-full shadow-lg">
                <CardContent className="pt-6 text-center">
                  <item.Icon className="w-10 h-10 mb-3 mx-auto text-blue-600" />
                  <h3 className="font-semibold text-gray-900 mb-2">{item.title}</h3>
                  <div className="flex items-center justify-center text-blue-600 text-sm font-medium">
                    Explore <ArrowRight className="w-4 h-4 ml-2" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
