"""Chemical solvent knowledge base and hazard classification utilities."""

from __future__ import annotations

from typing import Any, Dict, List

# Canonical solvent profiles. Extend as needed for project-specific chemistry.
SOLVENT_DB: Dict[str, Dict[str, Any]] = {
    "water": {
        "display_name": "Water",
        "classification": "green",
        "warnings": [],
    },
    "ethanol": {
        "display_name": "Ethanol",
        "classification": "green",
        "warnings": ["Flammable liquid; follow standard handling and storage controls."],
    },
    "ethyl acetate": {
        "display_name": "Ethyl Acetate",
        "classification": "green",
        "warnings": ["Flammable solvent; ensure ventilation and ignition control."],
    },
    "acetone": {
        "display_name": "Acetone",
        "classification": "moderate",
        "warnings": ["Highly flammable; monitor exposure and use proper ventilation."],
    },
    "methanol": {
        "display_name": "Methanol",
        "classification": "hazardous",
        "warnings": [
            "Toxic by ingestion, inhalation, and skin absorption.",
            "Use closed handling where possible and strict PPE controls.",
        ],
    },
    "dmso": {
        "display_name": "DMSO",
        "classification": "moderate",
        "warnings": [
            "Can enhance dermal absorption of dissolved compounds; avoid skin contact.",
        ],
    },
    "dmf": {
        "display_name": "DMF",
        "classification": "hazardous",
        "warnings": [
            "Reprotoxic risk and chronic exposure concern.",
            "Use enclosed systems and robust exposure monitoring.",
        ],
    },
    "dichloromethane": {
        "display_name": "Dichloromethane",
        "classification": "hazardous",
        "warnings": [
            "Volatile chlorinated solvent with inhalation hazard.",
            "Potential carcinogenic concern; prioritize substitution.",
        ],
    },
    "chloroform": {
        "display_name": "Chloroform",
        "classification": "hazardous",
        "warnings": [
            "Possible carcinogenicity and organ toxicity risk.",
            "Avoid use where safer alternatives exist.",
        ],
    },
    "benzene": {
        "display_name": "Benzene",
        "classification": "hazardous",
        "warnings": [
            "Known carcinogen; avoid use whenever possible.",
            "Requires strict occupational exposure controls.",
        ],
    },
    "hexane": {
        "display_name": "Hexane",
        "classification": "hazardous",
        "warnings": [
            "Neurotoxicity risk on prolonged exposure.",
            "High VOC contribution; consider lower-impact alternatives.",
        ],
    },
    "toluene": {
        "display_name": "Toluene",
        "classification": "hazardous",
        "warnings": [
            "Neurotoxic and reproductive risk at elevated exposure.",
            "Ensure engineering controls and solvent recovery.",
        ],
    },
}

# Aliases and common user-input variants.
SOLVENT_ALIASES = {
    "h2o": "water",
    "etoh": "ethanol",
    "ethylacetate": "ethyl acetate",
    "ea": "ethyl acetate",
    "dimethyl sulfoxide": "dmso",
    "dimethylformamide": "dmf",
    "methylene chloride": "dichloromethane",
    "dcm": "dichloromethane",
    "phh": "benzene",
}


def _normalize_name(solvent_name: str) -> str:
    key = (solvent_name or "").strip().lower()
    key = SOLVENT_ALIASES.get(key, key)
    return key


def check_solvent(solvent_name: str) -> Dict[str, Any]:
    """Return solvent safety classification and contextual warnings.

    Returns:
        {
            "solvent": <canonical display name or provided>,
            "classification": "green" | "moderate" | "hazardous" | "unknown",
            "warnings": [<warning strings>]
        }
    """
    normalized = _normalize_name(solvent_name)
    profile = SOLVENT_DB.get(normalized)

    if profile is None:
        warnings: List[str] = []
        if solvent_name:
            warnings.append(
                "Solvent not found in internal database; review SDS and classify manually."
            )
        return {
            "solvent": solvent_name,
            "classification": "unknown",
            "warnings": warnings,
        }

    return {
        "solvent": profile["display_name"],
        "classification": profile["classification"],
        "warnings": list(profile.get("warnings", [])),
    }
