"""Machine-learning utilities for reaction sustainability scoring.

This module provides:
1) Synthetic dataset generation
2) Model training (Random Forest by default)
3) Model persistence with joblib
4) Prediction helpers for new samples
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# ------------------------------- Paths ------------------------------------ #

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"

DATASET_PATH = DATA_DIR / "reaction_sustainability_data.csv"
MODEL_PATH = MODEL_DIR / "sustainability_model.joblib"


# --------------------------- Data generation ------------------------------- #

REACTION_CONFIG = {
    "Esterification": {"mw_reactants": (120, 280), "yield": (68, 92), "atom_economy": (60, 90)},
    "Amidation": {"mw_reactants": (130, 320), "yield": (65, 88), "atom_economy": (58, 86)},
    "Hydrogenation": {"mw_reactants": (90, 260), "yield": (75, 97), "atom_economy": (70, 97)},
    "Oxidation": {"mw_reactants": (110, 300), "yield": (55, 85), "atom_economy": (45, 80)},
    "Reduction": {"mw_reactants": (95, 280), "yield": (60, 90), "atom_economy": (50, 88)},
    "Suzuki Coupling": {"mw_reactants": (200, 520), "yield": (50, 86), "atom_economy": (35, 78)},
    "Nitration": {"mw_reactants": (80, 210), "yield": (58, 84), "atom_economy": (42, 75)},
    "Friedel-Crafts": {"mw_reactants": (140, 360), "yield": (45, 80), "atom_economy": (30, 70)},
}

SOLVENT_PROFILE = {
    "Water": {"waste_factor": 0.85, "green_bonus": 7.0},
    "Ethanol": {"waste_factor": 0.9, "green_bonus": 5.0},
    "Acetone": {"waste_factor": 1.0, "green_bonus": 2.0},
    "Ethyl Acetate": {"waste_factor": 0.95, "green_bonus": 4.0},
    "Toluene": {"waste_factor": 1.15, "green_bonus": -3.0},
    "DMF": {"waste_factor": 1.25, "green_bonus": -6.0},
    "DMSO": {"waste_factor": 1.1, "green_bonus": -2.0},
    "Hexane": {"waste_factor": 1.3, "green_bonus": -7.0},
}


def _calculate_sustainability_score(
    yield_pct: float,
    e_factor: float,
    atom_economy: float,
    waste_mass: float,
    solvent_bonus: float,
    rng: np.random.Generator,
) -> float:
    """Construct a realistic sustainability score in [0, 100]."""
    score = (
        0.40 * yield_pct
        + 0.35 * atom_economy
        - 8.0 * np.log1p(e_factor)
        - 0.02 * waste_mass
        + solvent_bonus
        + rng.normal(0.0, 2.8)
    )
    return float(np.clip(score, 0.0, 100.0))


def generate_synthetic_dataset(n_samples: int = 300, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic reaction sustainability dataset."""
    if not (200 <= n_samples <= 500):
        raise ValueError("n_samples must be between 200 and 500.")

    rng = np.random.default_rng(seed)
    reactions = list(REACTION_CONFIG.keys())
    solvents = list(SOLVENT_PROFILE.keys())

    rows: List[Dict[str, Any]] = []
    for _ in range(n_samples):
        reaction_name = str(rng.choice(reactions))
        solvent = str(rng.choice(solvents))

        cfg = REACTION_CONFIG[reaction_name]
        solv = SOLVENT_PROFILE[solvent]

        mw_reactants = float(rng.uniform(*cfg["mw_reactants"]))
        yield_pct = float(rng.uniform(*cfg["yield"]))
        atom_economy = float(rng.uniform(*cfg["atom_economy"]))

        conversion = np.clip(yield_pct / 100.0 + rng.normal(0.0, 0.02), 0.35, 0.99)
        mw_product = float(mw_reactants * conversion * rng.uniform(0.85, 1.02))

        base_waste = max(mw_reactants - mw_product, 3.0)
        process_waste = rng.uniform(5.0, 35.0)
        waste_mass = float((base_waste + process_waste) * solv["waste_factor"])

        # Common E-factor range in fine chemicals/pharma contexts can be broad.
        product_mass_ref = max(mw_product * rng.uniform(0.7, 1.3), 10.0)
        e_factor = float(np.clip(waste_mass / product_mass_ref, 0.1, 20.0))

        sustainability_score = _calculate_sustainability_score(
            yield_pct=yield_pct,
            e_factor=e_factor,
            atom_economy=atom_economy,
            waste_mass=waste_mass,
            solvent_bonus=solv["green_bonus"],
            rng=rng,
        )

        rows.append(
            {
                "reaction_name": reaction_name,
                "mw_reactants": round(mw_reactants, 2),
                "mw_product": round(mw_product, 2),
                "solvent": solvent,
                "waste_mass": round(waste_mass, 2),
                "yield": round(yield_pct, 2),
                "e_factor": round(e_factor, 3),
                "atom_economy": round(atom_economy, 2),
                "sustainability_score": round(sustainability_score, 2),
            }
        )

    return pd.DataFrame(rows)


