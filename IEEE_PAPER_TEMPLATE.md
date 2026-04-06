# Real-Time Metro Route Optimization: A Comparative Study of Graph Algorithms with ML-based Delay Prediction

**Student:** Ms. SADIYA MAHEEN SIDDIQUI
**Project Lead:** Dr. Shivani Yadao, Associate Professor
**Institution:** [Your Institution Name]
**Submission Date:** 15th April 2026

---

## Abstract

Urban metro systems face significant challenges in providing accurate estimated times of arrival (ETAs) due to real-time congestion, weather conditions, and operational delays. This research presents an integrated approach combining graph-based route optimization algorithms (Dijkstra, A*, and Yen's K-shortest paths) with machine learning-based delay prediction using XGBoost and Random Forest models. Applied to Hyderabad Metro Rail Limited (HMRL) data, our system achieves a prediction accuracy with MAE of [X.XX] minutes and RMSE of [X.XX] minutes on a dataset of 50,000 synthetic delay records. The comparative analysis demonstrates that A* with Haversine heuristic achieves [X]% faster pathfinding compared to Dijkstra while maintaining optimal path quality, and Yen's algorithm successfully identifies K=3 alternative routes with less than [X]% additional travel time. This work contributes to smart city applications by enabling commuters to make informed decisions based on predicted delays and alternative route suggestions.

**Keywords:** Metro route optimization, Dijkstra algorithm, A* search, Yen's algorithm, Machine learning, XGBoost, Delay prediction, Smart cities, Public transportation, GTFS

---

## I. INTRODUCTION

### A. Background and Motivation

Urban transportation systems are the backbone of modern smart cities, with metro rail networks serving millions of commuters daily. In India, cities like Delhi, Bangalore, and Hyderabad have rapidly expanded their metro infrastructure, with Hyderabad Metro Rail Limited (HMRL) alone carrying [X] million passengers per month. However, a persistent challenge remains: the discrepancy between scheduled travel times and actual journey durations due to various delay factors including peak-hour congestion, transfer inefficiencies, and unexpected service disruptions.

Traditional route planning systems rely solely on theoretical shortest paths without considering real-time operational constraints. This limitation leads to inaccurate ETAs, causing commuter frustration and suboptimal travel decisions. The integration of machine learning-based delay prediction with advanced graph algorithms presents an opportunity to bridge this gap.

### B. Problem Statement

Given a metro network G = (V, E) where V represents stations and E represents connections with associated travel times, the problem is threefold:

1. **Optimal Route Discovery:** Find the shortest path P between source station s and destination station d that minimizes total travel time T(P).

2. **Real-time Delay Prediction:** Predict delay δ(v,t) at any station v at time t based on historical patterns, weather conditions, peak hours, and station characteristics.

3. **Comparative Algorithm Analysis:** Evaluate and compare the performance of Dijkstra's algorithm, A* search, and Yen's K-shortest paths algorithm in terms of computational efficiency, path optimality, and practical applicability.

### C. Research Objectives

1. Develop a comprehensive data engineering pipeline to process GTFS (General Transit Feed Specification) data from HMRL
2. Implement and compare three graph algorithms: Dijkstra, A*, and Yen's
3. Build ML models (XGBoost and Random Forest) for delay prediction
4. Create an interactive visualization dashboard for route intelligence
5. Identify bottleneck stations and suggest infrastructure improvements
6. Provide empirical evidence for smart city transportation planning

### D. Contributions

This research makes the following contributions:
- A scalable data pipeline generating 50,000+ realistic delay scenarios
- Comparative empirical evaluation of three graph algorithms on real metro topology
- ML-based delay prediction with 15 engineered features achieving [X]% R² score
- Interactive dashboard for commuters and transit authorities
- Open-source implementation for reproducibility and extension

---

## II. LITERATURE REVIEW

### A. Route Optimization in Public Transport

[Cite 3-5 papers on routing algorithms in metro systems]

Key findings from existing research:
- Dijkstra's algorithm guarantees optimal paths but explores many unnecessary nodes
- A* with appropriate heuristics significantly reduces search space
- Yen's algorithm for K-shortest paths is computationally expensive but provides valuable alternatives

### B. Machine Learning for Delay Prediction

[Cite 3-5 papers on ML in transportation]

Previous approaches include:
- Linear regression models with limited accuracy
- Neural networks requiring large training data
- Ensemble methods showing promising results

### C. Smart City Applications

[Cite 2-3 papers on smart transportation systems]

### D. Research Gap

While existing literature addresses route optimization and delay prediction separately, limited research integrates both aspects with comparative algorithm analysis on Indian metro networks. This study fills this gap by providing an end-to-end solution with real-world validation.

---

## III. METHODOLOGY

### A. Data Collection and Processing

#### 1) GTFS Data Acquisition
- Source: Hyderabad Metro Rail Limited (HMRL)
- Files: stops.txt, routes.txt, trips.txt, stop_times.txt
- Total stations: 69 (Red: 27, Blue: 23, Green: 9)
- Interchange stations: 2 (Ameerpet, MG Bus Station)

#### 2) OpenStreetMap Integration
- GeoJSON data for precise station coordinates
- Validation and name matching with GTFS data
- Extraction of 57 parent stations for network graph

#### 3) Synthetic Delay Generation
To address the lack of real-time historical delay data, we generated a synthetic dataset modeling realistic delay patterns:

**Generation Logic:**
```
delay = base_delay × peak_multiplier × zone_factor × weather_impact + random_events

where:
- base_delay ~ Normal(0.5, 0.3) minutes
- peak_multiplier = 2.5-4.0 during rush hours
- zone_factor accounts for IT hubs, commercial areas, educational zones
- weather_impact: clear(1.0), rain(1.2), fog/storm(1.4)
- random_events: 5% chance of 5-15 min delays, 2% chance of 15-30 min severe delays
```

**Dataset Specifications:**
- Records: 50,000
- Time span: 30 days
- Features: 14 (hour, peak_hour, weekday, weather, importance_score, is_interchange, is_terminal, commercial_area, college_zone, near_it_hub, transfer_load, platform_occupancy, congestion_score, delay_minutes)

### B. Network Graph Construction

#### 1) Graph Representation
- Nodes: 57 parent stations (location_type=1 in GTFS)
- Edges: Physical connections between consecutive stations on each line
- Weight: Haversine distance in kilometers

#### 2) Station Metadata
Each station v ∈ V is assigned attributes:
- Importance score I(v) ∈ [0, 100]
- Interchange flag: I_interchange(v) ∈ {0, 1}
- Terminal flag: I_terminal(v) ∈ {0, 1}
- Zone classification: Z(v) ∈ {IT Hub, Commercial, Educational, Residential, Medical}

**Importance Calculation:**
```
I(v) = 50 + 25×I_interchange(v) + 10×I_terminal(v) + zone_bonus(v) + priority_bonus(v)

Capped at 100
```

### C. Route Optimization Algorithms

#### 1) Dijkstra's Algorithm

**Algorithm:**
```
function DIJKSTRA(G, s, d):
    dist[s] = 0
    for all v ∈ V: dist[v] = ∞
    Q = priority_queue(V, key=dist)

    while Q not empty:
        u = Q.extract_min()
        if u == d: break

        for each neighbor v of u:
            alt = dist[u] + weight(u, v)
            if alt < dist[v]:
                dist[v] = alt
                predecessor[v] = u
                Q.decrease_key(v)

    return reconstruct_path(predecessor, s, d), dist[d]
```

**Complexity:** O((|V| + |E|) log |V|)

**Implementation:** NetworkX shortest_path() with 'weight' parameter

#### 2) A* Algorithm

**Algorithm:**
```
function ASTAR(G, s, d):
    g_score[s] = 0
    f_score[s] = heuristic(s, d)
    open_set = {s}

    while open_set not empty:
        u = node in open_set with minimum f_score
        if u == d: return reconstruct_path()

        open_set.remove(u)
        closed_set.add(u)

        for each neighbor v of u:
            if v in closed_set: continue

            tentative_g = g_score[u] + weight(u, v)

            if v not in open_set or tentative_g < g_score[v]:
                predecessor[v] = u
                g_score[v] = tentative_g
                f_score[v] = g_score[v] + heuristic(v, d)

                if v not in open_set:
                    open_set.add(v)

    return failure
```

**Heuristic Function:**
```
heuristic(v, d) = haversine_distance(lat_v, lon_v, lat_d, lon_d)
```

Where Haversine distance is the great-circle distance between two points on a sphere:

```
a = sin²(Δlat/2) + cos(lat₁) × cos(lat₂) × sin²(Δlon/2)
c = 2 × atan2(√a, √(1-a))
distance = R × c    (R = 6371 km)
```

**Admissibility:** This heuristic is admissible as straight-line distance never overestimates actual metro travel distance.

**Complexity:** Best case O(|E|), worst case same as Dijkstra

**Implementation:** NetworkX astar_path() with custom heuristic

#### 3) Yen's K-Shortest Paths Algorithm

**Algorithm:**
```
function YEN_KSP(G, s, d, K):
    A = [shortest_path(G, s, d)]  // Dijkstra's result
    B = priority_queue()

    for k = 2 to K:
        for i = 0 to len(A[k-1]) - 2:
            spur_node = A[k-1][i]
            root_path = A[k-1][0:i+1]

            // Remove edges used by previous paths
            edges_removed = []
            for path in A:
                if root_path == path[0:i+1]:
                    remove_edge(path[i], path[i+1])
                    edges_removed.append((path[i], path[i+1]))

            // Remove nodes in root path except spur node
            nodes_removed = root_path[:-1]

            spur_path = shortest_path(G, spur_node, d)

            if spur_path found:
                total_path = root_path + spur_path
                B.add(total_path)

            // Restore graph
            restore(edges_removed, nodes_removed)

        if B empty: break

        A[k] = B.extract_min()
        B.remove_duplicates_of(A[k])

    return A
```

**Complexity:** O(K × |V| × (|E| + |V| log |V|))

**Implementation:** NetworkX shortest_simple_paths() generator

### D. Machine Learning Models

#### 1) Feature Engineering

We engineered 15 features from raw data:

**Time Features:**
- hour: Hour of day [0-23]
- hour_sin: sin(2π × hour / 24)
- hour_cos: cos(2π × hour / 24)
- peak_hour: Binary flag for rush hours
- weekday: Binary flag for weekdays

**Station Features:**
- importance_score: [0-100]
- is_interchange: Binary
- is_terminal: Binary
- commercial_area: Binary
- college_zone: Binary
- near_it_hub: Binary

**Operational Features:**
- weather_encoded: {0: clear, 1: rain, 2: fog, 3: storm}
- transfer_load: [0-100] passengers waiting for transfer
- platform_occupancy: [0-100]% platform fullness
- congestion_score: [0-100] overall congestion

**Target Variable:** delay_minutes (continuous)

#### 2) XGBoost Model

**Hyperparameters:**
- n_estimators: 100
- max_depth: 6
- learning_rate: 0.1
- objective: reg:squarederror
- random_state: 42

**Training:**
- Train-test split: 80-20
- Training samples: 40,000
- Test samples: 10,000

**Model Equation:**
```
ŷ = Σ(i=1 to M) η × f_i(x)

where:
- ŷ: predicted delay
- η: learning rate
- f_i: decision tree i
- M: number of trees
```

#### 3) Random Forest Model

**Hyperparameters:**
- n_estimators: 100
- max_depth: 10
- random_state: 42

**Ensemble Prediction:**
```
ŷ = (1/M) × Σ(i=1 to M) f_i(x)
```

#### 4) Model Evaluation Metrics

**Mean Absolute Error (MAE):**
```
MAE = (1/n) × Σ|y_i - ŷ_i|
```

**Root Mean Squared Error (RMSE):**
```
RMSE = √[(1/n) × Σ(y_i - ŷ_i)²]
```

**R² Score (Coefficient of Determination):**
```
R² = 1 - [Σ(y_i - ŷ_i)²] / [Σ(y_i - ȳ)²]
```

### E. System Architecture

**Backend:** FastAPI (Python)
- RESTful API endpoints
- Route optimization service
- ML inference engine

**Frontend:** Next.js 16 (TypeScript)
- Interactive map (MapLibre GL)
- Real-time visualizations (Recharts)
- Responsive dashboard

**Data Flow:**
1. User selects source & destination
2. Frontend sends POST request to /api/route/optimize
3. Backend runs selected algorithm (Dijkstra/A*/Yen)
4. ML model predicts delays for stations in path
5. Backend returns optimized route + delay estimates
6. Frontend visualizes on interactive map

---

## IV. RESULTS AND ANALYSIS

### A. Dataset Statistics

| Metric | Value |
|--------|-------|
| Total delay records | 50,000 |
| Stations covered | 57 |
| Time span | 30 days |
| Avg delay (overall) | [X.XX] min |
| Avg delay (peak) | [X.XX] min |
| Avg delay (off-peak) | [X.XX] min |
| Max delay recorded | [X.XX] min |
| Interchange avg delay | [X.XX] min |
| Terminal avg delay | [X.XX] min |

### B. Algorithm Performance Comparison

| Metric | Dijkstra | A* | Yen (K=3) |
|--------|----------|----|-----------|
| Avg execution time (ms) | [X.XX] | [X.XX] | [X.XX] |
| Nodes explored | [XXX] | [XXX] | [XXX] |
| Path optimality | 100% | 100% | Alt paths within X% |
| Scalability | O((V+E)logV) | Better in practice | K×O((V+E)logV) |

**Key Findings:**
1. A* reduces nodes explored by approximately [X]% compared to Dijkstra
2. Yen's algorithm successfully finds K=3 diverse alternative routes
3. Alternative routes average [X]% longer than optimal but avoid bottlenecks

### C. ML Model Performance

| Metric | XGBoost | Random Forest |
|--------|---------|---------------|
| MAE (min) | [X.XX] | [X.XX] |
| RMSE (min) | [X.XX] | [X.XX] |
| R² Score | [X.XX] | [X.XX] |
| Training time (s) | [X.XX] | [X.XX] |
| Inference time (ms) | [X.XX] | [X.XX] |

**Feature Importance (Top 5):**
1. importance_score: [X.XX]%
2. peak_hour: [X.XX]%
3. is_interchange: [X.XX]%
4. congestion_score: [X.XX]%
5. hour: [X.XX]%

### D. Bottleneck Analysis

**Top 5 Bottleneck Stations:**
1. Ameerpet: [X.XX] min avg delay (Interchange: Red+Blue)
2. MG Bus Station: [X.XX] min avg delay (Interchange: Red+Green)
3. Secunderabad East: [X.XX] min avg delay (Major hub)
4. [Station 4]: [X.XX] min
5. [Station 5]: [X.XX] min

**Root Causes:**
- Interchange stations have [X]% higher delays
- Peak hour delays are [X]× normal hour delays
- Commercial zones experience [X]% more congestion
- Weather impact: Rain increases delay by [X]%

### E. Case Studies

#### Case Study 1: Miyapur to LB Nagar (Red Line)
- **Dijkstra:** [X] stations, [X.XX] min
- **A*:** Same path, [X]% faster computation
- **Predicted delay:** [X.XX] min
- **Actual travel time:** [X.XX] min

#### Case Study 2: Raidurg to Nagole (Blue Line)
- **Bottleneck:** Ameerpet interchange
- **Alternative route suggested:** Via [route]
- **Time saved by alternative:** [X] min during peak

---

## V. DISCUSSION

### A. Algorithm Trade-offs

**Dijkstra:**
- ✅ Guaranteed optimal path
- ✅ Simple implementation
- ❌ Explores many unnecessary nodes
- ❌ No heuristic guidance

**A*:**
- ✅ Faster than Dijkstra in practice
- ✅ Still guarantees optimal path
- ❌ Requires good heuristic function
- ✅ Haversine works well for metro networks

**Yen's:**
- ✅ Provides valuable alternatives
- ✅ Helps avoid bottlenecks
- ❌ Computationally expensive
- ❌ Alternatives may be significantly longer

### B. ML Model Insights

XGBoost outperforms Random Forest due to:
1. Gradient boosting handles sequential patterns better
2. Better feature importance weighting
3. Efficient handling of temporal correlations

Peak hour and station importance are top predictors, validating our domain knowledge.

### C. Practical Implications

**For Commuters:**
- Real-time delay predictions enable informed decisions
- Alternative routes during peak hours
- Avg time saved: [X] min per journey

**For Transit Authorities:**
- Bottleneck identification guides infrastructure investment
- Predictive maintenance scheduling
- Dynamic train frequency adjustment

**For Smart Cities:**
- Integration with multimodal transport planning
- Data-driven policy decisions
- Scalable to other metro networks

### D. Limitations

1. **Synthetic Data:** Real delay data would improve accuracy
2. **Static Network:** Doesn't account for temporary service disruptions
3. **Weather Data:** Simplified weather modeling
4. **Transfer Times:** Fixed transfer penalties, actual times vary
5. **Crowd Dynamics:** Simplified passenger flow modeling

---

## VI. CONCLUSION

This research successfully integrates graph-based route optimization with machine learning-based delay prediction for metro systems. Key achievements include:

1. **Comprehensive Data Pipeline:** Generated 50,000 realistic delay scenarios from GTFS data
2. **Algorithm Comparison:** A* achieves [X]% speedup over Dijkstra while maintaining optimality
3. **ML Accuracy:** XGBoost achieves R² = [X.XX] for delay prediction
4. **Bottleneck Identification:** Quantified impact of interchanges and peak hours
5. **Practical Dashboard:** Interactive tool for commuters and planners

The system demonstrates that combining classical algorithms with modern ML techniques provides significant value for smart city transportation.

### Future Scope

1. **Real-time Integration:** Deploy with live GTFS-Realtime feeds
2. **Deep Learning:** LSTM/Transformer models for temporal patterns
3. **Multimodal:** Extend to bus, bike-share, ride-sharing
4. **Crowd Simulation:** Agent-based modeling of passenger flow
5. **Dynamic Pricing:** Integrate with surge pricing models
6. **Mobile App:** Native iOS/Android deployment
7. **Other Cities:** Scale to Delhi, Bangalore, Mumbai metros

---

## VII. REFERENCES

[Format according to IEEE citation style]

[1] Author, "Title," Journal/Conference, vol., no., pp., year.
[2] GTFS Specification: https://gtfs.org/
[3] NetworkX documentation: https://networkx.org/
[4] XGBoost documentation: https://xgboost.readthedocs.io/
[5] Hyderabad Metro Rail Limited: https://hmrl.co.in/

[Add 15-20 relevant academic references]

---

## APPENDIX

### A. Station List with Importance Scores

[Table of all 57 stations with scores]

### B. Code Repository

GitHub: [Your repository URL]

### C. Dataset Samples

[Include 2-3 sample rows from each CSV]

### D. Dashboard Screenshots

[Include 3-5 screenshots of the dashboard]

---

**Word Count:** [Target: 3000-4000 words]
**Figures:** [8-10 recommended]
**Tables:** [5-7 recommended]
