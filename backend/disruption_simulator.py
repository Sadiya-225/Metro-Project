"""
Disruption Simulator & Robustness Analysis
==========================================
Simulate various transit disruptions and evaluate algorithm resilience
Addresses reviewer feedback on robustness evaluation
"""

import json
import numpy as np
import networkx as nx
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
import time


class DisruptionSimulator:
    """Simulate transit disruptions and measure impact."""

    def __init__(self, G: nx.DiGraph, output_dir: Path = None):
        self.G_original = G.copy()
        self.G = G.copy()
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "data" / "processed"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []

    def dijkstra_path(self, source: int, target: int) -> Tuple[List, float]:
        """Find shortest path using Dijkstra."""
        try:
            path = nx.dijkstra_path(self.G, source, target, weight='scheduled_minutes')
            cost = nx.dijkstra_path_length(self.G, source, target, weight='scheduled_minutes')
            return path, cost
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None, float('inf')

    def astar_path(self, source: int, target: int) -> Tuple[List, float]:
        """Find shortest path using A*."""
        def heuristic(node, goal):
            lat1 = self.G.nodes[node].get('lat', 0)
            lon1 = self.G.nodes[node].get('lon', 0)
            lat2 = self.G.nodes[goal].get('lat', 0)
            lon2 = self.G.nodes[goal].get('lon', 0)
            return abs(lat1 - lat2) + abs(lon1 - lon2)

        try:
            path = nx.astar_path(self.G, source, target, heuristic=heuristic, weight='scheduled_minutes')
            cost = nx.astar_path_length(self.G, source, target, heuristic=heuristic, weight='scheduled_minutes')
            return path, cost
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None, float('inf')

    def get_k_shortest_paths(self, source: int, target: int, k: int = 3) -> List[Tuple]:
        """Find K shortest paths (simple implementation)."""
        paths = []
        try:
            for _ in range(k):
                path, cost = self.dijkstra_path(source, target)
                if path is None:
                    break
                paths.append((path, cost))

                # Remove edges from this path (except last edge)
                G_temp = self.G.copy()
                for i in range(len(path) - 1):
                    if G_temp.has_edge(path[i], path[i + 1]):
                        G_temp.remove_edge(path[i], path[i + 1])
                self.G = G_temp
        except Exception:
            pass

        self.G = self.G_original.copy()
        return paths

    def simulate_station_closure(self, station_id: int) -> Dict:
        """Simulate single station closure."""
        result = {
            "disruption_type": "Station Closure",
            "affected_station": int(station_id),
        }

        # Remove station
        self.G.remove_node(station_id)

        # Test random routes
        num_tests = 10
        detour_ratios = []
        path_failures = 0

        nodes = list(self.G_original.nodes())
        for _ in range(num_tests):
            source = int(np.random.choice(nodes))
            target = int(np.random.choice(nodes))

            if source == target or source == station_id or target == station_id:
                continue

            # Original path
            original_path, original_cost = self.dijkstra_path(source, target)
            self.G = self.G_original.copy()

            # Path with closure
            self.G.remove_node(station_id)
            disrupted_path, disrupted_cost = self.dijkstra_path(source, target)

            if original_path and disrupted_path:
                detour_ratio = disrupted_cost / original_cost if original_cost > 0 else 1.0
                detour_ratios.append(detour_ratio)
            elif disrupted_path is None:
                path_failures += 1

        result["mean_detour_ratio"] = float(np.mean(detour_ratios)) if detour_ratios else 1.0
        result["path_failures"] = path_failures
        result["alternative_routes_found"] = len(detour_ratios)

        self.G = self.G_original.copy()
        return result

    def simulate_line_closure(self, line_edges: List[Tuple]) -> Dict:
        """Simulate entire line closure."""
        result = {
            "disruption_type": "Line Closure",
            "affected_edges": len(line_edges),
        }

        # Remove all edges in line
        self.G.remove_edges_from(line_edges)

        # Test random routes
        num_tests = 10
        detour_ratios = []
        path_failures = 0

        nodes = list(self.G_original.nodes())
        for _ in range(num_tests):
            source = np.random.choice(nodes)
            target = np.random.choice(nodes)

            if source == target:
                continue

            # Original path
            original_path, original_cost = self.dijkstra_path(source, target)
            self.G = self.G_original.copy()

            # Path with line closure
            self.G.remove_edges_from(line_edges)
            disrupted_path, disrupted_cost = self.dijkstra_path(source, target)

            if original_path and disrupted_path:
                detour_ratio = disrupted_cost / original_cost if original_cost > 0 else 1.0
                detour_ratios.append(detour_ratio)
            elif disrupted_path is None:
                path_failures += 1

        result["mean_detour_ratio"] = float(np.mean(detour_ratios)) if detour_ratios else 1.0
        result["path_failures"] = path_failures
        result["alternative_routes_found"] = len(detour_ratios)

        self.G = self.G_original.copy()
        return result

    def simulate_congestion_surge(self, affected_nodes: List[int], congestion_factor: float = 2.0) -> Dict:
        """Simulate congestion surge at certain stations."""
        result = {
            "disruption_type": "Congestion Surge",
            "affected_stations": len(affected_nodes),
            "congestion_factor": congestion_factor,
        }

        # Increase edge weights for edges connected to affected nodes
        self.G = self.G_original.copy()
        for node in affected_nodes:
            for (u, v) in self.G.in_edges(node):
                if 'scheduled_minutes' in self.G[u][v]:
                    self.G[u][v]['scheduled_minutes'] *= congestion_factor

            for (u, v) in self.G.out_edges(node):
                if 'scheduled_minutes' in self.G[u][v]:
                    self.G[u][v]['scheduled_minutes'] *= congestion_factor

        # Test routes
        num_tests = 10
        cost_increases = []

        nodes = list(self.G_original.nodes())
        for _ in range(num_tests):
            source = np.random.choice(nodes)
            target = np.random.choice(nodes)

            if source == target:
                continue

            # Original cost
            original_path, original_cost = self.dijkstra_path(source, target)
            self.G = self.G_original.copy()

            # With congestion
            for node in affected_nodes:
                for (u, v) in self.G.in_edges(node):
                    if 'scheduled_minutes' in self.G[u][v]:
                        self.G[u][v]['scheduled_minutes'] *= congestion_factor

                for (u, v) in self.G.out_edges(node):
                    if 'scheduled_minutes' in self.G[u][v]:
                        self.G[u][v]['scheduled_minutes'] *= congestion_factor

            disrupted_path, disrupted_cost = self.dijkstra_path(source, target)

            if original_path and disrupted_path:
                cost_increase = (disrupted_cost - original_cost) / original_cost * 100
                cost_increases.append(cost_increase)

        result["mean_eta_increase_percent"] = float(np.mean(cost_increases)) if cost_increases else 0.0
        result["max_eta_increase_percent"] = float(np.max(cost_increases)) if cost_increases else 0.0

        self.G = self.G_original.copy()
        return result

    def simulate_weather_event(self, affected_edges_fraction: float = 0.3, delay_factor: float = 1.5) -> Dict:
        """Simulate weather event affecting random edges."""
        result = {
            "disruption_type": "Weather Event",
            "affected_edges_fraction": affected_edges_fraction,
            "delay_factor": delay_factor,
        }

        self.G = self.G_original.copy()

        # Randomly select edges to affect
        all_edges = list(self.G.edges())
        num_affected = int(len(all_edges) * affected_edges_fraction)
        affected_edges = np.random.choice(len(all_edges), size=num_affected, replace=False)

        # Increase delays on affected edges
        for idx in affected_edges:
            u, v = all_edges[idx]
            if 'scheduled_minutes' in self.G[u][v]:
                self.G[u][v]['scheduled_minutes'] *= delay_factor

        # Test routes
        num_tests = 10
        delay_increases = []

        nodes = list(self.G_original.nodes())
        for _ in range(num_tests):
            source = np.random.choice(nodes)
            target = np.random.choice(nodes)

            if source == target:
                continue

            # Original delay
            original_path, original_cost = self.dijkstra_path(source, target)
            self.G = self.G_original.copy()

            # With weather
            for idx in affected_edges:
                u, v = all_edges[idx]
                if 'scheduled_minutes' in self.G[u][v]:
                    self.G[u][v]['scheduled_minutes'] *= delay_factor

            weather_path, weather_cost = self.dijkstra_path(source, target)

            if original_path and weather_path:
                delay_increase = (weather_cost - original_cost) / original_cost * 100 if original_cost > 0 else 0
                delay_increases.append(delay_increase)

        result["mean_delay_increase_percent"] = float(np.mean(delay_increases)) if delay_increases else 0.0
        result["max_delay_increase_percent"] = float(np.max(delay_increases)) if delay_increases else 0.0

        self.G = self.G_original.copy()
        return result

    def run_all_disruption_scenarios(self) -> List[Dict]:
        """Run all disruption scenarios."""
        print("=" * 70)
        print("PHASE 7: ROBUSTNESS ANALYSIS")
        print("=" * 70)

        results = []

        # Scenario 1: Station closures
        print("\n1. Testing station closures...")
        nodes = list(self.G_original.nodes())
        for station_id in np.random.choice(nodes, size=min(5, len(nodes)), replace=False):
            result = self.simulate_station_closure(station_id)
            results.append(result)
            print(f"   Station {station_id}: {result['mean_detour_ratio']:.2f}x detour")

        # Scenario 2: Line closures
        print("\n2. Testing line closures...")
        all_edges = list(self.G_original.edges())
        line_edges = np.random.choice(len(all_edges), size=min(10, len(all_edges) // 5), replace=False)
        line_edges = [all_edges[i] for i in line_edges]
        result = self.simulate_line_closure(line_edges)
        results.append(result)
        print(f"   Line closure: {result['mean_detour_ratio']:.2f}x detour")

        # Scenario 3: Congestion surge
        print("\n3. Testing congestion surge...")
        for factor in [1.5, 2.0, 3.0]:
            affected = np.random.choice(nodes, size=min(5, len(nodes)), replace=False)
            result = self.simulate_congestion_surge(list(affected), congestion_factor=factor)
            results.append(result)
            print(f"   Congestion {factor}x: {result['mean_eta_increase_percent']:.1f}% ETA increase")

        # Scenario 4: Weather event
        print("\n4. Testing weather events...")
        for frac in [0.2, 0.5]:
            result = self.simulate_weather_event(affected_edges_fraction=frac)
            results.append(result)
            print(f"   Weather {frac*100:.0f}% edges: {result['mean_delay_increase_percent']:.1f}% delay increase")

        return results

    def save_results(self, results: List[Dict]) -> Path:
        """Save robustness analysis results."""
        output_file = self.output_dir / "robustness_results.json"

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\nRobustness results saved to {output_file}")
        return output_file
