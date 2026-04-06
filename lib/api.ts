/**
 * API client for the Metro Route Intelligence backend.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface RouteRequest {
  source: string;
  destination: string;
  algorithm?: string;
  k_paths?: number;
}

export interface Station {
  station_id: string;
  station_name: string;
  line: string;
  latitude: number;
  longitude: number;
  is_interchange: boolean;
  is_terminal: boolean;
  platform_count: number;
  zone: string;
  importance_score: number;
  commercial_area: boolean;
  college_zone: boolean;
  near_it_hub: boolean;
  smart_city_priority?: boolean;
}

export interface TransferSegment {
  from_station: string;
  to_station: string;
  line: string;
  is_walking_transfer: boolean;
}

export interface StationCongestion {
  station_name: string;
  congestion_score: number;
}

export interface AlternativeRoute {
  path: string[];
  distance: number;
  time: number;
  transfer_count: number;
}

export interface RouteResponse {
  source: string;
  destination: string;
  shortest_path: string[];
  actual_path: string[];
  distance: number;
  actual_distance: number;
  estimated_time: number;
  actual_time: number;
  delay: number;
  eta_deviation: number;
  route_divergence_score: number;
  bottleneck_stations: string[];
  transfer_segments: TransferSegment[];
  transfer_count: number;
  station_congestion: StationCongestion[];
  alternative_routes: AlternativeRoute[];
}

export interface DelayPredictionResponse {
  station_id: string;
  predicted_delay: number;
  confidence: number;
  risk_level: string;
}

export interface DashboardAnalyticsResponse {
  line_delay_comparison: Array<{ line: string; avg_delay: number }>;
  zone_congestion: Array<{ zone: string; avg_congestion: number }>;
  hourly_delay_profile: Array<{
    hour: number;
    avg_delay: number;
    avg_congestion: number;
  }>;
  interchange_risk: Array<{
    station_name: string;
    avg_delay: number;
    congestion_score: number;
    importance_score: number;
    is_interchange: boolean;
    zone: string;
    line: string;
    risk_score: number;
  }>;
}

export interface ImportanceScore {
  station_id: string;
  station_name: string;
  importance_score: number;
  smart_city_priority: boolean;
  route_count: number;
  degree_centrality: number;
  betweenness_centrality: number;
  closeness_centrality: number;
  activity_score: number;
}

export async function getStations(): Promise<Station[]> {
  const response = await fetch(`${API_BASE_URL}/api/stations`);
  if (!response.ok) throw new Error("Failed to fetch stations");
  const data = await response.json();
  return data.stations;
}

export async function getStationImportance(): Promise<ImportanceScore[]> {
  const response = await fetch(`${API_BASE_URL}/api/stations/importance`);
  if (!response.ok) throw new Error("Failed to fetch station importance");
  const data = await response.json();
  return data.stations;
}

export async function optimizeRoute(
  request: RouteRequest,
): Promise<RouteResponse> {
  const response = await fetch(`${API_BASE_URL}/api/route/optimize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error("Failed to optimize route");
  return response.json();
}

export async function getBottlenecks(limit = 10) {
  const response = await fetch(
    `${API_BASE_URL}/api/bottlenecks?limit=${limit}`,
  );
  if (!response.ok) throw new Error("Failed to fetch bottlenecks");
  return response.json();
}

export async function getDashboardAnalytics(): Promise<DashboardAnalyticsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/analytics/dashboard`);
  if (!response.ok) throw new Error("Failed to fetch dashboard analytics");
  return response.json();
}

export async function getDelayStats() {
  const response = await fetch(`${API_BASE_URL}/api/delays/stats`);
  if (!response.ok) throw new Error("Failed to fetch delay stats");
  return response.json();
}

export async function getODPairs(limit = 20) {
  const response = await fetch(`${API_BASE_URL}/api/od-pairs?limit=${limit}`);
  if (!response.ok) throw new Error("Failed to fetch OD pairs");
  return response.json();
}

export async function predictDelay(data: {
  station_id: string;
  hour: number;
  is_peak: boolean;
  weekday: boolean;
  weather?: string;
}): Promise<DelayPredictionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/predict/delay`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to predict delay");
  return response.json();
}

export async function getMLMetrics() {
  const response = await fetch(`${API_BASE_URL}/api/ml/metrics`);
  if (!response.ok) throw new Error("Failed to fetch ML metrics");
  return response.json();
}
