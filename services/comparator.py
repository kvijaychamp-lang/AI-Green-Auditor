"""Comparison utilities for evaluating two reaction profiles."""

from __future__ import annotations
from typing import Any, Dict, List

def _to_float(value: Any, default: float = 0.0) -> float:
    """Safely convert any value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def _reaction_label(data: Dict[str, Any], fallback: str) -> str:
    """Get the reaction name or use a fallback label."""
    name = str(data.get("reaction_name", "")).strip()
    return name if name else fallback

def compare_reactions(data1: Dict[str, Any], data2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to compare two reactions.
    Input: Dictionaries containing 'e_factor', 'atom_economy', 'sustainability_score'.
    """
    label1 = _reaction_label(data1, "Reaction 1")
    label2 = _reaction_label(data2, "Reaction 2")

    # Data extraction and cleaning
    ef1, ef2 = _to_float(data1.get("e_factor")), _to_float(data2.get("e_factor"))
    ae1, ae2 = _to_float(data1.get("atom_economy")), _to_float(data2.get("atom_economy"))
    s1, s2 = _to_float(data1.get("sustainability_score")), _to_float(data2.get("sustainability_score"))

    # Weighted Aggregate Score Logic (Higher is Better)
    # E-factor is inverted (100 - (ef * 10)) so that lower waste gives higher score
    ef_comp1 = max(0.0, 100.0 - (ef1 * 10.0))
    ef_comp2 = max(0.0, 100.0 - (ef2 * 10.0))
    
    # Sustainability Index (Weighted: 35% AE, 35% Score, 30% E-Factor)
    agg1 = (0.35 * ae1) + (0.35 * s1) + (0.30 * ef_comp1)
    agg2 = (0.35 * ae2) + (0.35 * s2) + (0.30 * ef_comp2)

    # Determine Winner
    if abs(agg1 - agg2) < 1e-6:
        overall_winner = "tie"
    else:
        overall_winner = "reaction_1" if agg1 > agg2 else "reaction_2"

    # Improvement index
    improvement_pct = ((agg1 - agg2) / agg2 * 100) if agg2 != 0 else 0.0
    diff_type = "more" if improvement_pct > 0 else "less"

    explanation = [
        f"{label1} is {abs(improvement_pct):.1f}% {diff_type} sustainable than {label2} (score-based index)."
    ]

    return {
        "reaction_labels": {"reaction_1": label1, "reaction_2": label2},
        "overall": {
            "winner": overall_winner,
            "better_reaction_name": label1 if overall_winner == "reaction_1" else label2,
            "aggregate_scores": {"r1": round(agg1, 2), "r2": round(agg2, 2)}
        },
        "explanation": explanation,
        "chart_data": {
            "categories": ["E-Factor", "Atom Economy", "Sustainability Score"],
            "r1": [round(ef1, 3), round(ae1, 2), round(s1, 2)],
            "r2": [round(ef2, 3), round(ae2, 2), round(s2, 2)]
        }
    }