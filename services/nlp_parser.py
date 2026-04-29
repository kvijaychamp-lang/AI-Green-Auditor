"""Robust NLP parser for extracting reaction context from plain text.

Goals:
- Extract reactant/product/waste masses using a simple (number + unit) regex
- Assign masses by order (1st=reactant, 2nd=product, 3rd=waste)
- Override order when explicit waste is mentioned (e.g. "waste is 10kg")
- If only reactant + product are present, infer waste = reactant - product
- Convert all masses to kg internally (supports kg, g, mg, tonne/ton)
- Fuzzy-match reaction/solvent names against known lists
- Provide a safe, non-crashing response for UI integration
"""

from __future__ import annotations

import difflib
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


KNOWN_REACTIONS = [
    "grignard reaction",
    "suzuki coupling",
    "friedel-crafts",
    "esterification",
    "amidation",
    "hydrogenation",
    "oxidation",
    "reduction",
    "nitration",
]

KNOWN_SOLVENTS = [
    "water",
    "ethanol",
    "methanol",
    "acetone",
    "ethyl acetate",
    "benzene",
    "chloroform",
    "dichloromethane",
    "dmf",
    "dmso",
    "thf",
    "tetrahydrofuran",
    "hexane",
    "toluene",
    "ether",
    "diethyl ether",
]

_WORD_RE = re.compile(r"[a-zA-Z]+(?:[-'][a-zA-Z]+)*")
_NUM_UNIT_RE = re.compile(
    r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>kg|kgs|kilogram|kilograms|g|gram|grams|mg|milligram|milligrams|ton|tons|tonne|tonnes)?\b",
    re.IGNORECASE,
)

# Basic number pattern (used for MW which often appears without mass units).
_NUM_RE = re.compile(r"(?P<value>\d+(?:\.\d+)?)")

# Like _NUM_UNIT_RE but avoids MW patterns such as "g/mol".
_MASS_VALUE_UNIT_RE = re.compile(
    r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>kg|kgs|kilogram|kilograms|g|gram|grams|mg|milligram|milligrams|ton|tons|tonne|tonnes)\b(?!\s*/\s*mol)",
    re.IGNORECASE,
)

# Waste MUST map to the number immediately following "waste" / "generated".
_WASTE_IMMEDIATE_RE = re.compile(
    r"\b(?:waste|generated)\b[^0-9]{0,18}(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>kg|kgs|kilogram|kilograms|g|gram|grams|mg|milligram|milligrams|ton|tons|tonne|tonnes)\b(?!\s*/\s*mol)",
    re.IGNORECASE,
)

# Common phrasing: "70kg of product", "100 kg of waste"
_OF_WASTE_RE = re.compile(
    r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>kg|kgs|kilogram|kilograms|g|gram|grams|mg|milligram|milligrams|ton|tons|tonne|tonnes)\s+of\s+waste\b",
    re.IGNORECASE,
)

# Keyword groups for disambiguating MW vs mass.
_MW_REACTANT_KEYWORDS = [
    "mw reactant",
    "mw reactants",
    "reactant mw",
    "reactants mw",
    "molecular weight of reactant",
    "molecular weight of reactants",
    "molecular weight reactant",
    "molecular weight reactants",
]
_MW_PRODUCT_KEYWORDS = [
    "mw product",
    "product mw",
    "molecular weight of product",
    "molecular weight product",
]
_MASS_REACTANT_KEYWORDS = [
    "started with",
    "start with",
    "initial",
    "reactant mass",
    "mass reactant",
    "reactant",
]
_MASS_PRODUCT_KEYWORDS = [
    "product mass",
    "mass product",
    "obtained",
    "yielded",
    "produced",
    "product",
]
_MASS_WASTE_KEYWORDS = [
    "waste mass",
    "mass waste",
    "generated waste",
    "waste",
    "generated",
    "gen",
    "byproduct",
    "by-product",
]

# Explicit waste patterns override order-based assignment.
_EXPLICIT_WASTE_RE = re.compile(
    r"\bwaste\b[^0-9]{0,16}(?:is|=|:)?\s*(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>kg|kgs|kilogram|kilograms|g|gram|grams|mg|milligram|milligrams|ton|tons|tonne|tonnes)?\b",
    re.IGNORECASE,
)

