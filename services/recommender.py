"""Hybrid recommendation engine for sustainability improvements.

Combines:
1) Rule-based heuristics from green chemistry metrics
2) Data-driven hints derived from historical dataset patterns
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from services.chemical_db import check_solvent

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "data" / "reaction_sustainability_data.csv"

def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_prediction(prediction: Any) -> Tuple[Optional[float], Optional[str]]:
    """Extract score and grade from flexible prediction payloads."""
    score = None
    grade = None

    if isinstance(prediction, list) and prediction:
        prediction = prediction[0]

    if isinstance(prediction, dict):
        score = prediction.get("predicted_sustainability_score")
        if score is None:
            score = prediction.get("sustainability_score")

        grade = prediction.get("predicted_grade") or prediction.get("grade")

    score_value = _to_float(score, default=-1.0)
    if score_value < 0:
        score_value = None
    return score_value, grade


def _dataset_insights(
    reaction_name: str,
    solvent: str,
    atom_economy: float,
    e_factor: float,
) -> Dict[str, Any]:
    """Compute data-driven recommendations from available dataset patterns."""
    insights: Dict[str, Any] = {
        "reaction_best_solvent": None,
        "reaction_top_atom_economy": None,
        "reaction_low_e_factor": None,
        "global_green_solvents": [],
    }
    if not DATASET_PATH.exists():
        return insights

    try:
        df = pd.read_csv(DATASET_PATH)
    except Exception:
        return insights

    required = {
        "reaction_name",
        "solvent",
        "e_factor",
        "atom_economy",
        "sustainability_score",
    }
    if not required.issubset(df.columns):
        return insights

    reaction_name = (reaction_name or "").strip()
    solvent = (solvent or "").strip()

    df_reaction = df[df["reaction_name"].astype(str).str.lower() == reaction_name.lower()]
    if not df_reaction.empty:
        by_solvent = (
            df_reaction.groupby("solvent", as_index=False)
            .agg(
                sustainability_score=("sustainability_score", "mean"),
                e_factor=("e_factor", "mean"),
                atom_economy=("atom_economy", "mean"),
                samples=("solvent", "count"),
            )
            .sort_values(["sustainability_score", "samples"], ascending=[False, False])
        )

        if not by_solvent.empty:
            best = by_solvent.iloc[0].to_dict()
            insights["reaction_best_solvent"] = best

            top_ae = by_solvent.sort_values("atom_economy", ascending=False).iloc[0].to_dict()
            insights["reaction_top_atom_economy"] = top_ae

            low_ef = by_solvent.sort_values("e_factor", ascending=True).iloc[0].to_dict()
            insights["reaction_low_e_factor"] = low_ef

    # Global solvent trend: high sustainability, low e-factor, decent sample count.
    solvent_stats = (
        df.groupby("solvent", as_index=False)
        .agg(
            sustainability_score=("sustainability_score", "mean"),
            e_factor=("e_factor", "mean"),
            atom_economy=("atom_economy", "mean"),
            samples=("solvent", "count"),
        )
        .sort_values("sustainability_score", ascending=False)
    )
    solvent_stats = solvent_stats[solvent_stats["samples"] >= 5]
    green = solvent_stats.sort_values(
        ["sustainability_score", "e_factor", "atom_economy"],
        ascending=[False, True, False],
    )
    insights["global_green_solvents"] = green.head(3).to_dict(orient="records")

    # Keep current sample-specific deltas for useful comparisons.
    if solvent and not df_reaction.empty:
        current = df_reaction[df_reaction["solvent"].astype(str).str.lower() == solvent.lower()]
        if not current.empty:
            current_mean_ef = float(current["e_factor"].mean())
            current_mean_ae = float(current["atom_economy"].mean())
            insights["current_solvent_baseline"] = {
                "e_factor": current_mean_ef,
                "atom_economy": current_mean_ae,
                "input_e_factor_delta": e_factor - current_mean_ef,
                "input_atom_economy_delta": atom_economy - current_mean_ae,
            }

    return insights


def get_recommendations(input_data: Dict[str, Any], prediction: Any) -> List[str]:
    """Return dynamic hybrid recommendations based on rules + dataset patterns."""
    reaction_name = str(input_data.get("reaction_name", "")).strip()
    solvent = str(input_data.get("solvent", "")).strip()

    atom_economy = _to_float(input_data.get("atom_economy"))
    e_factor = _to_float(input_data.get("e_factor"))
    waste_mass = _to_float(input_data.get("waste_mass"))
    yield_pct = _to_float(input_data.get("yield"))

    score, grade = _normalize_prediction(prediction)

    recommendations: List[str] = []
    seen = set()
    solvent_info = check_solvent(solvent)
    solvent_class = str(solvent_info.get("classification", "unknown")).lower()
    solvent_name = str(solvent_info.get("solvent") or solvent or "the selected solvent")

    def add(message: str) -> None:
        key = message.strip().lower()
        if key and key not in seen:
            seen.add(key)
            recommendations.append(message)

    # --------------------- Rule-based baseline ---------------------------- #
    if solvent_class == "hazardous":
        add(
            f"Hazardous solvent detected ({solvent_name}). Prioritize replacing it with greener "
            "alternatives such as water, ethanol, or ethyl acetate."
        )
        add("Add a solvent recovery loop (distillation/reuse) to immediately reduce solvent waste burden.")
    elif solvent_class == "moderate":
        add(
            f"{solvent_name} is classified as moderate risk. Evaluate whether a greener solvent can "
            "deliver similar performance."
        )
    elif solvent_class == "unknown":
        add(
            f"No solvent classification was found for '{solvent}'. Run an SDS-based hazard review before scale-up."
        )

    for warning in solvent_info.get("warnings", []):
        add(f"Solvent warning: {warning}")

    if e_factor >= 1.0:
        add(
            f"E-factor is elevated ({e_factor:.2f}). Focus on waste minimization, tighter stoichiometry, "
            "and solvent volume optimization."
        )
    elif e_factor >= 0.5:
        add(
            f"E-factor is moderate ({e_factor:.2f}). A process optimization pass could reduce waste by 10-20%."
        )

    if atom_economy < 60:
        add(
            f"Atom economy is low ({atom_economy:.1f}%). Consider route redesign to improve "
            "reactant incorporation into the final product."
        )
        add("Use catalytic pathways or one-pot transformations to reduce by-product formation.")
    elif atom_economy < 75:
        add(
            f"Atom economy is acceptable but improvable ({atom_economy:.1f}%). "
            "Review reagent excess and side-reaction suppression."
        )

    if waste_mass > 100:
        add(
            f"Waste mass is high ({waste_mass:.1f}). Evaluate in-process recycling and telescoping steps to cut waste."
        )

    if yield_pct < 70:
        add(
            f"Reaction yield is on the lower side ({yield_pct:.1f}%). Improving conversion/selectivity should improve "
            "both sustainability score and waste profile."
        )

    if score is not None:
        if score < 50:
            add(
                f"Predicted sustainability score is low ({score:.1f}). Prioritize solvent substitution and atom economy gains first."
            )
        elif score < 70:
            add(
                f"Predicted sustainability score is moderate ({score:.1f}). Incremental process optimization can move this toward Grade A."
            )

    if grade is not None and str(grade).upper() == "C":
        add("Grade C prediction indicates high improvement potential; start with the highest waste-generating unit operation.")

    # ----------------------- Data-driven layer ---------------------------- #
    insights = _dataset_insights(
        reaction_name=reaction_name,
        solvent=solvent,
        atom_economy=atom_economy,
        e_factor=e_factor,
    )

    best_solvent = insights.get("reaction_best_solvent")
    if best_solvent:
        best_name = str(best_solvent["solvent"])
        best_score = _to_float(best_solvent["sustainability_score"])
        if solvent and best_name.lower() != solvent.lower():
            add(
                f"For {reaction_name or 'this reaction type'}, dataset trends favor {best_name} "
                f"(avg score ~{best_score:.1f}) over {solvent}. Consider screening this solvent."
            )

    low_ef_solvent = insights.get("reaction_low_e_factor")
    if low_ef_solvent:
        low_ef_name = str(low_ef_solvent["solvent"])
        low_ef_value = _to_float(low_ef_solvent["e_factor"])
        if e_factor > low_ef_value + 0.15 and low_ef_name.lower() != solvent.lower():
            add(
                f"Dataset benchmark: {low_ef_name} shows lower average E-factor (~{low_ef_value:.2f}) "
                "for this reaction family. Use it as a waste-reduction trial condition."
            )

    top_ae_solvent = insights.get("reaction_top_atom_economy")
    if top_ae_solvent:
        top_ae_name = str(top_ae_solvent["solvent"])
        top_ae_value = _to_float(top_ae_solvent["atom_economy"])
        if atom_economy + 5 < top_ae_value and top_ae_name.lower() != solvent.lower():
            add(
                f"Atom-economy benchmark: {top_ae_name} reaches ~{top_ae_value:.1f}% in similar entries. "
                "Compare reagent ratios and conditions used with this solvent profile."
            )

    global_green = insights.get("global_green_solvents", [])
    if global_green and solvent_class == "hazardous":
        top_options = ", ".join(str(item["solvent"]) for item in global_green[:3])
        add(f"Globally greener solvents in your dataset are: {top_options}. Prioritize these in substitution experiments.")

    if not recommendations:
        add(
            "Current profile looks strong. Maintain solvent recovery, monitor E-factor per batch, and track atom economy drift."
        )

    return recommendations[:8]
