import random
import time
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# AgroCops browser dashboard — demo/simulated data only.
st.set_page_config(page_title="AgroCops Central Command", page_icon="🌱", layout="wide")

st.markdown("""
<style>
.stApp { background: #101214; color: #f4f6f8; }
.block-container { padding-top: 1.3rem; padding-bottom: 2rem; }
h1, h2, h3 { color: #f4f6f8; }
[data-testid="stMetric"] { background: #1c2227; border: 1px solid #303940; padding: 12px; border-radius: 12px; }
.sensor-tile { height: 56px; display:flex; align-items:center; justify-content:center;
  border-radius: 7px; color:white; font-weight:700; font-size:12px; margin:2px;
  border: 1px solid rgba(255,255,255,.08); }
.small-note { color:#aab4bd; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

st.title("🌱 AGROCOPS CENTRAL COMMAND")
st.caption("Smart Harvest Security System · Simulated demonstration mode · No physical sensors required")

with st.sidebar:
    st.header("Demo Controls")
    auto_refresh = st.toggle("Auto-refresh readings", value=True)
    refresh_seconds = st.slider("Refresh interval (seconds)", 2, 10, 3)
    seed = st.number_input("Dataset seed", min_value=1, max_value=99999, value=42)
    st.info("This demo uses synthetic/duplicate-style readings. Values are not real sensor measurements.")

random.seed(int(seed))
now = datetime.now()

# Generate reproducible baseline data for 100 sensor tiles.
sensors = []
for r in range(10):
    for c in range(10):
        sensor_id = f"S-{r}-{c}"
        # Mostly nominal, with a small number of warning/critical examples.
        gas = max(180, int(random.gauss(300, 35)))
        temp = round(random.gauss(28.3, 0.7), 1)
        humidity = max(35, min(90, int(random.gauss(65, 4))))
        if (r, c) in [(1, 7), (4, 2), (7, 8)]:
            gas = random.randint(450, 700)
        if (r, c) in [(3, 4), (8, 1)]:
            gas = random.randint(1050, 1300)
        if gas > 1000:
            status, color = "CRITICAL", "#D32F2F"
        elif gas > 400:
            status, color = "WARNING", "#F57C00"
        else:
            status, color = "NOMINAL", "#247A3B"
        sensors.append({"id": sensor_id, "row": r, "col": c, "gas": gas,
                        "temperature": temp, "humidity": humidity,
                        "status": status, "color": color})

df = pd.DataFrame(sensors)
critical_count = int((df.status == "CRITICAL").sum())
warning_count = int((df.status == "WARNING").sum())
nominal_count = int((df.status == "NOMINAL").sum())

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Modules", len(df))
m2.metric("Nominal", nominal_count)
m3.metric("Warnings", warning_count)
m4.metric("Critical", critical_count)

st.subheader("Sensor Grid · 10 × 10")
st.markdown('<div class="small-note">Select a tile below to inspect its simulated readings and trend.</div>', unsafe_allow_html=True)

grid_cols = st.columns(10, gap="small")
for idx, item in df.iterrows():
    with grid_cols[int(item["col"])]:
        if st.button(item["id"], key=f"sensor_{item['row']}_{item['col']}",
                      help=f"{item['status']} · gas/VOC-like value {item['gas']}"):
            st.session_state.selected_sensor = item["id"]
        # Color tile via CSS class-like custom HTML; button remains the click target.
        st.markdown(
            f'<div style="background:{item["color"]};height:5px;border-radius:4px;margin:-7px 0 7px 0;"></div>',
            unsafe_allow_html=True
        )

if "selected_sensor" not in st.session_state:
    st.session_state.selected_sensor = "S-3-4"

selected = df[df.id == st.session_state.selected_sensor].iloc[0]
st.divider()
st.subheader(f"Sensor Details · {selected['id']}")
status_color = selected["color"]
st.markdown(f"**Status:** <span style='color:{status_color};font-weight:700'>{selected['status']}</span>",
            unsafe_allow_html=True)

g1, g2, g3 = st.columns(3)
g1.metric("Temperature", f"{selected['temperature']:.1f} °C")
g2.metric("Humidity", f"{selected['humidity']} %")
g3.metric("Gas / VOC-like level", f"{selected['gas']}")

def gauge(title, value, maximum, suffix, bar_color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value, title={"text": title, "font": {"color": "white"}},
        number={"suffix": suffix, "font": {"color": "white"}},
        gauge={"axis": {"range": [0, maximum], "tickcolor": "white"},
               "bar": {"color": bar_color}, "bgcolor": "#1c2227",
               "bordercolor": "#39434b",
               "steps": [{"range": [0, maximum * .7], "color": "#263039"},
                         {"range": [maximum * .7, maximum], "color": "#3a2a1e"}]}
    ))
    fig.update_layout(height=230, margin=dict(l=15, r=15, t=45, b=10),
                      paper_bgcolor="#101214", font_color="white")
    return fig

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(gauge("Temperature", float(selected["temperature"]), 50, " °C", "#00d4ff"),
                    use_container_width=True)
with c2:
    st.plotly_chart(gauge("Humidity", float(selected["humidity"]), 100, " %", "#00d4ff"),
                    use_container_width=True)

# Repeated/synthetic time-series points, similar to the original 50-point popup chart.
rng = random.Random(int(seed) + int(selected["row"]) * 10 + int(selected["col"]))
times = [now - timedelta(seconds=49-i) for i in range(50)]
values = [max(0, int(selected["gas"] + rng.randint(-25, 25))) for _ in range(50)]
trend = go.Figure()
trend.add_trace(go.Scatter(x=times, y=values, mode="lines+markers",
                           name="Gas / VOC-like level",
                           line=dict(color=status_color, width=2),
                           marker=dict(size=4)))
trend.update_layout(title="Simulated Spoilage-Risk Trend (last 50 samples)",
                    xaxis_title="Time", yaxis_title="Gas / VOC-like level",
                    paper_bgcolor="#101214", plot_bgcolor="#1c2227",
                    font_color="white", height=380,
                    margin=dict(l=20, r=20, t=55, b=25))
trend.update_xaxes(gridcolor="#39434b")
trend.update_yaxes(gridcolor="#39434b", rangemode="tozero")
st.plotly_chart(trend, use_container_width=True)

st.subheader("Dataset Preview")
st.dataframe(df[["id", "temperature", "humidity", "gas", "status"]], use_container_width=True, hide_index=True)

st.caption(f"Last rendered: {now.strftime('%Y-%m-%d %H:%M:%S')} · Demo data only; not validated for real spoilage detection.")

if auto_refresh:
    time.sleep(refresh_seconds)
    st.rerun()