REACTANT_HINTS = {"start", "started", "input", "use", "used", "using", "reactant", "reactants", "charge", "charged", "feed"}
PRODUCT_HINTS = {"yield", "product", "produced", "obtain", "obtained", "result", "results", "gave", "gives", "output"}
WASTE_HINTS = {"waste", "loss", "lost", "byproduct", "by-product", "trash", "scrap"}


def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalize_unit(unit: Optional[str]) -> str:
    if not unit:
        return "kg"
    u = unit.strip().lower()
    if u in {"kg", "kgs", "kilogram", "kilograms"}:
        return "kg"
    if u in {"g", "gram", "grams"}:
        return "g"
    if u in {"mg", "milligram", "milligrams"}:
        return "mg"
    if u in {"ton", "tons", "tonne", "tonnes"}:
        return "ton"
    return "kg"


def _to_kg(value: float, unit: Optional[str]) -> float:
    u = _normalize_unit(unit)
    if u == "g":
        return value / 1000.0
    if u == "mg":
        return value / 1_000_000.0
    if u == "ton":
        return value * 1000.0
    return value


def _fuzzy_match(phrase: str, candidates: List[str], cutoff: float) -> Optional[str]:
    phrase = (phrase or "").strip().lower()
    if not phrase:
        return None
    matches = difflib.get_close_matches(phrase, candidates, n=1, cutoff=cutoff)
    return matches[0] if matches else None


def _extract_reaction_name(text: str) -> str:
    text_lc = text.lower()
    for r in sorted(KNOWN_REACTIONS, key=len, reverse=True):
        if r in text_lc:
            return r.title()

    # fuzzy across n-grams + "... reaction"
    m = re.search(r"\b([a-zA-Z][a-zA-Z\-\s]{2,40})\s+reaction\b", text_lc)
    if m:
        cand = _normalize_spaces(m.group(1) + " reaction")
        matched = _fuzzy_match(cand, KNOWN_REACTIONS, cutoff=0.72)
        return (matched or cand).title()

    words = [w for (w, _) in [(m.group(0).lower(), m.start()) for m in _WORD_RE.finditer(text)]]
    for n in (3, 2):
        for i in range(0, max(0, len(words) - n + 1)):
            cand = " ".join(words[i : i + n])
            matched = _fuzzy_match(cand, KNOWN_REACTIONS, cutoff=0.84)
            if matched:
                return matched.title()
    return ""


def _extract_solvent(text: str) -> str:
    text_lc = text.lower()

    # Prefer the app's canonical solvent list if available.
    candidates: List[str]
    try:
        from services.chemistry import SOLVENT_LIST as _SOLVENT_LIST  # type: ignore

        candidates = [str(s).strip().lower() for s in _SOLVENT_LIST if str(s).strip()]
    except Exception:
        candidates = [s.lower() for s in KNOWN_SOLVENTS]

    # Always include parser-known solvents too (e.g., THF) even if the UI list is shorter.
    candidates = list(sorted(set(candidates + [s.lower() for s in KNOWN_SOLVENTS])))

    for s in sorted(set(candidates), key=len, reverse=True):
        if re.search(rf"\b{re.escape(s)}\b", text_lc):
            if s in {"dmf", "dmso", "thf"}:
                return s.upper()
            return s.title()

    words = [m.group(0).lower() for m in _WORD_RE.finditer(text)]
    for n in (2, 1):
        for i in range(0, max(0, len(words) - n + 1)):
            cand = " ".join(words[i : i + n])
            matched = _fuzzy_match(cand, list(sorted(set(candidates))), cutoff=0.80)
            if matched:
                if matched in {"dmf", "dmso", "thf"}:
                    return matched.upper()
                return matched.title()
    return ""


