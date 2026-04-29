"""HTTP API routes for ML prediction and green chemistry calculations."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

import joblib
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from models.ml_model import MODEL_PATH, predict as ml_predict
from services.pdf_report import generate_pdf_report

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

api_router = APIRouter(tags=["Sustainability API"])
_MODEL_ARTIFACT = None


class PredictionInput(BaseModel):
    reaction_name: str = Field(..., min_length=1)
    mw_reactants: float = Field(..., gt=0)
    mw_product: float = Field(..., gt=0)
    solvent: str = Field(..., min_length=1)
    waste_mass: float = Field(..., ge=0)
    yield_value: float = Field(..., alias="yield", ge=0, le=100)
    e_factor: float = Field(..., ge=0)
    atom_economy: float = Field(..., ge=0, le=100)

    def to_model_payload(self) -> Dict[str, float]:
        return {
            "reaction_name": self.reaction_name,
            "mw_reactants": self.mw_reactants,
            "mw_product": self.mw_product,
            "solvent": self.solvent,
            "waste_mass": self.waste_mass,
            "yield": self.yield_value,
            "e_factor": self.e_factor,
            "atom_economy": self.atom_economy,
        }


class PredictionRequest(BaseModel):
    samples: List[PredictionInput] = Field(..., min_items=1)


class CalculationRequest(BaseModel):
    mw_reactants: float = Field(..., gt=0)
    mw_product: float = Field(..., gt=0)
    mass_waste: float = Field(..., ge=0)
    mass_product: float = Field(..., gt=0)


class ReportRequest(BaseModel):
    reaction_name: str = "Unnamed Reaction"
    solvent: str = "N/A"
    atom_economy: float = 0.0
    e_factor: float = 0.0
    score: float = 0.0
    grade: str = "N/A"
    waste_prevented: float = 0.0
    co2_impact: float = 0.0
    recommendations: List[str] = Field(default_factory=list)


def _load_model() -> None:
    """Load model artifact once for readiness check and warm-up."""
    global _MODEL_ARTIFACT
    if _MODEL_ARTIFACT is not None:
        return

    model_file = Path(MODEL_PATH)
    if not model_file.exists():
        logger.error("Model artifact is missing at %s", model_file)
        raise FileNotFoundError(f"Model artifact not found at {model_file}")

    _MODEL_ARTIFACT = joblib.load(model_file)
    logger.info("Model artifact loaded from %s", model_file)


def _calculate_atom_economy(mw_product: float, mw_reactants: float) -> float:
    return (mw_product / mw_reactants) * 100 if mw_reactants else 0.0


def _calculate_e_factor(mass_waste: float, mass_product: float) -> float:
    return mass_waste / mass_product if mass_product else 0.0


@api_router.post("/predict")
def predict_sustainability(payload: PredictionRequest):
    """Predict sustainability score and grade from reaction input features."""
    try:
        _load_model()
    except FileNotFoundError as exc:
        logger.exception("Prediction failed: model unavailable.")
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Prediction failed during model loading.")
        raise HTTPException(status_code=500, detail="Failed to initialize model.") from exc

    try:
        records = [sample.to_model_payload() for sample in payload.samples]
        predictions = ml_predict(records, model_path=MODEL_PATH)
        logger.info("Generated %d prediction(s).", len(predictions))
        return {"predictions": predictions}
    except ValueError as exc:
        logger.warning("Prediction validation error: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unhandled error during prediction.")
        raise HTTPException(status_code=500, detail="Internal server error.") from exc


@api_router.post("/calculate")
def calculate_metrics(payload: CalculationRequest):
    """Calculate E-factor and atom economy from mass and molecular weights."""
    try:
        if payload.mw_product > payload.mw_reactants:
            raise HTTPException(
                status_code=422,
                detail="mw_product cannot be greater than mw_reactants.",
            )

        atom_economy = _calculate_atom_economy(
            mw_product=payload.mw_product,
            mw_reactants=payload.mw_reactants,
        )
        e_factor = _calculate_e_factor(
            mass_waste=payload.mass_waste,
            mass_product=payload.mass_product,
        )
        logger.info("Calculated metrics for one request.")
        return {
            "atom_economy": round(atom_economy, 4),
            "e_factor": round(e_factor, 4),
        }
    except HTTPException:
        logger.warning("Calculation request failed validation.")
        raise
    except Exception as exc:
        logger.exception("Unhandled error during metric calculation.")
        raise HTTPException(status_code=500, detail="Internal server error.") from exc


@api_router.post("/report")
def export_report(payload: ReportRequest):
    """Generate a PDF report and return bytes as downloadable content."""
    try:
        pdf_bytes = generate_pdf_report(payload.model_dump())
        logger.info("Generated PDF report for reaction '%s'.", payload.reaction_name)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=green_auditor_report.pdf"},
        )
    except Exception as exc:
        logger.exception("Unhandled error during report generation.")
        raise HTTPException(status_code=500, detail="Failed to generate report.") from exc
