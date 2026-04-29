"""Frontend theme constants and CSS helpers."""

DEEP_CYAN = "#00a3cc"
MUTED_GREEN = "#66ff99"
SOFT_RED = "#ff6666"
DARK_BG = "#0a1628"
TEXT_COLOR = "#e0e0e0"
SCIENTIFIC_CYAN = "#00e5ff"
GLOW_GREEN = "#66ff99"


def inject_custom_css(st) -> None:
    """Apply lightweight modern styling."""
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {DARK_BG};
            color: {TEXT_COLOR};
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        .main-title {{
            text-align: center;
            color: #1FBF8B !important;
            text-shadow: 0 0 12px rgba(31,191,139,0.85), 0 0 28px rgba(31,191,139,0.45);
            font-size: 2.6rem;
            font-weight: 700;
            margin-bottom: 1.2rem;
        }}
        .panel {{
            border: 1px solid {SCIENTIFIC_CYAN};
            border-radius: 10px;
            padding: 12px;
            background: rgba(10,22,40,0.45);
        }}
        .section-card {{
            border-radius: 12px;
            padding: 14px 16px;
            margin: 8px 0 12px 0;
            border: 1px solid rgba(255,255,255,0.15);
        }}
        .impact-card {{
            background: rgba(0, 200, 255, 0.10);
            border-color: rgba(0, 229, 255, 0.35);
        }}
        .recommendation-card {{
            background: rgba(102, 255, 153, 0.10);
            border-color: rgba(102, 255, 153, 0.35);
        }}
        .analytics-title {{
            text-align: center;
            color: {SCIENTIFIC_CYAN};
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 6px;
        }}
        .section-heading {{
            text-align: left;
            color: {GLOW_GREEN};
            font-size: 1.65rem;
            font-weight: 800;
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 14px 0 10px 0;
            text-shadow: none;
        }}
        .left-section-heading {{
            text-align: left;
            color: {SCIENTIFIC_CYAN};
            font-size: 1.35rem;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        .grade-title {{
            text-align: center;
            color: {SCIENTIFIC_CYAN};
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 6px;
        }}
        .grade-score {{
            text-align: center;
            color: {SCIENTIFIC_CYAN};
            font-size: 1.55rem;
            font-weight: 700;
            margin-top: 8px;
        }}
        .impact-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
        }}
        .impact-item {{
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 10px;
            padding: 10px 12px;
            background: rgba(10,22,40,0.35);
            min-height: 92px;
        }}
        .impact-item-title {{
            color: {SCIENTIFIC_CYAN};
            font-size: 1.35rem;
            font-weight: 800;
            margin-bottom: 6px;
        }}
        .impact-item-value {{
            color: {TEXT_COLOR};
            font-size: 1.15rem;
            font-weight: 600;
            line-height: 1.3;
        }}
        .grade-glow {{
            text-align:center;
            font-size:4.5rem;
            font-weight:800;
            border-radius:14px;
            width: 210px;
            margin: 0 auto;
            padding: 18px 10px;
            border: 2px solid transparent;
        }}
        .grade-A {{
            color: #66ff99;
            border-color: #66ff99;
            background: rgba(102,255,153,0.10);
            box-shadow: 0 0 16px rgba(102,255,153,0.7), 0 0 34px rgba(102,255,153,0.45);
        }}
        .grade-B {{
            color: #ffd966;
            border-color: #ffd966;
            background: rgba(255,217,102,0.10);
            box-shadow: 0 0 16px rgba(255,217,102,0.7), 0 0 34px rgba(255,217,102,0.45);
        }}
        .grade-C {{
            color: #ff6666;
            border-color: #ff6666;
            background: rgba(255,102,102,0.12);
            box-shadow: 0 0 16px rgba(255,102,102,0.7), 0 0 34px rgba(255,102,102,0.45);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
