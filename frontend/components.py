"""Reusable UI components."""

from __future__ import annotations

from frontend.theme import SCIENTIFIC_CYAN


def render_waiting_state(st) -> None:
    st.markdown('<div class="panel">Enter reaction data to begin analysis.</div>', unsafe_allow_html=True)


def render_error_state(st, errors) -> None:
    st.error("Input validation errors:\n- " + "\n- ".join(errors))


def render_warning_state(st, warning_message: str) -> None:
    st.warning(warning_message)

def render_dashboard_heading(st, text: str) -> None:
    """Render a consistent tech-dashboard section heading."""
    st.markdown(f"<div class='section-heading'>{text}</div>", unsafe_allow_html=True)


def render_grade_badge(st, grade: str) -> None:
    grade_class = "grade-A" if grade == "A" else "grade-B" if grade == "B" else "grade-C"
    st.markdown(
        f"<div class='grade-glow {grade_class}'>{grade}</div>",
        unsafe_allow_html=True,
    )


def render_recommendations(st, recommendations) -> None:
    st.markdown("<div class='section-heading'>AI Recommendations</div>", unsafe_allow_html=True)
    for rec in recommendations:
        st.markdown(f"- {rec}")


def render_numeric_summary(st, waste_prevented, co2_impact, toxicity_level, toxicity_desc) -> None:
    trees_equivalent = co2_impact / 20
    html = f"""
    <div class='impact-grid'>
        <div class='impact-item'>
            <div class='impact-item-title'>Waste Prevented</div>
            <div class='impact-item-value'>{waste_prevented:.2f} kg</div>
        </div>
        <div class='impact-item'>
            <div class='impact-item-title'>CO2 Released</div>
            <div class='impact-item-value'>{co2_impact:.2f} kg</div>
        </div>
        <div class='impact-item'>
            <div class='impact-item-title'>Trees Equivalent</div>
            <div class='impact-item-value'>{trees_equivalent:.1f}</div>
        </div>
        <div class='impact-item'>
            <div class='impact-item-title'>Toxicity</div>
            <div class='impact-item-value'>{toxicity_level}<br>{toxicity_desc}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
