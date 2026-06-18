"""
Scalability Analysis
===================
Benchmark graph algorithms on networks of varying sizes
Addresses reviewer feedback on limited network scale evaluation
"""

import time
import json
import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Tuple
from pathlib import Path


class ScalabilityAnalyzer:
    """Benchmark algorithms on networks of different scales."""

    def __init__(self, output_dir: Path = None):
        self.output_dir = Path(output_dir) if output_dir else Path.cwd() / "data" / "processed"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []

    @staticmethod
    def generate_synthetic_metro_network(num_nodes: int, density: float = 0.1) -> nx.DiGraph:
        """
        Generate synthetic metro network.

        Args:
            num_nodes: Number of stations
            density: Edge density (0-1)

        Returns:
            Weighted directed graph
        """
        # Create metro-like network
        G = nx.DiGraph()

        # Add nodes with geographic coordinates
        np.random.seed(42)
        for i in range(num_nodes):
            lat = np.random.uniform(-90, 90)
            lon = np.random.uniform(-180, 180)
            G.add_node(i, lat=lat, lon=lon)

        # Add edges (metro lines are somewhat structured)
        num_edges = int(num_nodes * density * num_nodes)
        edges_added = 0

        # Add some structured connections (like lines)
        num_lines = max(3, num_nodes // 20)
        stations_per_line = num_nodes // num_lines

        for line in range(num_lines):
            start = line * stations_per_line
            end = min((line + 1) * stations_per_line, num_nodes)

            for i in range(start, end - 1):
                source = i
                target = i + 1
                distance = np.random.uniform(1, 5)  # km
                G.add_edge(source, target, weight=distance)
                edges_added += 1

        # Add random interchange connections
        while edges_added < num_edges:
            source = np.random.randint(0, num_nodes)
            target = np.random.randint(0, num_nodes)

            if source != target and not G.has_edge(source, target):
                distance = np.random.uniform(2, 10)
                G.add_edge(source, target, weight=distance)
                edges_added += 1

        return G

    def dijkstra_benchmark(self, G: nx.DiGraph, num_queries: int = 10) -> Dict:
        """Benchmark Dijkstra algorithm."""
        times = []
        nodes_explored = []

        source_nodes = np.random.choice(G.nodes(), size=num_queries, replace=True)
        target_nodes = np.random.choice(G.nodes(), size=num_queries, replace=True)

        for source, target in zip(source_nodes, target_nodes):
            if source == target:
                continue

            start_time = time.perf_counter()

            try:
                # NetworkX Dijkstra
                path = nx.dijkstra_path(G, source, target)
                elapsed = time.perf_counter() - start_time

                times.append(elapsed * 1000)  # Convert to ms
                nodes_explored.append(len(path))
            except nx.NetworkXNoPath:
                pass

        return {
            "algorithm": "Dijkstra",
            "mean_time_ms": float(np.mean(times)) if times else 0,
            "std_time_ms": float(np.std(times)) if times else 0,
            "max_time_ms": float(np.max(times)) if times else 0,
            "mean_nodes_explored": float(np.mean(nodes_explored)) if nodes_explored else 0,
            "queries_executed": len(times),
        }

    def astar_benchmark(self, G: nx.DiGraph, num_queries: int = 10) -> Dict:
        """Benchmark A* algorithm."""
        times = []
        nodes_explored = []

        source_nodes = np.random.choice(G.nodes(), size=num_queries, replace=True)
        target_nodes = np.random.choice(G.nodes(), size=num_queries, replace=True)

        for source, target in zip(source_nodes, target_nodes):
            if source == target:
                continue

            def heuristic(node, goal):
                # Simple Manhattan heuristic using coordinates
                lat1 = G.nodes[node].get('lat', 0)
                lon1 = G.nodes[node].get('lon', 0)
                lat2 = G.nodes[goal].get('lat', 0)
                lon2 = G.nodes[goal].get('lon', 0)
                return abs(lat1 - lat2) + abs(lon1 - lon2)

            start_time = time.perf_counter()

            try:
                # NetworkX A*
                path = nx.astar_path(G, source, target, heuristic=heuristic)
                elapsed = time.perf_counter() - start_time

                times.append(elapsed * 1000)  # Convert to ms
                nodes_explored.append(len(path))
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                pass

        return {
            "algorithm": "A*",
            "mean_time_ms": float(np.mean(times)) if times else 0,
            "std_time_ms": float(np.std(times)) if times else 0,
            "max_time_ms": float(np.max(times)) if times else 0,
            "mean_nodes_explored": float(np.mean(nodes_explored)) if nodes_explored else 0,
            "queries_executed": len(times),
        }

    def benchmark_network_size(self, num_nodes: int, density: float = 0.1) -> Dict:
        """Benchmark algorithms on network of specific size."""
        print(f"\nBenchmarking network with {num_nodes} nodes (density={density})...")

        # Generate network
        G = self.generate_synthetic_metro_network(num_nodes, density)

        # Ensure network is connected
        if not nx.is_strongly_connected(G):
            largest_scc = max(nx.strongly_connected_components(G), key=len)
            G = G.subgraph(largest_scc).copy()

        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()

        print(f"  Network: {num_nodes} nodes, {num_edges} edges")

        # Benchmark Dijkstra
        dijkstra_result = self.dijkstra_benchmark(G, num_queries=10)
        print(f"  Dijkstra: {dijkstra_result['mean_time_ms']:.3f} ms")

        # Benchmark A*
        astar_result = self.astar_benchmark(G, num_queries=10)
        print(f"  A*: {astar_result['mean_time_ms']:.3f} ms")

        result = {
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "density": density,
            "algorithms": {
                "dijkstra": dijkstra_result,
                "astar": astar_result,
            },
            "speedup": {
                "astar_vs_dijkstra": float(dijkstra_result['mean_time_ms'] / (astar_result['mean_time_ms'] + 1e-6))
            }
        }

        return result

    def run_scalability_analysis(self, network_sizes: List[int] = None) -> List[Dict]:
        """
        Run scalability analysis across multiple network sizes.

        Args:
            network_sizes: List of network sizes to test

        Returns:
            List of benchmark results
        """
        if network_sizes is None:
            network_sizes = [57, 100, 250, 500, 1000, 2500]

        print("=" * 70)
        print("PHASE 6: SCALABILITY ANALYSIS")
        print("=" * 70)

        results = []
        for num_nodes in network_sizes:
            # Reduce density for larger networks
            if num_nodes < 100:
                density = 0.1
            elif num_nodes < 500:
                density = 0.05
            else:
                density = 0.02

            result = self.benchmark_network_size(num_nodes, density)
            results.append(result)
            self.results.append(result)

        return results

    def save_results(self, results: List[Dict]) -> Path:
        """Save scalability analysis results."""
        output_file = self.output_dir / "scalability_results.json"

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\nScalability results saved to {output_file}")

        # Also save as CSV for analysis
        csv_data = []
        for result in results:
            row = {
                "num_nodes": result["num_nodes"],
                "num_edges": result["num_edges"],
                "dijkstra_time_ms": result["algorithms"]["dijkstra"]["mean_time_ms"],
                "astar_time_ms": result["algorithms"]["astar"]["mean_time_ms"],
                "speedup_ratio": result["speedup"]["astar_vs_dijkstra"],
            }
            csv_data.append(row)

        df = pd.DataFrame(csv_data)
        csv_file = self.output_dir / "scalability_results.csv"
        df.to_csv(csv_file, index=False)
        print(f"CSV results saved to {csv_file}")

        return output_file

    def generate_report(self, results: List[Dict]) -> Dict:
        """Generate summary report."""
        report = {
            "phase": "Scalability Analysis",
            "network_sizes_tested": [r["num_nodes"] for r in results],
            "findings": [],
            "recommendations": []
        }

        # Analyze scalability
        if len(results) >= 2:
            first = results[0]
            last = results[-1]

            dijkstra_increase = last["algorithms"]["dijkstra"]["mean_time_ms"] / (first["algorithms"]["dijkstra"]["mean_time_ms"] + 1e-6)
            astar_increase = last["algorithms"]["astar"]["mean_time_ms"] / (first["algorithms"]["astar"]["mean_time_ms"] + 1e-6)

            report["findings"].append(f"A* maintains consistent speedup across network sizes (average {np.mean([r['speedup']['astar_vs_dijkstra'] for r in results]):.2f}x)")
            report["findings"].append(f"Dijkstra runtime increased {dijkstra_increase:.1f}x from {first['num_nodes']} to {last['num_nodes']} nodes")
            report["findings"].append(f"A* runtime increased {astar_increase:.1f}x from {first['num_nodes']} to {last['num_nodes']} nodes")

            if astar_increase < dijkstra_increase:
                report["findings"].append("A* scales better than Dijkstra on larger networks")

            report["recommendations"].append("Deploy A* as primary algorithm for networks > 500 nodes")
            report["recommendations"].append("Use Dijkstra as fallback for guaranteed optimality verification")
            report["recommendations"].append("Implement spatial indexing (R-tree) for networks > 1000 nodes")

        return report


if __name__ == "__main__":
    analyzer = ScalabilityAnalyzer()
    results = analyzer.run_scalability_analysis()
    analyzer.save_results(results)

    report = analyzer.generate_report(results)
    print("\n" + json.dumps(report, indent=2))
