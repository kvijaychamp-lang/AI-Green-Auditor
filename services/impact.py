"""Environmental impact calculation utilities with scale projections."""

from __future__ import annotations

from typing import Any, Dict


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_positive(value: float, minimum: float = 0.0) -> float:
    return value if value >= minimum else minimum


def calculate_impact(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate CO2 and environmental impact from process-level inputs.

    Expected input fields:
    - mass_waste (kg)
    - mass_product (kg)
    - e_factor
    - atom_economy (0-100)
    - energy_kwh (optional, process energy)
    - solvent_hazard_factor (optional, 0.0-2.0 typical)
    - transport_km (optional, logistics distance)
    - yearly_batches (optional, industrial scaling)
    - scale_multiplier (optional, industrial scaling)
    - baseline_e_factor (optional, for avoided-impact comparison)
    """
    mass_waste = _safe_positive(_to_float(input_data.get("mass_waste")))
    mass_product = _safe_positive(_to_float(input_data.get("mass_product")))
    e_factor = _safe_positive(_to_float(input_data.get("e_factor")))
    atom_economy = _to_float(input_data.get("atom_economy"), default=0.0)
    atom_economy = min(100.0, max(0.0, atom_economy))

    energy_kwh = _safe_positive(_to_float(input_data.get("energy_kwh")))
    transport_km = _safe_positive(_to_float(input_data.get("transport_km")))
    solvent_hazard_factor = _to_float(input_data.get("solvent_hazard_factor"), default=1.0)
    solvent_hazard_factor = min(3.0, max(0.1, solvent_hazard_factor))

    yearly_batches = max(1.0, _to_float(input_data.get("yearly_batches"), default=1.0))
    scale_multiplier = max(1.0, _to_float(input_data.get("scale_multiplier"), default=1.0))
    baseline_e_factor = max(e_factor, _to_float(input_data.get("baseline_e_factor"), default=max(2.0, e_factor)))

    # ------------------ Formula-driven emissions model ------------------ #
    # Emission factors are formula coefficients, not fixed impact constants.
    # They transform process inputs into a dynamic estimate.
    # Waste treatment CO2 intensity increases with E-factor and hazard profile.
    waste_treatment_factor = 1.3 + (0.12 * e_factor) + (0.35 * (solvent_hazard_factor - 1.0))
    waste_treatment_factor = max(0.6, waste_treatment_factor)

    # Energy intensity uses a grid-emission coefficient with mild efficiency effect.
    grid_emission_factor = 0.32 + (0.03 * min(e_factor, 5.0))
    energy_emissions = energy_kwh * grid_emission_factor

    # Transport emissions depend on product throughput and distance.
    throughput_mass = mass_waste + mass_product
    transport_emissions = (throughput_mass / 1000.0) * transport_km * 0.09

    waste_emissions = mass_waste * waste_treatment_factor
    co2_total_kg = waste_emissions + energy_emissions + transport_emissions

    # ---------------- Composite environmental impact index -------------- #
    # Lower is better. Components normalized to 0-100 style bands.
    waste_intensity = (mass_waste / max(mass_product, 1e-6))
    normalized_waste = min(100.0, waste_intensity * 12.0)
    normalized_emissions = min(100.0, co2_total_kg / max(mass_product, 1.0) * 8.0)
    normalized_efficiency_penalty = 100.0 - atom_economy
    normalized_hazard = min(100.0, (solvent_hazard_factor / 3.0) * 100.0)

    environmental_impact_index = (
        0.35 * normalized_waste
        + 0.30 * normalized_emissions
        + 0.20 * normalized_efficiency_penalty
        + 0.15 * normalized_hazard
    )
    environmental_impact_index = min(100.0, max(0.0, environmental_impact_index))

    # ------------------ Industrial-level scale projection ---------------- #
    projected_runs = yearly_batches * scale_multiplier
    annual_co2_kg = co2_total_kg * projected_runs

    # Compare against baseline process to estimate avoided impact potential.
    baseline_waste_mass = baseline_e_factor * max(mass_product, 0.0)
    baseline_waste_treatment_factor = 1.3 + (0.12 * baseline_e_factor) + (0.35 * (solvent_hazard_factor - 1.0))
    baseline_co2_kg = (
        baseline_waste_mass * max(0.6, baseline_waste_treatment_factor)
        + energy_emissions
        + transport_emissions
    )
    co2_avoided_per_run = max(0.0, baseline_co2_kg - co2_total_kg)
    annual_co2_avoided_kg = co2_avoided_per_run * projected_runs

    impact_band = (
        "low" if environmental_impact_index < 33
        else "moderate" if environmental_impact_index < 66
        else "high"
    )

    return {
        "inputs_used": {
            "mass_waste_kg": round(mass_waste, 4),
            "mass_product_kg": round(mass_product, 4),
            "e_factor": round(e_factor, 4),
            "atom_economy_pct": round(atom_economy, 4),
            "energy_kwh": round(energy_kwh, 4),
            "solvent_hazard_factor": round(solvent_hazard_factor, 4),
            "transport_km": round(transport_km, 4),
            "yearly_batches": round(yearly_batches, 4),
            "scale_multiplier": round(scale_multiplier, 4),
            "baseline_e_factor": round(baseline_e_factor, 4),
        },
        "co2_impact": {
            "waste_emissions_kg": round(waste_emissions, 4),
            "energy_emissions_kg": round(energy_emissions, 4),
            "transport_emissions_kg": round(transport_emissions, 4),
            "total_co2_kg_per_run": round(co2_total_kg, 4),
        },
        "environmental_impact": {
            "impact_index_0_to_100": round(environmental_impact_index, 4),
            "impact_band": impact_band,
            "normalized_components": {
                "waste_intensity": round(normalized_waste, 4),
                "emissions_intensity": round(normalized_emissions, 4),
                "efficiency_penalty": round(normalized_efficiency_penalty, 4),
                "hazard_factor": round(normalized_hazard, 4),
            },
        },
        "industrial_projection": {
            "projected_runs_per_year": round(projected_runs, 4),
            "annual_co2_kg": round(annual_co2_kg, 4),
            "annual_co2_tons": round(annual_co2_kg / 1000.0, 4),
            "co2_avoided_per_run_kg_vs_baseline": round(co2_avoided_per_run, 4),
            "annual_co2_avoided_kg_vs_baseline": round(annual_co2_avoided_kg, 4),
            "annual_co2_avoided_tons_vs_baseline": round(annual_co2_avoided_kg / 1000.0, 4),
        },
    }
