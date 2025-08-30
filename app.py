import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.llm_handler import ask_ocean_gpt, extract_sql_from_response
from utils.database import test_connection, execute_query

# ---------------------------
# Page config + styles
# ---------------------------
st.set_page_config(page_title="🌊 FloatChat - Ocean Data Explorer",
                   page_icon="🌊", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 3rem; color: #1E90FF; text-align: center; }
    .subheader { font-size: 1.5rem; color: #4682B4; text-align: center; }
    .stButton button { background-color: #1E90FF; color: white; }
    .stButton button:hover { background-color: #4682B4; color: white; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Headers
# ---------------------------
st.markdown('<h1 class="main-header">🌊 FloatChat - Your Ocean Data Whisperer</h1>', unsafe_allow_html=True)
st.markdown('<h2 class="subheader">Ask me anything about ARGO float data in the Indian Ocean!</h2>', unsafe_allow_html=True)

# ---------------------------
# Session state
# ---------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "🌊 Hello! I'm your ocean data assistant. Try asking: 'Show me the warmest surface waters' or 'Find floats near the equator'."}
    ]
if "query_results" not in st.session_state:
    st.session_state.query_results = None

# ---------------------------
# Sidebar
# ---------------------------
with st.sidebar:
    st.header("🔌 System Status")
    try:
        record_count = test_connection()
        st.success(f"✅ Connected! {record_count} records ready")
        st.info("🌊 85 ARGO floats active\n📍 Indian Ocean region\n📅 2024 data")
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")

    st.header("💡 Example Questions")
    example_questions = [
        "Show me all floats with surface temperature above 30°C",
        "Find the saltiest water measurements",
        "Which floats are active near the equator?",
        "Compare temperature vs salinity",
        "Show me data from float 4903660",
        "What's the deepest measurement we have?"
    ]
    for q in example_questions:
        if st.button(f"💬 {q}"):
            st.session_state.messages.append({"role": "user", "content": q})
            with st.spinner("🧠 Thinking..."):
                llm_response = ask_ocean_gpt(q)
                sql = extract_sql_from_response(llm_response)

                if sql:
                    df, error = execute_query(sql)
                    if error:
                        st.session_state.messages.append({"role": "assistant", "content": f"❌ {error}"})
                    else:
                        st.session_state.query_results = df
                        st.session_state.messages.append(
                            {"role": "assistant", "content": f"✅ Found {len(df)} records!\n\n```sql\n{sql}\n```"}
                        )
                else:
                    st.session_state.messages.append({"role": "assistant", "content": llm_response})

# ---------------------------
# Display chat history
# ---------------------------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# ---------------------------
# User input
# ---------------------------
if prompt := st.chat_input("Ask about ocean data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🧠 Thinking..."):
            llm_response = ask_ocean_gpt(prompt)
            sql = extract_sql_from_response(llm_response)

            if sql:
                st.code(sql, language="sql")
                df, error = execute_query(sql)

                if error:
                    st.error(f"❌ {error}")
                    st.session_state.messages.append({"role": "assistant", "content": f"❌ {error}"})
                else:
                    st.success(f"✅ Found {len(df)} records.")
                    st.session_state.query_results = df
                    st.session_state.messages.append(
                        {"role": "assistant", "content": f"✅ Found {len(df)} records!\n\n```sql\n{sql}\n```"}
                    )
                    if not df.empty:
                        st.subheader("📊 Query Results")
                        st.dataframe(df.head(20))
            else:
                st.write(llm_response)
                st.session_state.messages.append({"role": "assistant", "content": llm_response})

# ---------------------------
# Results + visualizations
# ---------------------------
df = st.session_state.query_results
if df is not None and not df.empty:
    st.divider()
    st.header("📈 Data Visualizations")
    tab1, tab2, tab3, tab4 = st.tabs(["Map", "Temperature", "Salinity", "Depth Profile"])

    # Map
    with tab1:
        st.subheader("🗺️ Float Locations")
        if 'latitude' in df.columns and 'longitude' in df.columns:
            map_df = df.dropna(subset=['latitude', 'longitude']).copy()
            if not map_df.empty:
                if 'temperature' in map_df.columns:
                    map_df['size'] = (map_df['temperature'] - map_df['temperature'].min() + 1) * 10
                    fig = px.scatter_mapbox(map_df, lat="latitude", lon="longitude",
                                            color="temperature", size="size",
                                            hover_data=["platform_number", "temperature", "salinity", "pressure"],
                                            color_continuous_scale=px.colors.sequential.Viridis,
                                            zoom=3, height=500)
                else:
                    fig = px.scatter_mapbox(map_df, lat="latitude", lon="longitude",
                                            hover_data=["platform_number"], zoom=3, height=500)
                fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No location data available.")

    # Temperature
    with tab2:
        st.subheader("🌡️ Temperature")
        if 'temperature' in df.columns:
            c1, c2 = st.columns(2)
            with c1: st.plotly_chart(px.histogram(df, x='temperature', title="Temperature Distribution"), use_container_width=True)
            with c2:
                if 'pressure' in df.columns:
                    fig = px.scatter(df, x='temperature', y='pressure', title="Temperature vs Depth")
                    fig.update_yaxis(autorange="reversed")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.plotly_chart(px.box(df, y='temperature', title="Temperature Range"), use_container_width=True)

    # Salinity
    with tab3:
        st.subheader("🧂 Salinity")
        if 'salinity' in df.columns:
            c1, c2 = st.columns(2)
            with c1: st.plotly_chart(px.histogram(df, x='salinity', title="Salinity Distribution"), use_container_width=True)
            with c2:
                if 'temperature' in df.columns:
                    st.plotly_chart(px.scatter(df, x='temperature', y='salinity',
                                               title="Temperature vs Salinity", trendline="lowess"), use_container_width=True)
                else:
                    st.plotly_chart(px.box(df, y='salinity', title="Salinity Range"), use_container_width=True)

    # Depth Profile
    with tab4:
        st.subheader("📊 Depth Profile")
        if 'pressure' in df.columns and 'temperature' in df.columns:
            fig = go.Figure()
            if 'platform_number' in df.columns:
                for platform in df['platform_number'].unique():
                    sub = df[df['platform_number'] == platform]
                    fig.add_trace(go.Scatter(x=sub['temperature'], y=sub['pressure'],
                                             mode='markers', name=f'Float {platform}'))
            else:
                fig.add_trace(go.Scatter(x=df['temperature'], y=df['pressure'], mode='markers'))
            fig.update_yaxis(autorange="reversed", title="Depth (dbar)")
            fig.update_xaxis(title="Temperature (°C)")
            st.plotly_chart(fig, use_container_width=True)

    # Download
    st.divider()
    st.subheader("💾 Download Results")
    st.download_button("Download CSV", data=df.to_csv(index=False),
                       file_name="argo_data.csv", mime="text/csv")

# ---------------------------
# Footer
# ---------------------------
st.divider()
st.markdown("---")
st.markdown("🏃‍♀️ *Built for the FloatChat challenge!*")
