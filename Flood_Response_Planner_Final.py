import json
import html
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Flood Response & Evacuation Planner", layout="wide")

# Flood-response visual theme: self-contained CSS + SVG (no external image/API dependency).
st.markdown("""
<style>
    :root {
        color-scheme: light;
        --ink: #173247;
        --muted: #526779;
        --line: #d5e3ec;
        --blue: #087ca7;
        --blue-dark: #075985;
        --surface: #ffffff;
    }
    .stApp {
        background: linear-gradient(180deg, #edf6fb 0%, #ffffff 340px) !important;
        color: var(--ink) !important;
    }
    [data-testid="stAppViewContainer"], [data-testid="stMain"],
    [data-testid="stMainBlockContainer"] {
        background: transparent !important;
        color: var(--ink) !important;
    }
    .block-container {
        max-width: 1440px;
        padding: 1.7rem clamp(1rem, 3vw, 2.8rem) 3rem !important;
    }
    /* Force readable foreground colors across Streamlit's inherited theme. */
    .stApp, .stApp p, .stApp span, .stApp label,
    .stApp [data-testid="stMarkdownContainer"],
    .stApp [data-testid="stMarkdownContainer"] p,
    .stApp [data-testid="stCaptionContainer"],
    .stApp [data-testid="stCaptionContainer"] p,
    .stApp [data-testid="stWidgetLabel"],
    .stApp [data-testid="stWidgetLabel"] p {
        color: var(--ink) !important;
    }
    h1, h2, h3, h4, h5, h6,
    .stApp h1, .stApp h2, .stApp h3 {
        color: #12344a !important;
        font-weight: 750 !important;
        letter-spacing: -.02em;
    }
    .stApp [data-testid="stCaptionContainer"],
    .stApp [data-testid="stCaptionContainer"] p {
        color: var(--muted) !important;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #e4f1f8 0%, #f5f9fc 100%) !important;
        border-right: 1px solid #cbdde8;
    }
    [data-testid="stSidebar"] * {
        color: #173247 !important;
    }
    [data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #d4e5ef !important;
        padding: 17px 18px !important;
        border-radius: 15px !important;
        box-shadow: 0 5px 18px rgba(15, 64, 91, .07) !important;
        min-height: 112px;
    }
    [data-testid="stMetric"] label,
    [data-testid="stMetric"] [data-testid="stMetricLabel"],
    [data-testid="stMetric"] [data-testid="stMetricValue"],
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: #173247 !important;
        opacity: 1 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: #526779 !important;
        font-weight: 650 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #075985 !important;
        font-weight: 750 !important;
    }
    [data-testid="stSelectbox"] label,
    [data-testid="stMultiSelect"] label {
        color: #29475c !important;
        font-weight: 650 !important;
    }
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background: #ffffff !important;
        border-color: #b9cfdd !important;
        color: #173247 !important;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid #d5e3ec;
        border-radius: 12px;
        overflow: hidden;
    }
    .flood-hero {
        background: linear-gradient(115deg, #082f49 0%, #075985 58%, #0e7490 100%);
        border-radius: 20px;
        padding: clamp(20px, 3vw, 30px) clamp(20px, 3.5vw, 36px);
        margin: 8px 0 24px;
        color: #ffffff !important;
        box-shadow: 0 12px 30px rgba(8, 47, 73, .17);
        overflow: hidden;
    }
    .flood-hero h2 { color: #ffffff !important; margin: 0 0 9px; font-size: clamp(1.45rem, 2.4vw, 2rem); }
    .flood-hero p { color: #e4f5fc !important; margin: 0; max-width: 760px; line-height: 1.6; }
    .flood-hero .eyebrow { color: #a5f3fc !important; text-transform: uppercase;
        letter-spacing: .13em; font-size: .75rem; font-weight: 800; margin-bottom: 8px; }
    .policy-chart {
        background: #ffffff;
        border: 1px solid #d5e3ec;
        border-radius: 15px;
        padding: 20px 22px;
        box-shadow: 0 5px 18px rgba(15,64,91,.06);
        margin: 8px 0 18px;
    }
    .policy-chart-title { color:#173247; font-weight:750; margin-bottom:16px; }
    .policy-row { display:grid; grid-template-columns:minmax(110px, 170px) 1fr minmax(75px, 100px);
        gap:12px; align-items:center; margin:13px 0; }
    .policy-name { color:#29475c; font-weight:650; overflow-wrap:anywhere; }
    .policy-track { height:17px; background:#e8f1f6; border-radius:99px; overflow:hidden; }
    .policy-fill { height:100%; border-radius:99px; background:linear-gradient(90deg,#0e7490,#38bdf8); }
    .policy-value { color:#12344a; font-weight:750; text-align:right; font-variant-numeric:tabular-nums; }
    @media (max-width: 700px) {
        .block-container { padding: 1rem .8rem 2rem !important; }
        .policy-row { grid-template-columns: 1fr 75px; gap:7px; }
        .policy-track { grid-column:1 / -1; grid-row:2; }
        .policy-value { grid-column:2; grid-row:1; }
    }
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
    # Responsive, high-contrast comparison bars built from the original live metrics.
    # This avoids a chart theme mismatch and does not alter any source values.
    comparison_chart = selected_metrics[["policy", compare_metric]].copy()
    comparison_chart[compare_metric] = pd.to_numeric(
        comparison_chart[compare_metric], errors="coerce"
    )
    comparison_chart = comparison_chart.dropna()
    if not comparison_chart.empty:
        max_value = max(abs(float(v)) for v in comparison_chart[compare_metric]) or 1.0
        rows_html = []
        for _, chart_row in comparison_chart.iterrows():
            policy_label = html.escape(str(chart_row["policy"]).replace("_", " ").title())
            value = float(chart_row[compare_metric])
            width_pct = min(100.0, abs(value) / max_value * 100.0)
            display_value = f"{value:,.1f}" if abs(value) < 1000 else f"{value:,.0f}"
            rows_html.append(
                '<div class="policy-row">'
                f'<div class="policy-name">{policy_label}</div>'
                f'<div class="policy-track"><div class="policy-fill" style="width:{width_pct:.2f}%"></div></div>'
                f'<div class="policy-value">{display_value}</div>'
                '</div>'
            )
        st.markdown(
            '<div class="policy-chart">'
            f'<div class="policy-chart-title">{html.escape(compare_metric.replace("_", " ").title())}</div>'
            + "".join(rows_html)
            + '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("No valid values are available for this comparison metric.")

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

    # Leaflet renders the same GeoJSON layers without requiring Folium.
    # Leaflet is loaded in the browser; no extra Python package is needed.
    with open(roads_path, encoding="utf-8") as f:
        roads_geojson = json.load(f)

    flood_geojson = {"type": "FeatureCollection", "features": []}
    if flood_path.exists():
        with open(flood_path, encoding="utf-8") as f:
            flood_geojson = json.load(f)

    route_coords = []
    route_label = ""
    if paths_path.exists():
        with open(paths_path, encoding="utf-8") as f:
            route_records = json.load(f)
        scenario_routes = [
            r for r in route_records
            if str(r.get("scenario_id")) == selected_scenario
        ]
        if scenario_routes:
            policies = sorted({r.get("policy", "unknown") for r in scenario_routes})
            chosen_policy = st.selectbox("Route policy", policies)
            policy_records = [
                r for r in scenario_routes if r.get("policy") == chosen_policy
            ]
            episode_ids = sorted({int(r.get("episode", 1)) for r in policy_records})
            chosen_episode = st.selectbox("Route episode", episode_ids)
            chosen = next(
                r for r in policy_records
                if int(r.get("episode", 1)) == chosen_episode
            )
            route_ids = [normalize_node_id(n) for n in chosen.get("path", [])]
            missing = [n for n in route_ids if n not in node_lookup]
            if missing:
                st.error(
                    f"{len(missing)} route nodes have no coordinates. "
                    "Re-run Member 3 evaluation and Member 4 export from the same RL_graph."
                )
            elif len(route_ids) >= 2:
                route_coords = [list(node_lookup[n]) for n in route_ids]
                route_label = f"{chosen_policy} evacuation route | Episode {chosen_episode}"
                if not selected_episodes.empty and {"policy", "episode"}.issubset(selected_episodes.columns):
                    selected_row = selected_episodes[
                        (selected_episodes["policy"] == chosen_policy)
                        & (selected_episodes["episode"].astype(int) == chosen_episode)
                    ]
                    if not selected_row.empty:
                        s = selected_row.iloc[0]
                        c1, c2, c3 = st.columns(3)
                        c1.metric(
                            "Route status",
                            "Successful" if bool(s.get("success", False)) else "Not completed",
                        )
                        c2.metric(
                            "Route length",
                            f"{float(s['route_distance_m']):,.0f} m"
                            if pd.notna(s.get("route_distance_m")) else "N/A",
                        )
                        c3.metric(
                            "Flood-risk edges used",
                            str(int(s["flood_edges_used"]))
                            if pd.notna(s.get("flood_edges_used")) else "N/A",
                        )
            else:
                st.info("No route with at least two nodes was recorded for this selection.")
        else:
            st.info("No route records exist for this scenario.")

    # Embed source GeoJSON and route coordinates safely as JSON data.
    roads_json = json.dumps(roads_geojson).replace("</", "<\\/")
    floods_json = json.dumps(flood_geojson).replace("</", "<\\/")
    route_json = json.dumps(route_coords).replace("</", "<\\/")
    route_text = json.dumps(route_label)

    map_html = f"""
    <!DOCTYPE html>
    <html><head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
      <style>
        html, body, #flood-map {{ height:100%; width:100%; margin:0; }}
        .leaflet-container {{ font-family:Arial,sans-serif; }}
        .map-legend {{
          background:#fff; padding:10px 12px; border-radius:8px;
          box-shadow:0 1px 8px #64748b66; color:#1e293b; line-height:1.7;
          font-size:12px;
        }}
        .legend-line {{ display:inline-block; width:22px; border-top:4px solid; vertical-align:middle; margin-right:6px; }}
      </style>
    </head><body>
      <div id="flood-map"></div>
      <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
      <script>
        const roads = {roads_json};
        const floods = {floods_json};
        const route = {route_json};
        const routeLabel = {route_text};
        const map = L.map('flood-map', {{preferCanvas:true}}).setView([{center[0]}, {center[1]}], 15);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
          maxZoom:19, attribution:'&copy; OpenStreetMap contributors'
        }}).addTo(map);

        const normalFeatures = [];
        const riskFeatures = [];
        (roads.features || []).forEach(feature => {{
          const risk = Number((feature.properties || {{}}).flood_risk || 0);
          (risk ? riskFeatures : normalFeatures).push(feature);
        }});
        const normalLayer = L.geoJSON({{type:'FeatureCollection',features:normalFeatures}}, {{
          style: {{color:'#64748b',weight:2,opacity:.85}}
        }}).addTo(map);
        const riskLayer = L.geoJSON({{type:'FeatureCollection',features:riskFeatures}}, {{
          style: {{color:'#f97316',weight:4,opacity:.95}},
          onEachFeature: (feature, layer) => layer.bindTooltip('Historical flood-risk road')
        }}).addTo(map);

        const floodLayer = L.geoJSON(floods, {{
          pointToLayer: (feature, latlng) => L.circleMarker(latlng, {{
            radius:6,color:'#991b1b',weight:1,fillColor:'#ef4444',fillOpacity:.9
          }}),
          onEachFeature: (feature, layer) => {{
            const p = feature.properties || {{}};
            const info = ['F_ID','DEPTH','ZONE','WARD']
              .filter(k => p[k] !== undefined)
              .map(k => `<b>${{k}}:</b> ${{p[k]}}`).join('<br>');
            if (info) layer.bindPopup(info);
          }}
        }}).addTo(map);

        const overlays = {{
          'Road network': normalLayer,
          'Flood-risk roads': riskLayer,
          'Historical flood locations': floodLayer
        }};
        if (route.length >= 2) {{
          const lineColor = routeLabel.toLowerCase().includes('dqn') ? '#2563eb' : '#16a34a';
          const routeLayer = L.polyline(route, {{
            color:lineColor,weight:7,opacity:.95
          }}).bindTooltip(routeLabel).addTo(map);
          L.circleMarker(route[0], {{
            radius:8,color:'#166534',fillColor:'#22c55e',fillOpacity:1
          }}).bindTooltip('Evacuation origin').addTo(map);
          L.circleMarker(route[route.length-1], {{
            radius:8,color:'#991b1b',fillColor:'#ef4444',fillOpacity:1
          }}).bindTooltip('Evacuation destination').addTo(map);
          overlays['Selected evacuation route'] = routeLayer;
          map.fitBounds(routeLayer.getBounds(), {{padding:[30,30]}});
        }}
        L.control.layers(null, overlays, {{collapsed:false}}).addTo(map);
        L.control.scale({{metric:true,imperial:false}}).addTo(map);
        const legend = L.control({{position:'bottomleft'}});
        legend.onAdd = function() {{
          const div = L.DomUtil.create('div','map-legend');
          div.innerHTML = '<b>Map legend</b><br>' +
            '<span class="legend-line" style="border-color:#64748b"></span>Roads<br>' +
            '<span class="legend-line" style="border-color:#f97316"></span>Flood-risk roads<br>' +
            '<span style="color:#dc2626">●</span> Historical flood points<br>' +
            '<span class="legend-line" style="border-color:#2563eb"></span>DQN route / ' +
            '<span style="color:#16a34a">━━</span> Safe reference';
          return div;
        }};
        legend.addTo(map);
      </script>
    </body></html>
    """
    components.html(map_html, height=690, scrolling=False)

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
