"""
DEPENDENCY-PARSING STRATEGY IMPLEMENTATION GUIDE
===============================================

This document explains the robust "Dependency-Parsing" extraction logic implemented in nlp_parser.py.

## Overview

The new extraction strategy handles simple, complex, and bracketed inputs using a multi-stage
context-aware approach:

1. DATA CLEANING - Normalize input
2. CONTEXT WINDOWING - Find all numbers and analyze surrounding words
3. PRIORITY MATRIX - Apply conditional logic to assign values to correct fields
4. BRACKET HANDLING - Maintain label continuity with colons/semicolons
5. VALIDATION & INFERENCE - Calculate missing values from available data
6. OUTPUT - Return clean JSON/Dictionary

---

## IMPLEMENTATION DETAILS

### Stage 1: Data Cleaning
- Input text is normalized: lowercase, whitespace collapsed
- Regular expression: `_normalize_spaces(text or "").lower()`

Example:
```
Input:  "  Grignard Reaction   WITH   100KG   "
Output: "grignard reaction with 100kg"
```

---

### Stage 2: Context Windowing
- All numbers are found using `_NUM_RE` pattern: `\d+(?:\.\d+)?`
- For each number, extract 3 words before and 3 words after
- Look for units immediately after the number (within 10 characters)

```
Input: "We used 50kg of reactants having a molecular weight of 92.1 g/mol"
Numbers found:
  - 50   (context: [used, of, reactants, of, having, a])
  - 92.1 (context: [weight, of, g/mol, blank, blank, blank])
```

Function: `_extract_context_window(text, num_start, num_end, window_words=3)`

---

### Stage 3: Priority Matrix
The extraction applies conditional logic based on keyword proximity:

```
IF (number near 'mw', 'molecular', 'g/mol') AND (near 'reactant', 'starting', 'initial')
  → ASSIGN TO mw_reactants_g_mol

IF (number near 'mw', 'molecular', 'g/mol') AND (near 'product', 'yield', 'final')
  → ASSIGN TO mw_product_g_mol

IF (number near 'kg', 'g', 'mass', 'weight') AND (near 'reactant', 'input', 'starting')
  → ASSIGN TO reactant_mass_kg

IF (number near 'kg', 'g', 'mass', 'weight') AND (near 'product', 'obtained', 'produced')
  → ASSIGN TO product_mass_kg

IF (number near 'kg', 'g', 'mass', 'weight') AND (near 'waste', 'byproduct', 'loss')
  → ASSIGN TO waste_mass_kg
```

**Keyword Lists:**
- MW Keywords: `["mw", "molecular", "weight", "g/mol"]`
- Reactant Keywords: `["reactant", "starting", "initial", "input", "charge"]`
- Product Keywords: `["product", "yield", "final", "obtained", "produced"]`
- Waste Keywords: `["waste", "byproduct", "loss", "gen", "generated"]`
- Mass Keywords: `["kg", "g", "mass", "weight"]`

---

### Stage 4: Bracket Handling & Label Continuity
When encountering colons or brackets, the parser maintains label continuity:

```
Input: "Reactant: 150kg of starting material, also 200g of additional charge"
Processing:
  - Detects colon after "Reactant"
  - Sets current_label = "reactant"
  - Applies "reactant" label to ALL subsequent numbers (150kg, 200g)
    until a new label (Product, Waste) appears
```

Example with multiple labels:
```
Input: "Reactant: 100kg, 50g | Product: 75kg, 10g"
Result:
  - reactant_mass_kg = 100.0 (first mass in reactant section)
  - product_mass_kg = 75.0 (first mass in product section)
  - waste_mass_kg calculated from conservation
```

---

### Stage 5: Validation & Inference Rules

**Inference Rule 1**: If reactant_mass is missing:
```
reactant_mass_kg = product_mass_kg + waste_mass_kg
```

**Inference Rule 2**: If waste_mass is missing:
```
waste_mass_kg = max(0, reactant_mass_kg - product_mass_kg)
```

**Validation Check**: If waste >> product, log a warning:
```
IF waste_mass_kg > 2.5 * product_mass_kg (or > product_mass_kg + 50)
  → Logger.warning("Check if keywords were swapped")
```

---

### Stage 6: Unit Conversion
All masses are converted to kilograms (kg):

| Input Unit | Conversion |
|-----------|-----------|
| kg, kilogram | ×1.0 |
| g, gram | ÷1000 |
| mg, milligram | ÷1,000,000 |
| ton, tonne | ×1000 |

Implementation:
```python
def _to_kg(value: float, unit: Optional[str]) -> float:
    u = _normalize_unit(unit)
    if u == "g":
        return value / 1000.0
    if u == "mg":
        return value / 1_000_000.0
    if u == "ton":
        return value * 1000.0
    return value  # default kg
```

---

### Stage 7: Output Structure
Returns clean JSON/Dictionary with `requires_rerun` flag:

```python
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
    "requires_rerun": bool  # Signals UI to trigger st.rerun()
}
```

---

## TESTING COVERAGE

All test scenarios verify robust handling:

✓ TEST 1: Simple Input
  - Basic reactant, product, waste extraction
  - Result: 100kg reactant, 60kg product, 40kg waste

✓ TEST 2: Complex Input (MW + Keywords)
  - Molecular weights with g/mol notation
  - Result: Correctly extracts MW values (180.16, 250.2)

✓ TEST 3: Bracketed Input (Label Continuity)
  - Multiple values under same label
  - Result: Label applies to all subsequent numbers

✓ TEST 4: Inference - Reactant from Product + Waste
  - Missing reactant calculated as sum
  - Result: 80kg + 20kg = 100kg (inferred)

✓ TEST 5: Inference - Waste from Reactant - Product
  - Missing waste calculated as difference
  - Result: 100kg - 75kg = 25kg (inferred)

✓ TEST 6: Context Windowing with MW Keywords
  - Numbers far from keywords still extracted
  - Result: MW values properly associated with roles

✓ TEST 7: Unit Conversion
  - Handles g, kg conversions
  - Result: 500g → 0.5kg, 300g → 0.3kg, 20000g → 20kg

---

## UI INTEGRATION

In `frontend/app_ui.py`, the parser output triggers UI updates:

```python
if st.button("Parse Text"):
    result = parse_text(raw_text)
    
    if result.get("success"):
        parsed = result["parsed_data"]
        
        # Update session state with parsed values
        st.session_state["reaction_name"] = parsed["reaction_name"]
        st.session_state["mass_product"] = parsed["product_mass_kg"]
        st.session_state["mass_waste"] = parsed["waste_mass_kg"]
        
        # Force all components to refresh
        if result.get("requires_rerun"):
            st.rerun()
```

The `requires_rerun: True` flag ensures all UI widgets update immediately with parsed values.

---

## EDGE CASES HANDLED

1. **Ambiguous units**: Numbers without clear units are skipped to avoid false positives
2. **Swapped keywords**: Warning logged if waste >> product (possible keyword swap)
3. **Decimal values**: Handles both integers (100) and decimals (92.1)
4. **Plural forms**: Recognizes "reactants" and "products" (plural)
5. **Case insensitivity**: All keyword matching is case-insensitive
6. **Incomplete data**: Infers missing values using mass balance conservation

---

## KEYWORD CUSTOMIZATION

To add support for additional keywords, update the lists in `_dependency_parse_extraction`:

```python
reactant_keywords = ["reactant", "starting", "initial", "input", "charge"]
product_keywords = ["product", "yield", "final", "obtained", "produced"]
waste_keywords = ["waste", "byproduct", "loss", "gen", "generated"]
```

Example: To recognize "feedstock", add to reactant_keywords:
```python
reactant_keywords = [..., "feedstock"]
```

---

## PERFORMANCE NOTES

- Time Complexity: O(n) where n = number of words in input
- Space Complexity: O(m) where m = number extracted values (typically ≤10)
- Suitable for real-time parsing in web UI
- No external ML models required (pure regex + string matching)

---

## FUTURE ENHANCEMENTS

1. Support for chemical formula notation (e.g., "H2O: 500g")
2. Recognition of temperature-dependent conversions
3. Integration with chemical databases for automatic MW lookup
4. Support for yield percentages and selectivity data
5. Batch processing for multiple reactions in one input

---

## TROUBLESHOOTING

**Issue**: Parser returns 0.0 for expected values
- **Check**: Verify keywords are present in input text
- **Fix**: Use clear keywords from the priority matrix lists

**Issue**: Unit conversion seems wrong
- **Check**: Ensure unit is directly after the number (e.g., "500 g" not "500g")
- **Fix**: Use consistent spacing in input

**Issue**: Wrong values assigned to fields
- **Check**: Review context windowing (3 words before/after)
- **Fix**: Move numbers closer to descriptive keywords

**Issue**: MW values not extracted
- **Check**: Ensure "g/mol" notation or "molecular weight" keyword present
- **Fix**: Use patterns like "MW=180.16 g/mol" or "molecular weight: 180.16"

---

## REFERENCES

Implementation File: [services/nlp_parser.py](services/nlp_parser.py)
Test Suite: [test_dependency_parsing.py](test_dependency_parsing.py)
UI Integration: [frontend/app_ui.py](frontend/app_ui.py)
"""
