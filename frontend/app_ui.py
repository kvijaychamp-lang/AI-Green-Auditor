"""Main Streamlit page assembly for Green Synth AI."""

from __future__ import annotations

import streamlit as st

from frontend.charts import (
    create_atom_economy_pie,
    create_comparison_bar_chart,
    create_e_factor_gauge,
    create_efficiency_radar,
    create_trend_analysis_chart,
)
from frontend.components import (
    render_error_state,
    render_grade_badge,
    render_numeric_summary,
    render_recommendations,
    render_waiting_state,
    render_warning_state,
)
from frontend.theme import inject_custom_css
from services.chemistry import (
    GREEN_PRINCIPLES,
    SOLVENT_LIST,
    TOXIC_SOLVENTS,
    calculate_atom_economy,
    calculate_co2_impact,
    calculate_e_factor,
    calculate_sustainability_score,
    calculate_toxicity_score,
    calculate_waste_prevented,
    check_mass_balance,
    get_sustainability_grade,
    validate_scientific_constraints,
)
from services.comparator import compare_reactions
from services.nlp_parser import parse_text
from services.pdf_report import generate_pdf_report
from services.recommender import get_recommendations


def render_dashboard_heading(st, text: str) -> None:
    """Render a consistent tech-dashboard section heading."""
    st.markdown(
        f"<div class='dashboard-heading'>{text}</div><div class='dashboard-heading-underline'></div>",
        unsafe_allow_html=True,
    )


