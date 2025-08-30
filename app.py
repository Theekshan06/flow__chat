import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.llm_handler import ask_ocean_gpt, extract_sql_from_response
from utils.database import test_connection, execute_query
import time

# Page configuration
st.set_page_config(
    page_title="🌊 FloatChat - Ocean Data Explorer",
    page_icon="🌊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1E90FF;
        text-align: center;
    }
    .subheader {
        font-size: 1.5rem;
        color: #4682B4;
        text-align: center;
    }
    .stButton button {
        background-color: #1E90FF;
        color: white;
    }
    .stButton button:hover {
        background-color: #4682B4;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# App header
st.markdown('<h1 class="main-header">🌊 FloatChat - Your Ocean Data Whisperer</h1>', unsafe_allow_html=True)
st.markdown('<h2 class="subheader">Ask me anything about ARGO float data in the Indian Ocean!</h2>', unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "🌊 Hello! I'm your ocean data assistant. Ask me about ARGO float temperatures, salinity, locations, or anything else! Try: 'Show me the warmest surface waters' or 'Find floats near the equator'"}
    ]

if "sql_query" not in st.session_state:
    st.session_state.sql_query = ""

if "query_results" not in st.session_state:
    st.session_state.query_results = None

# Sidebar
with st.sidebar:
    st.header("🔌 System Status")
    try:
        record_count = test_connection()
        st.success(f"✅ Connected! {record_count} records ready")
        st.info("🌊 85 ARGO floats active\n📍 Indian Ocean region\n📅 2024 data")
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")
    
    st.header("💡 Try These Questions!")
    example_questions = [
        "Show me all floats with surface temperature above 30°C",
        "Find the saltiest water measurements",
        "Which floats are active near the equator?",
        "Compare temperature vs salinity",
        "Show me data from float 4903660",
        "What's the deepest measurement we have?"
    ]
    
    for question in example_questions:
        if st.button(f"💬 {question}"):
            st.session_state.messages.append({"role": "user", "content": question})
            # Process the question
            with st.spinner("🧠 Thinking about ocean data..."):
                # Get LLM response
                llm_response = ask_ocean_gpt(question)
                
                # Extract SQL from response
                sql_query = extract_sql_from_response(llm_response)
                
                if sql_query:
                    st.session_state.sql_query = sql_query
                    
                    # Execute query
                    df, error = execute_query(sql_query)
                    
                    if error:
                        st.session_state.messages.append({"role": "assistant", "content": f"❌ Error: {error}"})
                    else:
                        st.session_state.query_results = df
                        st.session_state.messages.append({"role": "assistant", "content": f"✅ Found {len(df)} records!\n\n```sql\n{sql_query}\n```"})
                else:
                    st.session_state.messages.append({"role": "assistant", "content": llm_response})
            
            st.rerun()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User input