def _extract_value_near_keywords(
    text: str,
    keywords: List[str],
    *,
    window_chars: int = 48,
    require_mass_unit: bool = False,
) -> Optional[Tuple[float, Optional[str]]]:
    """
    Find a numeric value near any of the provided keywords.

    - For MW: set require_mass_unit=False (we accept bare numbers, or numbers followed by g/mol).
    - For mass: set require_mass_unit=True (we prefer values that carry a mass unit).
    """
    text_lc = (text or "").lower()
    if not text_lc.strip():
        return None

    for kw in sorted({k.lower().strip() for k in keywords if k.strip()}, key=len, reverse=True):
        start = 0
        while True:
            idx = text_lc.find(kw, start)
            if idx < 0:
                break

            left = max(0, idx - window_chars)
            right = min(len(text), idx + len(kw) + window_chars)

            # Avoid slicing through a numeric token (e.g., cutting "100 kg" into "0 kg").
            while left > 0 and text[left].isdigit() and text[left - 1].isdigit():
                left -= 1
            while right < len(text) and text[right - 1].isdigit() and text[right].isdigit():
                right += 1

            # Prefer numbers that appear AFTER the keyword to avoid stealing unrelated numbers earlier in the sentence.
            snippet_after = text[idx : right]
            snippet_full = text[left:right]

            if require_mass_unit:
                # For very generic anchors (e.g., "reactant"), only look AFTER the keyword.
                # This avoids incorrectly grabbing product mass that happens to appear earlier.
                if kw in {"reactant", "reactants"}:
                    m = _MASS_VALUE_UNIT_RE.search(snippet_after)
                else:
                    m = _MASS_VALUE_UNIT_RE.search(snippet_after) or _MASS_VALUE_UNIT_RE.search(snippet_full)
                if m:
                    return float(m.group("value")), m.group("unit")
            else:
                # Prefer a number that looks like MW (optionally followed by g/mol).
                # Example: "MW Product: 180.16 g/mol" or "MW Reactant 92.1"
                m = re.search(
                    r"(?P<value>\d+(?:\.\d+)?)\s*(?:g\s*/\s*mol|g\/mol)?",
                    snippet_after,
                    re.IGNORECASE,
                ) or re.search(r"(?P<value>\d+(?:\.\d+)?)\s*(?:g\s*/\s*mol|g\/mol)?", snippet_full, re.IGNORECASE)
                if m:
                    return float(m.group("value")), None

            start = idx + len(kw)

    return None


def _extract_mw_and_masses(text: str) -> Dict[str, float]:
    """
    Extract MW (g/mol) and actual masses (kg) using dependency-parsing strategy.
    
    This is the main extraction entry point that combines:
    - Context windowing for each number
    - Priority matrix to assign values to correct fields
    - Bracket/colon handling for label continuity
    - Validation and inference rules
    
    Returns:
      {
        "mw_reactants_g_mol": float,
        "mw_product_g_mol": float,
        "product_mass_kg": float,
        "waste_mass_kg": float,
        "reactant_mass_kg": float,   # kept for backward compatibility/fallback
      }
    """
    # Use the new dependency-parsing strategy
    extracted = _dependency_parse_extraction(text)
    
    # Ensure all required keys are present with defaults
    result = {
        "mw_reactants_g_mol": float(extracted.get("mw_reactants_g_mol", 0.0)),
        "mw_product_g_mol": float(extracted.get("mw_product_g_mol", 0.0)),
        "reactant_mass_kg": float(extracted.get("reactant_mass_kg", 0.0)),
        "product_mass_kg": float(extracted.get("product_mass_kg", 0.0)),
        "waste_mass_kg": float(extracted.get("waste_mass_kg", 0.0)),
    }
    
    # Validation / sanity check: if waste >> product, warn (can indicate swapped anchors in the sentence).
    if result["waste_mass_kg"] > 0 and result["product_mass_kg"] > 0 and result["waste_mass_kg"] >= max(2.5 * result["product_mass_kg"], result["product_mass_kg"] + 50.0):
        logger.warning(
            "Parsed waste_mass (%.6f kg) much larger than product_mass (%.6f kg). "
            "Check if keywords were swapped in input: %r",
            result["waste_mass_kg"],
            result["product_mass_kg"],
            text[:240],
        )
    
    return result


