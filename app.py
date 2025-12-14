import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output, ctx

# =========================================================
# 1. LOAD + PREP DATA
# =========================================================
try:
    df = pd.read_csv("/Users/rayyanahmad/Documents/Visulisation_Project/output_EDA_analysis.csv")
except:
    # Fallback for demonstration if file missing
    print("Error: csv file not found.")
    df = pd.DataFrame()

# Precompute global aggregates
global_fatalities = df["fatalities"].sum()
global_teisc = df["TEIS"].mean()
global_trend = df.groupby("Year").agg(
    TEIS=("TEIS", "mean"),
    fatalities=("fatalities", "sum")
).reset_index()

# Precompute The Structural Drag (Regression Line) for the Scatter
# We calculate the OLS line coordinates once using Plotly Express
try:
    trendline_fig = px.scatter(df, x="TEIS", y="GDP_growth_pct", trendline="ols")
    trendline_trace = trendline_fig.data[1]  # Extract the OLS line trace
    trendline_trace.line.color = 'red'
    trendline_trace.line.dash = 'dash'
    trendline_trace.name = 'Structural Drag (Global)'
except:
    trendline_trace = go.Scatter() # Empty fallback if statsmodels missing

# =========================================================
# 2. DASH APPLICATION (HD DESIGN WITH INJECTED CSS)
# =========================================================
app = Dash(__name__)
server = app.server

