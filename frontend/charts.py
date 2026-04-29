"""Chart factory functions for Streamlit pages."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from frontend.theme import DARK_BG, MUTED_GREEN, SCIENTIFIC_CYAN, SOFT_RED, TEXT_COLOR


def create_e_factor_gauge(e_factor: float):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=e_factor,
            title={"text": "", "font": {"color": SCIENTIFIC_CYAN, "size": 1}},
            number={"font": {"size": 44, "color": TEXT_COLOR}},
            gauge={
                "axis": {"range": [None, 10]},
                "bar": {"color": MUTED_GREEN},
                "steps": [
                    {"range": [0, 2], "color": "rgba(102,255,153,0.2)"},
                    {"range": [2, 5], "color": "rgba(0,212,255,0.2)"},
                    {"range": [5, 10], "color": "rgba(255,102,102,0.2)"},
                ],
            },
        )
    )
    fig.update_layout(
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font={"color": TEXT_COLOR},
        height=290,
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
    )
    return fig


def create_atom_economy_pie(atom_economy: float):
    waste_percent = max(0, 100 - atom_economy)
    fig = go.Figure(
        data=[
            go.Pie(
                labels=["Utilized", "Waste"],
                values=[atom_economy, waste_percent],
                hole=0.55,
                marker={"colors": [MUTED_GREEN, SOFT_RED]},
                textposition="inside",
                texttemplate="<b>%{percent}</b>",
                textfont={"size": 28, "color": "#0a1628"},
            )
        ]
    )
    fig.update_layout(
        title={"text": "", "font": {"color": SCIENTIFIC_CYAN, "size": 1}, "x": 0.5, "xanchor": "center"},
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font={"color": TEXT_COLOR},
        height=320,
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        legend={"font": {"size": 15, "color": TEXT_COLOR}},
    )
    return fig


def create_efficiency_radar(atom_economy: float, e_factor: float, principles_count: int, score: float):
    ef_normalized = max(0, 100 - (e_factor * 10))
    principles_score = (principles_count / 12) * 100
    categories = ["Atom Economy", "Low E-Factor", "Principles", "Overall"]
    values = [atom_economy, ef_normalized, principles_score, score]
    fig = go.Figure(data=[go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(102,255,153,0.20)",
        line={"color": MUTED_GREEN, "width": 3},
    )])
    fig.update_layout(
        polar={
            "bgcolor": "rgba(10,22,40,0.9)",
            "radialaxis": {"visible": True, "range": [0, 100], "gridcolor": "rgba(0,229,255,0.35)", "tickfont": {"size": 13}},
            "angularaxis": {"gridcolor": "rgba(0,229,255,0.25)", "tickfont": {"size": 14, "color": TEXT_COLOR}},
        },
        title={"text": "", "font": {"color": SCIENTIFIC_CYAN, "size": 1}, "x": 0.5, "xanchor": "center"},
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font={"color": TEXT_COLOR},
        height=320,
        margin={"l": 30, "r": 30, "t": 20, "b": 25},
    )
    return fig


def create_comparison_bar_chart(chart_data):
    categories = chart_data["categories"]
    r1 = chart_data["reaction_1"]
    r2 = chart_data["reaction_2"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=categories, y=r1["values"], name=r1["label"], marker_color="#00c4ff"))
    fig.add_trace(go.Bar(x=categories, y=r2["values"], name=r2["label"], marker_color=MUTED_GREEN))
    fig.update_layout(
        barmode="group",
        title={"text": "Reaction Comparison", "font": {"color": SCIENTIFIC_CYAN, "size": 22}, "x": 0.5, "xanchor": "center"},
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font={"color": TEXT_COLOR},
        height=500,
        margin={"l": 20, "r": 20, "t": 65, "b": 20},
    )
    return fig


def create_trend_analysis_chart(
    calculate_atom_economy_fn,
    calculate_e_factor_fn,
    calculate_sustainability_score_fn,
    mw_reactants: float,
    mw_product: float,
    mass_product: float,
    principles_count: int,
    solvent_penalty: float,
):
    base_waste = max(0.1, mass_product * 0.6)
    waste_values = [base_waste * ratio for ratio in [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]]
    atom_economy = calculate_atom_economy_fn(mw_product, mw_reactants)

    records = []
    for waste in waste_values:
        ef = calculate_e_factor_fn(waste, mass_product)
        score = calculate_sustainability_score_fn(atom_economy, ef, principles_count, solvent_penalty)
        records.append({"Waste Mass (kg)": waste, "E-Factor": ef, "Sustainability Score": score})
    df = pd.DataFrame(records)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Waste Mass (kg)"], y=df["E-Factor"], mode="lines+markers", name="E-Factor", line={"color": SOFT_RED}))
    fig.add_trace(
        go.Scatter(
            x=df["Waste Mass (kg)"],
            y=df["Sustainability Score"],
            mode="lines+markers",
            name="Sustainability Score",
            yaxis="y2",
            line={"color": MUTED_GREEN},
        )
    )
    fig.update_layout(
        title={"text": "Trend Analysis: Waste vs Sustainability", "font": {"color": SCIENTIFIC_CYAN, "size": 22}, "x": 0.5, "xanchor": "center"},
        paper_bgcolor=DARK_BG,
        plot_bgcolor=DARK_BG,
        font={"color": TEXT_COLOR},
        yaxis={"title": "E-Factor"},
        yaxis2={"title": "Sustainability Score", "overlaying": "y", "side": "right", "range": [0, 100]},
        height=500,
        margin={"l": 15, "r": 60, "t": 65, "b": 20},
    )
    return fig