def render_main_page() -> None:
    """Render the full application UI."""
    st.set_page_config(page_title="AI Green Auditor", page_icon="🌿", layout="wide", initial_sidebar_state="collapsed")
    inject_custom_css(st)
    st.markdown('<h1 class="main-title">🌿 AI Green Auditor</h1>', unsafe_allow_html=True)

    st.markdown("<div class='section-heading'>AI-Powered Reaction Parser</div>", unsafe_allow_html=True)
    with st.expander("NLP Quick Input", expanded=False):
        raw_text = st.text_area("Describe your reaction", placeholder="Grignard reaction using ether solvent with waste 10kg")
        if st.button("Parse Text"):
            result = parse_text(raw_text)
            st.session_state["nlp_result"] = result

            if result.get("success"):
                # Store last-known-good parse to support safe fallback.
                st.session_state["last_good_nlp_parse"] = result["parsed_data"]

                parsed = result["parsed_data"]
                # Update ALL relevant UI keys so widgets update instantly.
                if parsed.get("reaction_name"):
                    st.session_state["reaction_name"] = parsed["reaction_name"]
                if parsed.get("solvent") in SOLVENT_LIST:
                    st.session_state["solvent"] = parsed["solvent"]

                # MW inputs
                if parsed.get("mw_reactants_g_mol") and float(parsed.get("mw_reactants_g_mol", 0)) > 0:
                    st.session_state["mw_reactants"] = float(parsed["mw_reactants_g_mol"])
                if parsed.get("mw_product_g_mol") and float(parsed.get("mw_product_g_mol", 0)) > 0:
                    st.session_state["mw_product"] = float(parsed["mw_product_g_mol"])

                # Mass inputs (dependency-parsing strategy ensures these are properly assigned)
                if parsed.get("reactant_mass_kg") and float(parsed.get("reactant_mass_kg", 0)) > 0:
                    st.session_state["mass_reactant"] = float(parsed["reactant_mass_kg"])
                if parsed.get("product_mass_kg") and float(parsed.get("product_mass_kg", 0)) > 0:
                    st.session_state["mass_product"] = float(parsed["product_mass_kg"])
                if parsed.get("waste_mass_kg") and float(parsed.get("waste_mass_kg", 0)) > 0:
                    st.session_state["mass_waste"] = float(parsed["waste_mass_kg"])

                # CRITICAL: Force all components to update on successful parse
                # The requires_rerun flag indicates parser completed successfully with new extraction logic
                if result.get("requires_rerun"):
                    st.rerun()
            else:
                st.warning("Could not parse clearly, please adjust sliders manually.")
        if st.session_state.get("nlp_result"):
            parsed = st.session_state["nlp_result"]["parsed_data"]
            st.json(st.session_state["nlp_result"])
            if st.button("Use Parsed Values"):
                if parsed.get("reaction_name"):
                    st.session_state["reaction_name"] = parsed["reaction_name"]
                if parsed.get("solvent") in SOLVENT_LIST:
                    st.session_state["solvent"] = parsed["solvent"]
                if parsed.get("reactant_mass_kg") and float(parsed.get("reactant_mass_kg", 0)) > 0:
                    st.session_state["mass_reactant"] = float(parsed["reactant_mass_kg"])
                if parsed.get("product_mass_kg") and float(parsed.get("product_mass_kg", 0)) > 0:
                    st.session_state["mass_product"] = float(parsed["product_mass_kg"])
                if parsed.get("waste_mass_kg") and float(parsed.get("waste_mass_kg", 0)) > 0:
                    st.session_state["mass_waste"] = float(parsed["waste_mass_kg"])
                st.rerun()

    st.markdown("<div class='section-heading'>Reaction Data Input</div>", unsafe_allow_html=True)
    reaction_name = st.text_input("Name of the Reaction", key="reaction_name")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        mw_reactants = st.number_input("MW Reactants (g/mol)", min_value=0.0, value=0.0, key="mw_reactants")
    with c2:
        mw_product = st.number_input("MW Product (g/mol)", min_value=0.0, value=0.0, key="mw_product")
    with c3:
        mass_product = st.number_input("Mass Product (kg)", min_value=0.0, value=0.0, step=0.1, key="mass_product")
    with c4:
        mass_waste = st.number_input("Mass Waste (kg)", min_value=0.0, value=0.0, step=0.1, key="mass_waste")

    solvent = st.selectbox("Select Solvent", SOLVENT_LIST, key="solvent")
    solvent_penalty = 15 if solvent in TOXIC_SOLVENTS else 0

    with st.expander("Select Applied Green Chemistry Principles", expanded=False):
        selected = []
        cols = st.columns(3)
        for idx, (principle, description) in enumerate(GREEN_PRINCIPLES.items()):
            with cols[idx % 3]:
                if st.checkbox(principle, key=f"principle_{idx}", help=description):
                    selected.append(principle)
    principles_count = len(selected)

    if not (mw_reactants > 0 and mw_product > 0 and mass_product > 0):
        render_waiting_state(st)
        return

    is_valid, errors = validate_scientific_constraints(mw_reactants, mw_product, mass_product, mass_waste)
    if not is_valid:
        render_error_state(st, errors)
        return

    warn, warning_message = check_mass_balance(mass_product, mass_waste, mw_reactants, mw_product)
    if warn:
        render_warning_state(st, warning_message)

    atom_economy = calculate_atom_economy(mw_product, mw_reactants)
    e_factor = calculate_e_factor(mass_waste, mass_product)
    score = calculate_sustainability_score(atom_economy, e_factor, principles_count, solvent_penalty)
    grade = get_sustainability_grade(score)
    waste_prevented = calculate_waste_prevented(mass_waste, e_factor)
    co2_impact = calculate_co2_impact(mass_waste)
    toxicity_level, toxicity_desc = calculate_toxicity_score(solvent, principles_count)

    st.markdown("<div class='section-heading'>Core Analytics</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='analytics-title'>E-Factor</div>", unsafe_allow_html=True)
        st.plotly_chart(create_e_factor_gauge(e_factor), use_container_width=True)
    with c2:
        st.markdown("<div class='analytics-title'>Atom Economy</div>", unsafe_allow_html=True)
        st.plotly_chart(create_atom_economy_pie(atom_economy), use_container_width=True)
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("<div class='analytics-title'>Efficiency Metrics</div>", unsafe_allow_html=True)
        st.plotly_chart(create_efficiency_radar(atom_economy, e_factor, principles_count, score), use_container_width=True)
    with c4:
        st.markdown("<div class='grade-title'>Sustainability Grade</div>", unsafe_allow_html=True)
        render_grade_badge(st, grade)
        st.markdown(f"<div class='grade-score'>Score: {score:.1f}/100</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-heading'>Sustainability Impact</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-card impact-card'>", unsafe_allow_html=True)
    render_numeric_summary(st, waste_prevented, co2_impact, toxicity_level, toxicity_desc)
    st.markdown("</div>", unsafe_allow_html=True)

    predictions = {"predicted_sustainability_score": score, "predicted_grade": grade}
    recommendations = get_recommendations(
        {
            "reaction_name": reaction_name,
            "solvent": solvent,
            "atom_economy": atom_economy,
            "e_factor": e_factor,
            "waste_mass": mass_waste,
            "yield": (mw_product / mw_reactants) * 100 if mw_reactants else 0,
        },
        predictions,
    )
    st.markdown("<div class='section-card recommendation-card'>", unsafe_allow_html=True)
    render_recommendations(st, recommendations)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-heading'>Trend Analysis</div>", unsafe_allow_html=True)
    st.plotly_chart(
        create_trend_analysis_chart(
            calculate_atom_economy,
            calculate_e_factor,
            calculate_sustainability_score,
            mw_reactants,
            mw_product,
            mass_product,
            principles_count,
            solvent_penalty,
        ),
        use_container_width=True,
    )

    st.markdown("<div class='section-heading'>Comparative Benchmarking</div>", unsafe_allow_html=True)

    # Professional Benchmarking UI: Reaction 1 vs Reaction 2 side-by-side.
    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("#### Reaction 1 (Current)")
        r1_name = (st.session_state.get("reaction_name") or reaction_name or "Current Reaction").strip()
        st.text_input("Name", value=r1_name, disabled=True, key="cmp_r1_name_display")
        st.metric("E-Factor", f"{e_factor:.3f}")
        st.metric("Atom Economy (%)", f"{atom_economy:.2f}")
        st.metric("Sustainability Score", f"{score:.2f}")

    with right:
        st.markdown("#### Reaction 2 (Baseline / Alternative)")
        r2_name = st.text_input("Name", value="Traditional Baseline", key="cmp_r2_name")
        c1, c2, c3 = st.columns(3)
        with c1:
            r2_ef = st.number_input("E-Factor", min_value=0.0, value=max(0.0, float(e_factor)), step=0.1, key="cmp_r2_ef")
        with c2:
            r2_ae = st.number_input(
                "Atom Economy (%)",
                min_value=0.0,
                max_value=100.0,
                value=min(100.0, float(atom_economy)),
                step=0.5,
                key="cmp_r2_ae",
            )
        with c3:
            r2_score = st.number_input(
                "Sustainability Score",
                min_value=0.0,
                max_value=100.0,
                value=min(100.0, float(score)),
                step=0.5,
                key="cmp_r2_score",
            )

    # --- Visual feedback / benchmarking card ---
    score_gain = float(r2_score) - float(score)

    points_r1 = 0
    points_r2 = 0
    points_r2 += 1 if r2_ef < e_factor else 0
    points_r1 += 1 if e_factor < r2_ef else 0
    points_r2 += 1 if r2_ae > atom_economy else 0
    points_r1 += 1 if atom_economy > r2_ae else 0
    points_r2 += 1 if r2_score > score else 0
    points_r1 += 1 if score > r2_score else 0

    if points_r2 > points_r1:
        winner = r2_name or "Reaction 2"
        loser = r1_name or "Reaction 1"
    elif points_r1 > points_r2:
        winner = r1_name or "Reaction 1"
        loser = r2_name or "Reaction 2"
    else:
        winner = "Tie"
        loser = ""

    green_improvement_index = 0.0
    if float(score) > 0:
        green_improvement_index = (float(r2_score) - float(score)) / float(score) * 100.0

    with st.container():
        st.markdown("<div class='comparison-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-heading'>Benchmark Summary</div>", unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric(
                "E-Factor (Reaction 2 vs Reaction 1)",
                f"{float(r2_ef):.3f}",
                delta=f"{(float(r2_ef) - float(e_factor)):+.3f}",
                delta_color="inverse",
            )
        with m2:
            st.metric(
                "Sustainability Score (Reaction 2 vs Reaction 1)",
                f"{float(r2_score):.2f}",
                delta=f"{score_gain:+.2f}",
                delta_color="normal",
            )
        with m3:
            st.metric(
                "Green Improvement Index",
                f"{green_improvement_index:+.1f}%",
            )

        if winner == "Tie":
            st.info("Verdict: Both reactions are closely matched across the selected metrics.")
        else:
            st.success(f"Verdict: **{winner}** wins over **{loser}**.")
            st.markdown(
                f"**{winner}** is **{abs(green_improvement_index):.1f}%** "
                f"{'more' if green_improvement_index >= 0 else 'less'} sustainable than **{loser}** (score-based index)."
            )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-heading'>Export Report</div>", unsafe_allow_html=True)
    report_data = {
        "reaction_name": reaction_name or "Unnamed Reaction",
        "solvent": solvent,
        "atom_economy": atom_economy,
        "e_factor": e_factor,
        "score": score,
        "grade": grade,
        "waste_prevented": waste_prevented,
        "co2_impact": co2_impact,
        "recommendations": recommendations,
    }
    pdf_bytes = generate_pdf_report(report_data)
    st.download_button("Download Audit Report (PDF)", data=pdf_bytes, file_name="green_auditor_report.pdf", mime="application/pdf")