def _score_to_grade(scores: Union[pd.Series, np.ndarray]) -> np.ndarray:
    """Map numerical scores to A/B/C labels."""
    values = np.asarray(scores)
    return np.where(values >= 80, "A", np.where(values >= 60, "B", "C"))


# ------------------------------- Training --------------------------------- #

def train_model(
    n_samples: int = 300,
    dataset_path: Union[str, Path] = DATASET_PATH,
    model_path: Union[str, Path] = MODEL_PATH,
    random_state: int = 42,
    use_classifier: bool = True,
) -> Dict[str, float]:
    """Generate data, train model(s), and persist artifacts.

    Returns training diagnostics for quick inspection.
    """
    dataset_path = Path(dataset_path)
    model_path = Path(model_path)

    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.parent.mkdir(parents=True, exist_ok=True)

    df = generate_synthetic_dataset(n_samples=n_samples, seed=random_state)
    df.to_csv(dataset_path, index=False)

    feature_cols = [
        "reaction_name",
        "mw_reactants",
        "mw_product",
        "solvent",
        "waste_mass",
        "yield",
        "e_factor",
        "atom_economy",
    ]
    target_col = "sustainability_score"

    X = df[feature_cols].copy()
    y = df[target_col].copy()
    y_grade = _score_to_grade(y)

    categorical_cols = ["reaction_name", "solvent"]
    numeric_cols = [col for col in feature_cols if col not in categorical_cols]

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
            ("num", "passthrough", numeric_cols),
        ]
    )

    X_train, X_test, y_train, y_test, y_grade_train, y_grade_test = train_test_split(
        X, y, y_grade, test_size=0.2, random_state=random_state
    )

    regressor = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=300,
                    random_state=random_state,
                    min_samples_leaf=2,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    regressor.fit(X_train, y_train)

    y_pred = regressor.predict(X_test)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    classifier = None
    grade_acc = None
    if use_classifier:
        classifier = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=250,
                        random_state=random_state,
                        min_samples_leaf=2,
                        n_jobs=-1,
                    ),
                ),
            ]
        )
        classifier.fit(X_train, y_grade_train)
        grade_acc = float((classifier.predict(X_test) == y_grade_test).mean())

    artifact = {
        "regressor": regressor,
        "classifier": classifier,
        "feature_cols": feature_cols,
        "target_col": target_col,
    }
    joblib.dump(artifact, model_path)

    metrics = {"rmse": rmse, "r2": r2, "n_samples": float(len(df))}
    if grade_acc is not None:
        metrics["grade_accuracy"] = grade_acc
    return metrics


# ------------------------------ Inference --------------------------------- #

def predict(
    input_data: Union[Dict[str, Any], List[Dict[str, Any]], pd.DataFrame],
    model_path: Union[str, Path] = MODEL_PATH,
) -> List[Dict[str, Any]]:
    """Predict sustainability score (and optional grade) for input records.

    Expected input fields:
    - reaction_name
    - mw_reactants
    - mw_product
    - solvent
    - waste_mass
    - yield
    - e_factor
    - atom_economy
    """
    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found at {model_path}. Run train_model() first."
        )

    artifact = joblib.load(model_path)
    regressor: Pipeline = artifact["regressor"]
    classifier: Union[Pipeline, None] = artifact.get("classifier")
    feature_cols: List[str] = artifact["feature_cols"]

    if isinstance(input_data, pd.DataFrame):
        X_new = input_data.copy()
    elif isinstance(input_data, dict):
        X_new = pd.DataFrame([input_data])
    else:
        X_new = pd.DataFrame(input_data)

    missing = [col for col in feature_cols if col not in X_new.columns]
    if missing:
        raise ValueError(f"Missing required input fields: {missing}")

    X_new = X_new[feature_cols]
    score_pred = np.clip(regressor.predict(X_new), 0.0, 100.0)

    if classifier is not None:
        grade_pred = classifier.predict(X_new)
    else:
        grade_pred = _score_to_grade(score_pred)

    output: List[Dict[str, Any]] = []
    for score, grade in zip(score_pred, grade_pred):
        output.append(
            {
                "predicted_sustainability_score": round(float(score), 2),
                "predicted_grade": str(grade),
            }
        )
    return output


if __name__ == "__main__":
    results = train_model(n_samples=300)
    print("Training complete.")
    print(f"Saved dataset: {DATASET_PATH}")
    print(f"Saved model:   {MODEL_PATH}")
    print("Metrics:", results)