if prompt := st.chat_input("Ask about ocean data..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.write(prompt)
    
    # Process with LLM
    with st.chat_message("assistant"):
        with st.spinner("🧠 Thinking about ocean data..."):
            # Get LLM response
            llm_response = ask_ocean_gpt(prompt)
            
            # Extract SQL from response
            sql_query = extract_sql_from_response(llm_response)
            
            if sql_query:
                st.code(sql_query, language="sql")
                st.session_state.sql_query = sql_query
                
                # Execute query
                df, error = execute_query(sql_query)
                
                if error:
                    st.error(f"❌ {error}")
                    st.session_state.messages.append({"role": "assistant", "content": f"❌ Error: {error}"})
                else:
                    st.success(f"✅ Query executed! Found {len(df)} records.")
                    st.session_state.query_results = df
                    st.session_state.messages.append({"role": "assistant", "content": f"✅ Found {len(df)} records!\n\n```sql\n{sql_query}\n```"})
                    
                    # Show results
                    if not df.empty:
                        st.subheader("📊 Query Results")
                        st.dataframe(df.head(20))
            else:
                st.write(llm_response)
                st.session_state.messages.append({"role": "assistant", "content": llm_response})

# Display results and visualizations if we have data
if st.session_state.query_results is not None and not st.session_state.query_results.empty:
    df = st.session_state.query_results
    
    st.divider()
    st.header("📈 Data Visualizations")
    
    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["Map", "Temperature", "Salinity", "Depth Profile"])
    
    with tab1:
        st.subheader("🗺️ Float Locations")
        if 'latitude' in df.columns and 'longitude' in df.columns:
            # Clean data
            map_df = df.dropna(subset=['latitude', 'longitude']).copy()
            if not map_df.empty:
                # Add size for markers based on temperature if available
                if 'temperature' in map_df.columns:
                    map_df['size'] = (map_df['temperature'] - map_df['temperature'].min() + 1) * 10
                    fig = px.scatter_mapbox(
                        map_df, 
                        lat="latitude", 
                        lon="longitude", 
                        color="temperature",
                        size="size",
                        hover_data=["platform_number", "temperature", "salinity", "pressure"],
                        color_continuous_scale=px.colors.sequential.Viridis,
                        zoom=3,
                        height=500
                    )
                else:
                    fig = px.scatter_mapbox(
                        map_df, 
                        lat="latitude", 
                        lon="longitude", 
                        hover_data=["platform_number"],
                        zoom=3,
                        height=500
                    )
                
                fig.update_layout(mapbox_style="open-street-map")
                fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No location data available for mapping.")
        else:
            st.info("This query doesn't include location data.")
    
    with tab2:
        st.subheader("🌡️ Temperature Analysis")
        if 'temperature' in df.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.histogram(df, x='temperature', title="Temperature Distribution")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if 'pressure' in df.columns:
                    fig = px.scatter(df, x='temperature', y='pressure', 
                                    title="Temperature vs Depth", 
                                    labels={'pressure': 'Depth (dbar)'})
                    fig.update_yaxis(autorange="reversed")  # Reverse y-axis to show depth properly
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    fig = px.box(df, y='temperature', title="Temperature Range")
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No temperature data in this result set.")
    
    with tab3:
        st.subheader("🧂 Salinity Analysis")
        if 'salinity' in df.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.histogram(df, x='salinity', title="Salinity Distribution")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if 'temperature' in df.columns:
                    fig = px.scatter(df, x='temperature', y='salinity', 
                                    title="Temperature vs Salinity",
                                    trendline="lowess")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    fig = px.box(df, y='salinity', title="Salinity Range")
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No salinity data in this result set.")
    
    with tab4:
        st.subheader("📊 Depth Profile")
        if 'pressure' in df.columns and 'temperature' in df.columns:
            fig = go.Figure()
            
            # Group by platform if available
            if 'platform_number' in df.columns:
                for platform in df['platform_number'].unique():
                    platform_df = df[df['platform_number'] == platform]
                    fig.add_trace(go.Scatter(
                        x=platform_df['temperature'], 
                        y=platform_df['pressure'],
                        mode='markers',
                        name=f'Float {platform}',
                        hovertemplate='Temp: %{x}°C<br>Depth: %{y} dbar'
                    ))
            else:
                fig.add_trace(go.Scatter(
                    x=df['temperature'], 
                    y=df['pressure'],
                    mode='markers',
                    hovertemplate='Temp: %{x}°C<br>Depth: %{y} dbar'
                ))
            
            fig.update_yaxis(autorange="reversed", title="Depth (dbar)")
            fig.update_xaxis(title="Temperature (°C)")
            fig.update_layout(title="Temperature Depth Profile")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need both pressure and temperature data for depth profile.")
    
    # Download option
    st.divider()
    st.subheader("💾 Download Results")
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="argo_data.csv",
        mime="text/csv"
    )

# Footer
st.divider()
st.markdown("---")
st.markdown("🏃‍♀️ *Built for the FloatChat challenge!*")

# Create .env file template
with open(".env.template", "w") as f:
    f.write("OPENAI_API_KEY=your_openai_api_key_here\n")

# Create requirements.txt
with open("requirements.txt", "w") as f:
    f.write("""
streamlit==1.28.0
plotly==5.17.0
pandas==2.0.3
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
openai==1.3.0
python-dotenv==1.0.0
""")