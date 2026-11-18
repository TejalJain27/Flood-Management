import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
import folium
import streamlit.components.v1 as components
from folium.plugins import Fullscreen, MeasureControl

st.set_page_config(page_title="Flood Response & Evacuation Planner", layout="wide")

# Flood-response visual theme: self-contained CSS + SVG (no external image/API dependency).
st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #f2f8fc 0%, #ffffff 42%); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #e5f2fa 0%, #f4f9fc 100%); }
    .block-container { padding-top: 1.5rem; }
    h1, h2, h3 { color: #12344a; }
    [data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #d8e8f1;
        padding: 14px 16px; border-radius: 14px;
        box-shadow: 0 4px 14px rgba(15, 64, 91, .06);
    }
    div[data-testid="stPlotlyChart"], div[data-testid="stDataFrame"] {
        background: #ffffff; border-radius: 12px;
    }
    .flood-hero {
        background: linear-gradient(115deg, #082f49 0%, #075985 58%, #0e7490 100%);
        border-radius: 18px; padding: 22px 26px; margin: 8px 0 22px;
        color: white; box-shadow: 0 10px 26px rgba(8, 47, 73, .16);
        overflow: hidden;
    }
    .flood-hero h2 { color: #ffffff; margin: 0 0 7px; font-size: 1.65rem; }
    .flood-hero p { color: #d9f1fb; margin: 0; max-width: 680px; }
    .flood-hero .eyebrow { color: #a5f3fc; text-transform: uppercase;
        letter-spacing: .13em; font-size: .72rem; font-weight: 700; }
</style>
<div class="flood-hero">
  <div class="eyebrow">Flood resilience • Chennai, India</div>
  <h2>Plan safer routes. Respond smarter.</h2>
  <p>Explore historical flood hotspots, compare evacuation strategies, and inspect
  scenario-based routes across the Velachery road network.</p>
  <svg viewBox="0 0 900 145" role="img" aria-label="Illustration of a flooded city, rain clouds and a rescue boat"
       style="width:100%;height:112px;margin-top:10px" xmlns="http://www.w3.org/2000/svg">
    <circle cx="760" cy="34" r="22" fill="#bae6fd" opacity=".8"/>
    <path d="M0 105 L0 80 55 80 55 54 83 54 83 80 120 80 120 42 151 42 151 80 194 80 194 62 225 62 225 80 270 80 270 35 304 35 304 80 345 80 345 58 375 58 375 80 420 80 420 48 455 48 455 80 505 80 505 65 535 65 535 80 590 80 590 44 622 44 622 80 665 80 665 58 695 58 695 80 740 80 740 56 770 56 770 80 810 80 810 47 845 47 845 80 900 80 900 105Z" fill="#d8f1fa" opacity=".75"/>
    <g fill="#f0f9ff" opacity=".8">
      <path d="M115 24a18 18 0 0 1 35-5 15 15 0 0 1 22 14h-58a13 13 0 0 1 1-9z"/>
      <path d="M520 17a16 16 0 0 1 31-4 14 14 0 0 1 20 13h-52a12 12 0 0 1 1-9z"/>
    </g>
    <path d="M0 105 Q110 91 220 105 T440 105 T660 105 T900 105 V145 H0Z" fill="#38bdf8"/>
    <path d="M0 120 Q110 106 220 120 T440 120 T660 120 T900 120" fill="none" stroke="#bae6fd" stroke-width="4" opacity=".9"/>
    <path d="M565 98 L655 98 640 116 583 116Z" fill="#fbbf24"/>
    <path d="M610 68 L610 97 637 97 637 68Z" fill="#f8fafc"/>
    <path d="M610 68 L637 68 623 51Z" fill="#fbbf24"/>
    <path d="M590 98 L590 89 603 89 603 98" fill="#f8fafc"/>
    <path d="M635 98 L635 89 648 89 648 98" fill="#f8fafc"/>
    <path d="M600 122 Q623 130 646 122" fill="none" stroke="#e0f2fe" stroke-width="3"/>
  </svg>
</div>
""", unsafe_allow_html=True)
st.caption("Scenario-based decision-support prototype | Velachery, Chennai")

# Locate generated evaluation files in common deployment layouts.
APP_DIR = Path(__file__).resolve().parent
DATA_CANDIDATES = [
    APP_DIR / "member4_dashboard_data",  # recommended GitHub layout
    APP_DIR,                             # files placed beside app.py
    Path("/content/member4_dashboard_data"),  # Google Colab layout
]
DATA = next(
    (folder for folder in DATA_CANDIDATES
     if (folder / "scenario_metrics.csv").is_file()),
    DATA_CANDIDATES[0],
)

def read_csv(filename):
    path = DATA / filename
    return pd.read_csv(path) if path.is_file() else pd.DataFrame()

metrics = read_csv("scenario_metrics.csv")
episodes = read_csv("scenario_episode_results.csv")
config = read_csv("scenario_configuration.csv")
if metrics.empty:
    st.error("Scenario evaluation data is not present in this deployment.")
    st.markdown(
        "**Required fix:** run the notebook through the **Member 3 evaluation** "
        "and **Member 4: Prepare Dashboard Data** cells, then upload the generated "
        "`member4_dashboard_data` folder to the same GitHub repository as `app.py`."
    )
    st.code(
        "your-repository/\\n"
        "├── app.py\\n"
        "├── requirements.txt\\n"
        "└── member4_dashboard_data/\\n"
        "    ├── scenario_metrics.csv\\n"
        "    ├── scenario_episode_results.csv\\n"
        "    ├── scenario_configuration.csv\\n"
        "    ├── scenario_paths.json\\n"
        "    ├── road_nodes.csv\\n"
        "    ├── roads.geojson\\n"
        "    └── historical_flood_points.geojson",
        language="text",
    )
    st.caption(f"Checked data locations: {', '.join(str(p) for p in DATA_CANDIDATES)}")
    st.stop()
if "success_rate_pct" not in metrics.columns and "success_rate" in metrics.columns:
    metrics["success_rate_pct"] = (metrics["success_rate"] * 100).round(1)
if "success_rate_pct" not in metrics.columns:
    st.error("Metrics file has no success-rate column.")
    st.stop()

scenario_options = metrics["scenario_id"].dropna().astype(str).unique().tolist()
labels = {}
if not config.empty and {"scenario_id", "label"}.issubset(config.columns):
    labels = dict(zip(config["scenario_id"].astype(str), config["label"].astype(str)))
st.sidebar.header("Dashboard controls")
selected_scenario = st.sidebar.selectbox("Disaster scenario", scenario_options,
    format_func=lambda value: f"{value} — {labels.get(value, value)}")
selected_metrics = metrics[metrics["scenario_id"].astype(str) == selected_scenario].copy()
selected_episodes = episodes[episodes["scenario_id"].astype(str) == selected_scenario].copy() if not episodes.empty else episodes

st.subheader("Scenario performance")
dqn_rows = selected_metrics[selected_metrics["policy"] == "dqn"]
if not dqn_rows.empty:
    row = dqn_rows.iloc[0]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("DQN success rate", f"{float(row['success_rate_pct']):.1f}%")
    k2.metric("Mean route distance", f"{row['mean_distance_m']:.0f} m" if pd.notna(row.get("mean_distance_m")) else "N/A")
    k3.metric("Mean steps", f"{row['mean_steps']:.1f}" if pd.notna(row.get("mean_steps")) else "N/A")
    k4.metric("Mean flood-risk edges", f"{row['mean_flood_edges']:.1f}" if pd.notna(row.get("mean_flood_edges")) else "N/A")
else:
    st.info("No DQN summary row exists for this scenario.")

st.subheader("DQN vs Safe Reference")
available_metrics = [x for x in ["success_rate_pct", "mean_distance_m", "mean_steps", "mean_flood_edges", "mean_compute_ms"] if x in selected_metrics.columns]
if available_metrics:
    compare_metric = st.selectbox("Comparison metric", available_metrics, format_func=lambda x: x.replace("_", " ").title())
    st.plotly_chart(px.bar(selected_metrics, x="policy", y=compare_metric, color="policy", barmode="group", title=compare_metric.replace("_", " ").title()), use_container_width=True)

st.subheader("Evacuation map")
nodes_path = DATA / "road_nodes.csv"
roads_path = DATA / "roads.geojson"
flood_path = DATA / "historical_flood_points.geojson"
paths_path = DATA / "scenario_paths.json"
if not nodes_path.exists() or not roads_path.exists():
    st.warning("Map data is missing. Run the Member 4 data-export cell.")
else:
    node_df = pd.read_csv(nodes_path)
    def normalize_node_id(value):
        text = str(value).strip()
        try:
            number = float(text)
            if number.is_integer():
                return str(int(number))
        except (TypeError, ValueError):
            pass
        return text
    node_lookup = {normalize_node_id(r["node_id"]): (float(r["latitude"]), float(r["longitude"])) for _, r in node_df.iterrows()}
    center = [float(node_df["latitude"].mean()), float(node_df["longitude"].mean())]

    # OpenStreetMap standard tiles avoid the CARTO API-key watermark.
    fmap = folium.Map(location=center, zoom_start=15, tiles="OpenStreetMap", control_scale=True, prefer_canvas=True)
    Fullscreen(position="topleft").add_to(fmap)
    MeasureControl(position="topleft", primary_length_unit="meters").add_to(fmap)
    with open(roads_path, encoding="utf-8") as f:
        roads_geojson = json.load(f)

    normal_roads, risk_roads = [], []
    for feature in roads_geojson.get("features", []):
        risk = int(feature.get("properties", {}).get("flood_risk", 0) or 0)
        (risk_roads if risk else normal_roads).append(feature)

    normal_layer = folium.FeatureGroup(name="Road network", show=True)
    if normal_roads:
        folium.GeoJson({"type": "FeatureCollection", "features": normal_roads},
            style_function=lambda f: {"color": "#64748b", "weight": 1.6, "opacity": 0.8}).add_to(normal_layer)
    normal_layer.add_to(fmap)

    risk_layer = folium.FeatureGroup(name="Historical flood-risk roads", show=True)
    if risk_roads:
        folium.GeoJson({"type": "FeatureCollection", "features": risk_roads},
            style_function=lambda f: {"color": "#f97316", "weight": 3.4, "opacity": 0.95},
            tooltip="Road associated with historical flood records").add_to(risk_layer)
    risk_layer.add_to(fmap)

    if flood_path.exists():
        with open(flood_path, encoding="utf-8") as f:
            flood_geojson = json.load(f)
        flood_features = flood_geojson.get("features", [])
        if flood_features:
            fields = [x for x in ["F_ID", "DEPTH", "ZONE", "WARD"] if x in flood_features[0].get("properties", {})]
            folium.GeoJson(flood_geojson, name="Historical flood locations",
                marker=folium.CircleMarker(radius=5, color="#b91c1c", weight=1, fill=True, fill_color="#ef4444", fill_opacity=0.9),
                tooltip=folium.GeoJsonTooltip(fields=fields) if fields else None).add_to(fmap)

    if paths_path.exists():
        with open(paths_path, encoding="utf-8") as f:
            route_records = json.load(f)
        scenario_routes = [r for r in route_records if str(r.get("scenario_id")) == selected_scenario]
        if scenario_routes:
            policies = sorted({r.get("policy", "unknown") for r in scenario_routes})
            chosen_policy = st.selectbox("Route policy", policies)
            policy_records = [r for r in scenario_routes if r.get("policy") == chosen_policy]
            episode_ids = sorted({int(r.get("episode", 1)) for r in policy_records})
            chosen_episode = st.selectbox("Route episode", episode_ids)
            chosen = next(r for r in policy_records if int(r.get("episode", 1)) == chosen_episode)
            route_ids = [normalize_node_id(n) for n in chosen.get("path", [])]
            missing = [n for n in route_ids if n not in node_lookup]
            if missing:
                st.error(f"{len(missing)} route nodes have no coordinates. Re-run Member 3 evaluation and Member 4 export from the same RL_graph.")
            elif len(route_ids) >= 2:
                coords = [node_lookup[n] for n in route_ids]
                route_color = "#2563eb" if chosen_policy == "dqn" else "#16a34a"
                route_group = folium.FeatureGroup(name=f"Selected route: {chosen_policy}", show=True)
                folium.PolyLine(coords, color=route_color, weight=7, opacity=0.95,
                    tooltip=f"{chosen_policy} evacuation route | Episode {chosen_episode}").add_to(route_group)
                stride = max(1, len(coords) // 35)
                for point in coords[1:-1:stride]:
                    folium.CircleMarker(point, radius=2.5, color=route_color, fill=True, fill_opacity=0.9).add_to(route_group)
                folium.Marker(coords[0], tooltip="Evacuation origin", icon=folium.Icon(color="green", icon="play", prefix="fa")).add_to(route_group)
                folium.Marker(coords[-1], tooltip="Evacuation destination", icon=folium.Icon(color="red", icon="flag", prefix="fa")).add_to(route_group)
                route_group.add_to(fmap)
                fmap.fit_bounds(coords, padding=(35, 35))
                if not selected_episodes.empty and {"policy", "episode"}.issubset(selected_episodes.columns):
                    selected_row = selected_episodes[(selected_episodes["policy"] == chosen_policy) & (selected_episodes["episode"].astype(int) == chosen_episode)]
                    if not selected_row.empty:
                        s = selected_row.iloc[0]
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Route status", "Successful" if bool(s.get("success", False)) else "Not completed")
                        c2.metric("Route length", f"{float(s['route_distance_m']):,.0f} m" if pd.notna(s.get("route_distance_m")) else "N/A")
                        c3.metric("Flood-risk edges used", str(int(s["flood_edges_used"])) if pd.notna(s.get("flood_edges_used")) else "N/A")
            else:
                st.info("No route with at least two nodes was recorded for this selection.")
        else:
            st.info("No route records exist for this scenario.")

    legend = '<div style="position:fixed;bottom:24px;left:24px;z-index:9999;background:white;padding:9px 12px;border:1px solid #bbb;border-radius:6px;font-size:12px;color:#222;box-shadow:0 1px 5px rgba(0,0,0,.25)"><b>Map legend</b><br><span style="color:#64748b">━━</span> Roads<br><span style="color:#f97316">━━</span> Flood-risk roads<br><span style="color:#dc2626">●</span> Historical flood points<br><span style="color:#2563eb">━━</span> DQN route / <span style="color:#16a34a">━━</span> Safe reference</div>'
    fmap.get_root().html.add_child(folium.Element(legend))
    folium.LayerControl(collapsed=False).add_to(fmap)
    components.html(fmap.get_root().render(), height=690, scrolling=False)

st.subheader("Episode results")
if not selected_episodes.empty:
    st.dataframe(selected_episodes, use_container_width=True, hide_index=True)
else:
    st.info("No episode-level results are available for this scenario.")
with st.expander("Scenario assumptions"):
    if not config.empty:
        st.dataframe(config[config["scenario_id"].astype(str) == selected_scenario], use_container_width=True, hide_index=True)
    else:
        st.info("Scenario configuration file not found.")
st.caption("Prototype for scenario-based analysis; not a real-world emergency dispatch system. Live road closures, shelter capacity and resource inventories are not included in the supplied data.")