# Professional CSS Styling (Injected directly so you don't need a CSS file)
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Global Risk Monitor</title>
        {%favicon%}
        {%css%}
        <style>
            body { font-family: 'Segoe UI', sans-serif; background-color: #f4f6f9; margin: 0; }
            .header-box { background: white; padding: 20px; border-bottom: 3px solid #2c3e50; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px; }
            .kpi-container { display: flex; gap: 20px; margin-bottom: 20px; padding: 0 20px; }
            .kpi-box { flex: 1; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-align: center; border-top: 4px solid transparent; }
            .kpi-box:hover { transform: translateY(-2px); transition: all 0.2s; }
            .viz-container { display: flex; gap: 20px; padding: 0 20px; margin-bottom: 20px; }
            .viz-box { flex: 1; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
            .btn-reset { background-color: #e74c3c; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; }
            .btn-reset:hover { background-color: #c0392b; }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.layout = html.Div([

    # ---------------- HEADER ----------------
    html.Div([
        html.H1("Global Economic Risk Monitor", style={"margin": "0", "color": "#2c3e50"}),
        html.P("Conflict Exposure & Sectoral Vulnerability Cockpit", style={"margin": "5px 0 0 0", "color": "#7f8c8d"}),
        html.Button("↺ Reset Global View", id="btn-reset", className="btn-reset", style={"float": "right", "marginTop": "-40px"})
    ], className="header-box"),

    # ---------------- KPI ROW ----------------
    html.Div([
        html.Div([html.H4("Selected Region", style={"color": "#95a5a6", "margin": 0}), 
                  html.H2(id="kpi-country", children="Global View", style={"color": "#2c3e50", "margin": "10px 0"})], 
                  className="kpi-box", style={"borderTopColor": "#2c3e50"}),
        
        html.Div([html.H4("Total Fatalities", style={"color": "#95a5a6", "margin": 0}), 
                  html.H2(id="kpi-fatalities", children=f"{global_fatalities:,.0f}", style={"color": "#c0392b", "margin": "10px 0"})], 
                  className="kpi-box", style={"borderTopColor": "#c0392b"}),
        
        html.Div([html.H4("Avg Risk Intensity (TEIS)", style={"color": "#95a5a6", "margin": 0}), 
                  html.H2(id="kpi-teis", children=f"{global_teisc:.3f}", style={"color": "#27ae60", "margin": "10px 0"})], 
                  className="kpi-box", style={"borderTopColor": "#27ae60"}),
    ], className="kpi-container"),

    # ---------------- MAP + TREND ROW ----------------
    html.Div([
        html.Div([
            html.H3("1. Spatial Risk Concentration", style={"color": "#2c3e50", "marginTop": 0}),
            dcc.Graph(id="map-chart", style={"height": "350px"})
        ], className="viz-box"),

        html.Div([
            html.H3("2. Temporal Dynamics", style={"color": "#2c3e50", "marginTop": 0}),
            dcc.Graph(id="trend-chart", style={"height": "350px"})
        ], className="viz-box"),
    ], className="viz-container"),

    # ---------------- SCATTER ROW ----------------
    html.Div([
        html.Div([
            html.H3("3. Statistical Validation: The 'Structural Drag'", style={"color": "#2c3e50", "marginTop": 0}),
            html.P("Red Dashed Line = Global Growth Ceiling (Regression Model)", style={"fontSize": "12px", "color": "red"}),
            dcc.Graph(id="scatter-chart", style={"height": "400px"})
        ], className="viz-box")
    ], className="viz-container", style={"paddingBottom": "40px"})

])

# =========================================================
# 3. INTERACTIVITY
# =========================================================
@app.callback(
    [Output("map-chart", "figure"),
     Output("trend-chart", "figure"),
     Output("scatter-chart", "figure"),
     Output("kpi-country", "children"),
     Output("kpi-fatalities", "children"),
     Output("kpi-teis", "children")],
    [Input("map-chart", "clickData"),
     Input("btn-reset", "n_clicks")]
)
def update_dashboard(clickData, n_clicks):
    
    # Check trigger to handle "Reset" button
    triggered_id = ctx.triggered_id
    
    # DEFAULT / RESET STATE
    if not clickData or triggered_id == "btn-reset":
        selected_country = "Global View"
        trend_df = global_trend
        kpi_fat = global_fatalities
        kpi_teis = global_teisc
        
        # Default Scatter: All points steelblue
        scatter_colors = ["steelblue"] * len(df)
        scatter_opacity = [0.6] * len(df)
        
    # FILTERED STATE
    else:
        selected_country = clickData["points"][0]["location"]
        df_filtered = df[df["Country"] == selected_country]
        
        # Check if country has data
        if df_filtered.empty:
            trend_df = global_trend # Fallback
        else:
            trend_df = df_filtered.groupby("Year").agg(
                TEIS=("TEIS", "mean"), fatalities=("fatalities", "sum")
            ).reset_index()
            
        kpi_fat = df_filtered["fatalities"].sum()
        kpi_teis = df_filtered["TEIS"].mean()
        
        # Scatter Benchmarking Logic: Grey out world, highlight country in Red
        scatter_colors = ["lightgrey"] * len(df)
        scatter_opacity = [0.3] * len(df)
        for idx in df.index[df["Country"] == selected_country]:
            scatter_colors[idx] = "red"
            scatter_opacity[idx] = 1.0

    # --- 1. BUILD MAP ---
    # We use uirevision to prevent map from resetting zoom on click
    map_agg = df.groupby("Country")["TEIS"].mean().reset_index()
    fig_map = px.choropleth(map_agg, locations="Country", locationmode="country names",
                            color="TEIS", color_continuous_scale="Reds")
    fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), uirevision='constant', 
                         geo=dict(showframe=False, showcoastlines=False, projection_type='equirectangular'))

    # --- 2. BUILD TREND ---
    fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
    fig_trend.add_trace(go.Bar(x=trend_df["Year"], y=trend_df["fatalities"], name="Fatalities", marker_color="#bdc3c7", opacity=0.7), secondary_y=False)
    fig_trend.add_trace(go.Scatter(x=trend_df["Year"], y=trend_df["TEIS"], name="TEIS Intensity", line=dict(color="#27ae60", width=3)), secondary_y=True)
    fig_trend.update_layout(margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"), plot_bgcolor="white")
    fig_trend.update_yaxes(title_text="Fatalities", secondary_y=False, showgrid=False)
    fig_trend.update_yaxes(title_text="TEIS Index", secondary_y=True, showgrid=False)

    # --- 3. BUILD SCATTER ---
    fig_scatter = go.Figure()
    # A. Add the Regression Line (Structural Drag) - ALWAYS VISIBLE
    if trendline_trace:
        fig_scatter.add_trace(trendline_trace)
    # B. Add the Points
    fig_scatter.add_trace(go.Scatter(
        x=df["TEIS"], y=df["GDP_growth_pct"], mode="markers",
        marker=dict(size=8, color=scatter_colors, opacity=scatter_opacity),
        text=df["Country"], name="Countries"
    ))
    fig_scatter.update_layout(xaxis_title="Risk Intensity (TEIS)", yaxis_title="GDP Growth (%)",
                              margin=dict(l=0, r=0, t=10, b=0), plot_bgcolor="white", showlegend=False)
    fig_scatter.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
    fig_scatter.update_yaxes(showgrid=True, gridcolor="#f0f0f0")

    return fig_map, fig_trend, fig_scatter, selected_country, f"{kpi_fat:,.0f}", f"{kpi_teis:.3f}"

if __name__ == "__main__":
    app.run(debug=True, port=8050)


    #### Code: Context-Preserving Highlight Logic
@app.callback(...)
def update_dashboard(clickData):
    if selected_country:
        #### Baseline (global context)
        scatter_colors = ["lightgrey"] * len(df)
        scatter_opacity = [0.3] * len(df)
        
        #### Highlight selected region without removing global data
        for idx in df.index[df["Country"] == selected_country]:
            scatter_colors[idx] = "red"
            scatter_opacity[idx] = 1.0
