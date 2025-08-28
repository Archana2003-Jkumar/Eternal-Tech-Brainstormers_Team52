# Eternal-Tech-Brainstormers_Team52
## Your Problem Statement:
### Fleet Resource Optimization with AI Agents
# **AI-Driven Dynamic Fleet Reallocation Using Live Traffic, Weather, and Demand Data**

## **Short Introduction**

Efficient last‑mile logistics hinges on assigning the **right vehicle to the right request at the right time**. This project demonstrates a **simulation-driven prototype** for **dynamic fleet reallocation** that ingests **traffic**, **weather**, and **demand** signals to optimize assignments. Two main code segments are executed: (1) **Data Ingestion & Feature Engineering** from OpenWeather, OpenStreetMap (OSM/Nominatim), and simulated demand/traffic; and (2) an **RL environment** trained with **Stable‑Baselines3 (PPO)** to learn an assignment policy that minimizes ETA and penalizes infeasible choices.

---

## **Problem Statement**

**AI to dynamically reallocate fleet vehicles based on live traffic, weather, and demand data.**

### **Why It Matters**

* **Higher utilization** of assets (fewer idle miles, higher load factor).
* **Lower costs & faster ETAs**, improving service reliability.
* **Scalability**: architecture adapts to new cities and additional data sources.

---

## **Data Sources & APIs**

* **OpenWeather API** – current conditions that affect speed (e.g., rain slowdowns).
* **OpenStreetMap & Nominatim** – OSM **.osm** files for nodes and **reverse geocoding** to human‑readable locations/zones.
* **Simulated demand datasets** – time‑varying request intensity by zones.
* *(Optional)* **Google Maps APIs** for production-grade routing/ETAs.

---

## **Methodologies**

1. **Data Ingestion & Feature Engineering**

   * Fetch current weather via OpenWeather: `weather -> description -> weather_factor`.
   * Parse OSM nodes with **pyosmium**; sample reverse-geocode with **Nominatim** (with a proper `User-Agent` and conservative rate usage).
   * **Simulate traffic** per zone and hour (rush-hour slowdowns) to derive **speed (km/h)**.
   * **Assemble per (vehicle, demand)** features:

     * `[capacity, availability, demand_size, adjusted_traffic, eta, distance]`.
     * `eta` approximated from Euclidean distance and speed; weather may scale speed.

2. **Reinforcement Learning (RL) for Assignment**

   * **Environment design**: each **step** corresponds to choosing a vehicle for the **current demand**.
   * **Observation**: matrix of shape `(num_vehicles, feat_dim)` **flattened** to a vector.
   * **Action**: select **vehicle index** (Discrete).
   * **Reward**: `-ETA` with penalties for **capacity violation** and **unavailable** vehicles.
   * **Algorithm**: **PPO** (from Stable‑Baselines3) in a **DummyVecEnv** wrapper.
   * **Outcome**: a policy that **learns to minimize ETA** while avoiding infeasible assignments.

---

## **System Architecture (Block Diagram)**

```
flowchart LR
    A[Raw Inputs] -->|Weather API| B(Weather Ingestion)
    A -->|OSM .osm| C(OSM Parsing via pyosmium)
    A -->|Demand Simulator| D(Demand Generation)

    B --> E[Feature Engineering]
    C --> E
    D --> E

    E --> F{State Builder\n(pairs: vehicle × demand)}
    F --> G[RL Env (Gym)]
    G --> H[PPO Agent (SB3)]
    H --> I[Policy]

    I --> J[Assignment Decisions]
    J --> K[KPIs: ETA, Utilization, Feasibility]
```

---

## **Workflow**

1. **Weather Fetch (OpenWeather)**

   * Request **current conditions** using `q=<city>` or `(lat, lon)` and metric units.
   * Extract `weather[0].description` and compute **`weather_factor`** (e.g., rain ⇒ 1.2 slowdown).

2. **OSM Node Extraction & Reverse Geocoding**

   * Parse `.osm` with **osmium.SimpleHandler** → collect `{id, lat, lon, tags}`.
   * **Reverse Geocode** a **small sample** of nodes via Nominatim to infer zones like **Downtown / Airport / Suburb** (rate‑limited; use `User-Agent`).

3. **Traffic Simulation**

   * Zone‑specific **base speed** (e.g., Downtown < Airport < Other).
   * **Rush hours** (07–09, 17–19) reduce speed by 20–50%.

4. **Demand Simulation**

   * Hourly Poisson process per zone with configurable **intensity**.
   * Generate `(time, zone, lat, lon, demand_size_kg)` per request.

5. **Feature Engineering & State Matrix**

   * For each **(vehicle, demand)** pair, compute **distance**, **ETA**, and **adjusted\_traffic** with weather impact.
   * Build `pair_features[T, M, feat_dim]` and parallel vectors for **vehicle capacities** and **demand sizes**.