def _extract_context_window(text: str, num_start: int, num_end: int, window_words: int = 3) -> List[str]:
    """
    Extract words before and after a number with context windowing.
    
    Args:
        text: Input text
        num_start: Start position of number
        num_end: End position of number
        window_words: Number of words to extract on each side
    
    Returns:
        List of words in context (before + after)
    """
    # Extract text before and after the number
    before_text = text[:num_start].strip()
    after_text = text[num_end:].strip()
    
    # Split into words
    before_words = _WORD_RE.findall(before_text)
    after_words = _WORD_RE.findall(after_text)
    
    # Get the last N words before and first N words after
    context_words = before_words[-window_words:] + after_words[:window_words]
    return [w.lower() for w in context_words]


def _check_keyword_proximity(context_words: List[str], keywords: List[str]) -> bool:
    """Check if any keyword is in the context window."""
    kw_set = {kw.lower() for kw in keywords}
    return any(w in kw_set for w in context_words)


def _dependency_parse_extraction(text: str) -> Dict[str, Any]:
    """
    Universal extraction logic using Dependency-Parsing strategy.
    
    Process:
    1. Data Cleaning: normalize input (lowercase, remove extra spaces)
    2. Context Windowing: find all numbers, look at 3 words before/after
    3. Priority Matrix: assign to mw_reactants, mw_product, mass_reactant, mass_product, mass_waste
    4. Bracket Handling: apply labels to subsequent numbers until next label
    5. Validation: infer missing reactant_mass as product_mass + waste_mass
    
    Returns:
        {
            "mw_reactants_g_mol": float,
            "mw_product_g_mol": float,
            "reactant_mass_kg": float,
            "product_mass_kg": float,
            "waste_mass_kg": float,
        }
    """
    # Step 1: Data Cleaning
    text_normalized = _normalize_spaces(text or "").lower()
    
    # Keyword groups for context checking
    mw_keywords = ["mw", "molecular", "weight", "g/mol", "g/mol"]
    reactant_keywords = ["reactant", "starting", "initial", "input", "charge"]
    product_keywords = ["product", "yield", "final", "obtained", "produced"]
    waste_keywords = ["waste", "byproduct", "loss", "gen", "generated"]
    mass_keywords = ["kg", "g", "mass", "weight"]
    
    # Track extracted values
    extracted = {
        "mw_reactants_g_mol": 0.0,
        "mw_product_g_mol": 0.0,
        "reactant_mass_kg": 0.0,
        "product_mass_kg": 0.0,
        "waste_mass_kg": 0.0,
    }
    
    # Store numbers with their context
    numbers_found = []
    
    # Step 2: Context Windowing - find all numbers
    for num_match in _NUM_RE.finditer(text_normalized):
        num_str = num_match.group("value")
        num_start = num_match.start()
        num_end = num_match.end()
        
        try:
            num_value = float(num_str)
        except ValueError:
            continue
        
        context = _extract_context_window(text_normalized, num_start, num_end, window_words=3)
        
        # Try to find unit immediately after the number
        unit_after = ""
        text_after = text_normalized[num_end:num_end+10]
        unit_match = re.search(r'(kg|g|mg|ton|tonne)', text_after, re.IGNORECASE)
        if unit_match:
            unit_after = unit_match.group(1)
        
        numbers_found.append({
            "value": num_value,
            "start": num_start,
            "end": num_end,
            "context": context,
            "raw_match": num_match.group(0),
            "unit_after": unit_after,
        })
    
    # FALLBACK: Use old MW extraction for explicit "molecular weight" patterns
    # This catches cases like "molecular weight of 92.1 g/mol" better than context windowing
    mw_r_direct = _extract_value_near_keywords(text, _MW_REACTANT_KEYWORDS, require_mass_unit=False)
    if mw_r_direct:
        extracted["mw_reactants_g_mol"] = float(mw_r_direct[0])
    
    mw_p_direct = _extract_value_near_keywords(text, _MW_PRODUCT_KEYWORDS, require_mass_unit=False)
    if mw_p_direct:
        extracted["mw_product_g_mol"] = float(mw_p_direct[0])
    
    # Step 3 & 4: Priority Matrix + Bracket Handling
    # Track current label for bracketed contexts
    current_label = None
    used_numbers = set()
    
    for i, num_info in enumerate(numbers_found):
        if i in used_numbers:
            continue
        
        value = num_info["value"]
        context = num_info["context"]
        
        # Check for bracket/colon patterns to establish label continuity
        # e.g., "Reactant: 100kg, 200g" - apply "reactant" to both numbers
        text_before = text_normalized[:num_info["start"]]
        if ":" in text_before[-30:]:  # Colon within last 30 chars
            # Check what label precedes the colon
            colon_idx = text_before.rfind(":")
            label_text = text_before[:colon_idx]
            
            if any(kw in label_text.split()[-1] if label_text.split() else "" 
                   for kw in reactant_keywords):
                current_label = "reactant"
            elif any(kw in label_text.split()[-1] if label_text.split() else "" 
                     for kw in product_keywords):
                current_label = "product"
            elif any(kw in label_text.split()[-1] if label_text.split() else "" 
                     for kw in waste_keywords):
                current_label = "waste"
        
        # Step 3: Priority Matrix - apply conditional logic
        
        # Check for MW (Molecular Weight) patterns via context
        # Skip if already extracted via keyword method above
        if extracted["mw_reactants_g_mol"] <= 0 and _check_keyword_proximity(context, mw_keywords):
            # Check if it's reactant MW or product MW
            if _check_keyword_proximity(context, reactant_keywords):
                extracted["mw_reactants_g_mol"] = value
                used_numbers.add(i)
                continue
        
        if extracted["mw_product_g_mol"] <= 0 and _check_keyword_proximity(context, mw_keywords):
            if _check_keyword_proximity(context, product_keywords):
                extracted["mw_product_g_mol"] = value
                used_numbers.add(i)
                continue
        
        # Check for mass keywords (kg, g, mass, weight) + contextual keywords
        has_mass_keyword = _check_keyword_proximity(context, mass_keywords)
        
        if has_mass_keyword:
            # Extract unit if present in raw match or after the number
            unit = None
            if num_info.get("unit_after"):
                unit = num_info["unit_after"]
            else:
                unit_match = re.search(r'(kg|g|mg|ton|tonne)', num_info["raw_match"], re.IGNORECASE)
                unit = unit_match.group(1) if unit_match else None
            
            if not unit:
                # If no explicit unit found, skip this number (ambiguous)
                continue
            
            mass_kg = _to_kg(value, unit)
            mass_kg = float(round(mass_kg, 6))
            
            # Determine which field based on keywords
            if current_label == "reactant" or _check_keyword_proximity(context, reactant_keywords):
                if extracted["reactant_mass_kg"] <= 0:
                    extracted["reactant_mass_kg"] = mass_kg
                    used_numbers.add(i)
                    continue
            
            if current_label == "product" or _check_keyword_proximity(context, product_keywords):
                if extracted["product_mass_kg"] <= 0:
                    extracted["product_mass_kg"] = mass_kg
                    used_numbers.add(i)
                    current_label = "product"
                    continue
            
            if current_label == "waste" or _check_keyword_proximity(context, waste_keywords):
                if extracted["waste_mass_kg"] <= 0:
                    extracted["waste_mass_kg"] = mass_kg
                    used_numbers.add(i)
                    current_label = "waste"
                    continue
            
            # If we're in a bracketed context with no specific keyword,
            # use the current label to assign the mass
            if current_label:
                if current_label == "reactant" and extracted["reactant_mass_kg"] <= 0:
                    extracted["reactant_mass_kg"] = mass_kg
                    used_numbers.add(i)
                elif current_label == "product" and extracted["product_mass_kg"] <= 0:
                    extracted["product_mass_kg"] = mass_kg
                    used_numbers.add(i)
                elif current_label == "waste" and extracted["waste_mass_kg"] <= 0:
                    extracted["waste_mass_kg"] = mass_kg
                    used_numbers.add(i)
    
    # Step 5: Validation & Inference
    reactant_mass = extracted["reactant_mass_kg"]
    product_mass = extracted["product_mass_kg"]
    waste_mass = extracted["waste_mass_kg"]
    
    # If reactant_mass is missing, infer it from product + waste
    if reactant_mass <= 0 and product_mass > 0 and waste_mass > 0:
        extracted["reactant_mass_kg"] = float(round(product_mass + waste_mass, 6))
    
    # If waste is missing, infer it from reactant - product
    if waste_mass <= 0 and reactant_mass > 0 and product_mass > 0:
        extracted["waste_mass_kg"] = float(round(max(0.0, reactant_mass - product_mass), 6))
    
    return extracted


