from plotly.subplots import make_subplots
import plotly.graph_objects as go

def make_soil_figure(dfg):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=dfg.index, y=dfg["Rain_sum"], name="Lluvia (mm)",
        marker=dict(color="rgba(30,144,255,0.6)"),
        hovertemplate="%{x|%d %b}<br>%{y:.1f} mm<extra></extra>"
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=dfg.index, y=dfg["Air_Relat_Hum_mean"], name="Humedad (%)",
        mode="lines+markers", line=dict(color="teal", width=3, shape="spline"),
        marker=dict(size=6), hovertemplate="%{x|%d %b}<br>%{y:.0f}%<extra></extra>"
    ), secondary_y=True)
    fig.update_layout(
        title=dict(text="<b>🌦️ Precipitaciones y Humedad</b>", x=0.02, xanchor="left"),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode="x unified"
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(200,200,200,0.2)", tickangle=-45)
    fig.update_yaxes(title_text="mm", secondary_y=False)
    fig.update_yaxes(title_text="%", secondary_y=True)
    return fig

def make_temp_figure(dfg):
    fig = go.Figure()
    
    # Banda entre mínima y máxima (solo para el relleno, sin leyenda)
    fig.add_trace(go.Scatter(
        x=dfg.index,
        y=dfg["Air_Temp_max"],
        mode="lines",
        line=dict(color="rgba(255,99,71,0)"),
        hoverinfo="skip",
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=dfg.index,
        y=dfg["Air_Temp_min"],
        mode="lines",
        line=dict(color="rgba(255,99,71,0)"),
        fill="tonexty",
        fillcolor="rgba(255,99,71,0.1)",
        name="Rango min–máx",
        hoverinfo="skip"
    ))

    # Línea media
    fig.add_trace(go.Scatter(
        x=dfg.index, y=dfg["Air_Temp_mean"],
        mode="lines+markers",
        line=dict(color="crimson", width=3, shape="spline"),
        marker=dict(size=6, symbol="circle", color="crimson"),
        name="Media",
        hovertemplate="%{x|%d %b}<br>Media: %{y:.1f}°C<extra></extra>"
    ))

    # Línea mínima (dash)
    fig.add_trace(go.Scatter(
        x=dfg.index, y=dfg["Air_Temp_min"],
        mode="lines",
        line=dict(color="blue", width=2, dash="dash"),
        name="Mínima",
        hovertemplate="%{x|%d %b}<br>Mínima: %{y:.1f}°C<extra></extra>"
    ))

    # Línea máxima (dash)
    fig.add_trace(go.Scatter(
        x=dfg.index, y=dfg["Air_Temp_max"],
        mode="lines",
        line=dict(color="red", width=2, dash="dash"),
        name="Máxima",
        hovertemplate="%{x|%d %b}<br>Máxima: %{y:.1f}°C<extra></extra>"
    ))

    # Layout con título en negrita y leyenda debajo
    fig.update_layout(
        title=dict(text="<b>📈 Temperatura</b>", x=0.02, xanchor="left"),
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode="x unified"
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(200,200,200,0.2)", tickangle=-45)
    fig.update_yaxes(title_text="°C")

    return fig