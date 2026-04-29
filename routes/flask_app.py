"""Optional Flask deployment entrypoint.

Provides parity endpoints with FastAPI:
- POST /api/predict
- POST /api/calculate
- POST /api/report
"""

from __future__ import annotations

import logging

from flask import Flask, jsonify, request, send_file

from models.ml_model import MODEL_PATH, predict as ml_predict
from services.pdf_report import generate_pdf_report

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def create_flask_app() -> Flask:
    app = Flask(__name__)

    @app.post("/api/predict")
    def predict_route():
        body = request.get_json(silent=True) or {}
        samples = body.get("samples", [])
        if not isinstance(samples, list) or not samples:
            return jsonify({"detail": "samples must be a non-empty list"}), 422
        try:
            predictions = ml_predict(samples, model_path=MODEL_PATH)
            logger.info("Flask generated %d prediction(s).", len(predictions))
            return jsonify({"predictions": predictions})
        except Exception as exc:
            logger.exception("Flask prediction error.")
            return jsonify({"detail": f"Prediction failed: {exc}"}), 500

    @app.post("/api/calculate")
    def calculate_route():
        body = request.get_json(silent=True) or {}
        mw_reactants = float(body.get("mw_reactants", 0))
        mw_product = float(body.get("mw_product", 0))
        mass_waste = float(body.get("mass_waste", 0))
        mass_product = float(body.get("mass_product", 0))

        if mw_reactants <= 0 or mw_product <= 0 or mass_product <= 0 or mass_waste < 0:
            return jsonify({"detail": "Invalid input values"}), 422
        if mw_product > mw_reactants:
            return jsonify({"detail": "mw_product cannot be greater than mw_reactants"}), 422

        atom_economy = (mw_product / mw_reactants) * 100
        e_factor = mass_waste / mass_product
        return jsonify({"atom_economy": round(atom_economy, 4), "e_factor": round(e_factor, 4)})

    @app.post("/api/report")
    def report_route():
        body = request.get_json(silent=True) or {}
        try:
            pdf_bytes = generate_pdf_report(body)
            logger.info("Flask generated PDF report.")
            from io import BytesIO

            return send_file(
                BytesIO(pdf_bytes),
                mimetype="application/pdf",
                as_attachment=True,
                download_name="green_auditor_report.pdf",
            )
        except Exception as exc:
            logger.exception("Flask report generation error.")
            return jsonify({"detail": f"Report generation failed: {exc}"}), 500

    return app


FLASK_APP = create_flask_app()


if __name__ == "__main__":
    FLASK_APP.run(host="0.0.0.0", port=5000, debug=False)