def _extract_masses(text: str) -> Dict[str, float]:
    # 1) Find all masses (number + unit). We intentionally ignore bare numbers to
    # avoid confusing MW (g/mol) for actual mass.
    masses: List[float] = []
    for m in _MASS_VALUE_UNIT_RE.finditer(text):
        value = float(m.group("value"))
        unit = m.group("unit")
        masses.append(_to_kg(value, unit))

    reactant = float(round(masses[0], 6)) if len(masses) >= 1 else 0.0
    product = float(round(masses[1], 6)) if len(masses) >= 2 else 0.0
    waste = float(round(masses[2], 6)) if len(masses) >= 3 else 0.0

    # 2) Keyword fallback: explicit "waste is 10kg" overrides order assignment for waste.
    explicit = _EXPLICIT_WASTE_RE.search(text)
    if explicit:
        waste = float(round(_to_kg(float(explicit.group("value")), explicit.group("unit")), 6))

    # 3) Math check: if only two masses were provided, infer waste = reactant - product.
    if len(masses) == 2 and reactant > 0 and product > 0 and waste <= 0:
        waste = float(round(max(0.0, reactant - product), 6))

    return {"reactant_mass_kg": reactant, "product_mass_kg": product, "waste_mass_kg": waste}


def _auto_correct_masses(m: Dict[str, float]) -> Dict[str, float]:
    """Keep as no-op for compatibility with older callers."""
    return m