6. **RL Environment & Training (PPO)**

   * **Observation**: flattened features for all vehicles for the current demand.
   * **Action**: choose the **best vehicle**.
   * **Reward**: `-ETA`, minus **100** if capacity < demand size, minus **10** if vehicle unavailable.
   * Train PPO for **a few thousand timesteps** to learn a reasonable policy.

7. **Inference**

   * Reset env, feed observations, and obtain **vehicle index** per demand from the learned policy.

---

## **Executed Code Segments — What They Do**

### **Segment 1 — Data & Features**

* **OpenWeather Query** (current weather):

  * Example uses `q="India"`; in practice, specify **city** (e.g., `Bengaluru`) or **lat/lon** for precision.
  * Parses `temp` and `description` for contextual understanding.
* **OSM Parsing & Nominatim Reverse Geocoding**:

  * `NodeHandler` collects nodes; **sampled** reverse geocoding (e.g., `head(10/15)`) avoids rate limit.
  * **Zone detection** based on keywords in `display_name` (downtown/airport/suburb/other).
* **Traffic Simulation**:

  * Hour‑of‑day and zone‑based speeds → **`traffic_speed_kmh`** per demand.
* **State Vector**:

  * For each vehicle–demand pair, compute `[capacity, availability, demand_size, adjusted_traffic, eta, distance]` and stack into the **state matrix**.

### **Segment 2 — RL Environment & PPO**

* **Gym Environment** (`FleetAssignmentEnv`):

  * **Observation space**: continuous Box with shape `(num_vehicles * feat_dim,)`.
  * **Action space**: `Discrete(num_vehicles)`.
  * **Step logic**: returns **next observation, reward, done, info**; logs assignments.
* **Training**:

  * Wrap env with `DummyVecEnv`.
  * Train **PPO** with `MlpPolicy`, e.g., `total_timesteps=5000`.
  * **Reward shaping** encourages feasible, fast assignments.

---

## **Execution Guide (Reproducible Steps)**

1. **Environment Setup**

   * Python ≥ 3.10
   * Install deps:

     ```bash
     pip install requests osmium pandas numpy gym==0.26.2 "shimmy>=2.0" stable-baselines3[extra]
     ```

     > Note: Gym vs Gymnasium compatibility handled via **shimmy**. SB3 requires a **vectorized env**.

2. **Data Prep**

   * Place your **`map.osm`** in the working directory.
   * (Optional) Prepare **`synthetic_fleet_basic.csv`** or use the inline toy `fleet_df`.

3. **Run Segment 1**

   * Execute weather fetch, OSM parse, Nominatim reverse geocoding (sampled), traffic simulation, and state building.

4. **Run Segment 2**

   * Build `pair_features` using your `fleet_df` & `demand_df`.
   * Train PPO; save model via `model.save("fleet_assign_ppo")`.

5. **Inference**

   * `model.predict(obs, deterministic=True)` → **vehicle index** for the current demand.

---

## **How This Optimizes Well**

* **Data‑Aware Decisions**: Incorporates **traffic**, **weather**, and **demand size** directly into the **state**.
* **Feasibility First**: Heavy penalties for **capacity violations** and **unavailable** vehicles keep solutions realistic.
* **ETA Minimization**: Negative ETA reward aligns with **service speed** optimization.
* **Generalizes**: RL policy **learns patterns** (rush hours, zone effects) instead of fixed heuristics.
* **Extensible**: Swap in **real routing APIs** for more accurate ETAs without changing the learning scaffolding.

---

## **KPIs & Evaluation (for the Prototype)**

* **Average ETA** per assignment (↓ is better).
* **Feasibility rate** (capacity‑respecting assignments) (↑ is better).
* **Vehicle utilization**: % time active vs idle (↑ is better).
* **Penalty events**: counts of infeasible/unavailable selections (↓ is better).

---

## **Limitations & Next Steps**

* **ETA approximation** uses Euclidean distance and simulated speed; integrate **routing APIs** for network distance.
* **Nominatim rate limits** → cache results or pre‑label zones.
* **Static capacity** in episodes; extend to **inventory‑aware** multi‑stop routing.
* **Single‑demand step**; extend to **batching**, **rebalancing**, and **multi‑objective** rewards (cost, SLA, energy).
* **Weather factor** simplified; map to **speed distributions** per condition (rain, fog, heat).

---

## **Conclusion**

This prototype demonstrates a **practical, extensible pipeline** for **dynamic fleet reallocation**. By fusing **live/near‑real‑time signals** (traffic, weather) with **demand patterns** and training an **RL policy** to reduce ETA while avoiding infeasibility, the system **improves utilization and service quality**. The modular design allows straightforward **upgrades** (routing APIs, richer rewards, multi‑city scaling) for production.

---

## Architecture

* Weather (OpenWeather), OSM (pyosmium + Nominatim), Demand Simulator → Feature Engineering → RL Env → PPO Policy → Assignments.


