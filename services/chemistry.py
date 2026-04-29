"""Core chemistry/business logic for sustainability analytics."""

from __future__ import annotations

from typing import Dict, List, Tuple

GREEN_PRINCIPLES: Dict[str, str] = {
    "Prevention": "Prevent waste rather than treat or clean up waste after it's created",
    "Atom Economy": "Design syntheses to maximize incorporation of all materials into final product",
    "Less Hazardous Synthesis": "Design syntheses to use substances with little or no toxicity",
    "Designing Safer Chemicals": "Design chemical products to be fully effective yet have minimal toxicity",
    "Safer Solvents": "Avoid using auxiliary substances or use safer ones when necessary",
    "Energy Efficiency": "Minimize energy requirements and conduct reactions at ambient conditions",
    "Renewable Feedstocks": "Use renewable raw materials and feedstocks whenever practicable",
    "Reduce Derivatives": "Minimize or avoid unnecessary derivatization to reduce waste",
    "Catalysis": "Use catalytic reagents rather than stoichiometric reagents",
    "Design for Degradation": "Design products to break down into innocuous substances after use",
    "Real-time Pollution Prevention": "Monitor and control processes in real-time to prevent pollution",
    "Safer Chemistry for Accident Prevention": "Minimize potential for accidents including explosions and fires",
}

SOLVENT_LIST: List[str] = [
    "None",
    "Water",
    "Ethanol",
    "Methanol",
    "Acetone",
    "Benzene",
    "Chloroform",
    "Dichloromethane",
    "Ethyl Acetate",
    "Hexane",
    "Toluene",
]

TOXIC_SOLVENTS = ["Benzene", "Chloroform"]


def validate_scientific_constraints(
    mw_reactants: float, mw_product: float, mass_product: float, mass_waste: float
) -> Tuple[bool, List[str]]:
    """Validate hard scientific constraints."""
    errors = []
    if mw_reactants == 0:
        errors.append("Error: Molecular Weight of Reactants cannot be zero.")
    if mass_product == 0:
        errors.append("Error: Mass of Product cannot be zero.")
    if mw_product > mw_reactants and mw_reactants > 0:
        errors.append("Theoretical Error: Product MW cannot exceed total reactant MW.")
    if mass_waste < 0:
        errors.append("Error: Waste mass cannot be negative.")
    return len(errors) == 0, errors


def check_mass_balance(
    mass_product: float, mass_waste: float, mw_reactants: float, mw_product: float
) -> Tuple[bool, str]:
    """Warn when conservation-style mass balance seems implausible."""
    if mass_product > 0 and mw_reactants > 0 and mw_product > 0:
        theoretical_reactant_mass = mass_product * (mw_reactants / mw_product)
        total_output = mass_product + mass_waste
        if total_output > theoretical_reactant_mass * 1.5:
            return True, "Scientific warning: output mass appears high vs theoretical input."
    return False, ""


def calculate_atom_economy(mw_product: float, mw_reactants: float) -> float:
    """Calculate atom economy percentage."""
    return 0.0 if mw_reactants == 0 else (mw_product / mw_reactants) * 100


def calculate_e_factor(mass_waste: float, mass_product: float) -> float:
    """Calculate E-factor."""
    return 0.0 if mass_product == 0 else mass_waste / mass_product


def calculate_sustainability_score(
    atom_economy: float, e_factor: float, principles_count: int, solvent_penalty: float = 0
) -> float:
    """Weighted sustainability score in range [0, 100]."""
    ae_score = min(atom_economy, 100)
    ef_normalized = max(0, 100 - (e_factor * 10))
    principles_score = (principles_count / 12) * 100
    total_score = (ae_score * 0.4) + (ef_normalized * 0.3) + (principles_score * 0.3)
    return max(0, total_score - solvent_penalty)


def get_sustainability_grade(score: float) -> str:
    """Convert score to letter grade."""
    if score >= 75:
        return "A"
    if score >= 50:
        return "B"
    return "C"


def calculate_waste_prevented(mass_waste: float, e_factor: float) -> float:
    """Estimate avoided waste versus legacy process baseline."""
    traditional_e_factor = 10
    if e_factor < traditional_e_factor:
        return max(0, mass_waste * (traditional_e_factor - e_factor) / traditional_e_factor)
    return 0


def calculate_co2_impact(mass_waste: float) -> float:
    """Approximate CO2 equivalent from waste handling."""
    return mass_waste * 2


def calculate_toxicity_score(solvent: str, principles_count: int) -> Tuple[str, str]:
    """Classify toxicity level using solvent and green-principle adoption."""
    if solvent in TOXIC_SOLVENTS:
        base_score = 80
    elif solvent in ["Water", "Ethanol", "None"]:
        base_score = 10
    else:
        base_score = 40
    toxicity_reduction = (principles_count / 12) * 30
    final_score = max(0, base_score - toxicity_reduction)
    if final_score < 25:
        return "Low", "Minimal Hazard"
    if final_score < 60:
        return "Moderate", "Caution Required"
    return "High", "Significant Hazard"