def parse_text(input_string: str) -> Dict[str, Any]:
    """Parse free text and extract chemical entities and masses.
    
    Uses the Dependency-Parsing strategy for robust extraction:
    - Context windowing on each number (3 words before/after)
    - Priority matrix to assign values to correct fields
    - Bracket/colon handling for label continuity
    - Validation and inference rules
    
    Returns a clean dictionary for UI use:
      {
        "parsed_data": {
          "reaction_name": str,
          "solvent": str,
          "reactant_mass_kg": float,
          "product_mass_kg": float,
          "waste_mass_kg": float,
          "mw_reactants_g_mol": float,
          "mw_product_g_mol": float,
        },
        "success": bool,
        "requires_rerun": bool  # Flag for UI to trigger st.rerun()
      }
    """
    text = _normalize_spaces(input_string or "")

    # Extract reaction name using fuzzy matching
    reaction_name = _extract_reaction_name(text)
    
    # Extract solvent using fuzzy matching
    solvent = _extract_solvent(text)

    # Extract masses and molecular weights using dependency-parsing strategy
    extracted = _extract_mw_and_masses(text)
    
    parsed_data = {
        "reaction_name": reaction_name,
        "solvent": solvent,
        # Masses (kg)
        "reactant_mass_kg": float(extracted["reactant_mass_kg"]),
        "product_mass_kg": float(extracted["product_mass_kg"]),
        "waste_mass_kg": float(extracted["waste_mass_kg"]),
        # Molecular weights (g/mol)
        "mw_reactants_g_mol": float(extracted["mw_reactants_g_mol"]),
        "mw_product_g_mol": float(extracted["mw_product_g_mol"]),
    }

    # Determine success based on whether any data was extracted
    success = any(
        [
            bool(parsed_data["reaction_name"]),
            bool(parsed_data["solvent"]),
            parsed_data["mw_reactants_g_mol"] > 0,
            parsed_data["mw_product_g_mol"] > 0,
            parsed_data["reactant_mass_kg"] > 0,
            parsed_data["product_mass_kg"] > 0,
            parsed_data["waste_mass_kg"] > 0,
        ]
    )
    
    return {
        "parsed_data": parsed_data,
        "success": bool(success),
        "requires_rerun": True,  # Flag for UI to trigger st.rerun() and update components
    }
