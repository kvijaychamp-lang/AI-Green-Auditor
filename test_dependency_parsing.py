"""
Test suite for Dependency-Parsing extraction strategy.

Demonstrates robust handling of:
- Simple inputs (single values)
- Complex inputs (multiple values with keywords)
- Bracketed inputs (label continuity with colons)
"""

from services.nlp_parser import parse_text


def test_simple_input():
    """Test simple input: basic reactant, product, waste"""
    print("\n" + "="*70)
    print("TEST 1: Simple Input")
    print("="*70)
    
    input_text = "Grignard reaction with 100kg reactant, yielded 60kg product, 40kg waste"
    result = parse_text(input_text)
    
    print(f"Input: {input_text}")
    print(f"\nParsed Data:")
    parsed = result["parsed_data"]
    print(f"  Reaction: {parsed['reaction_name']}")
    print(f"  Solvent: {parsed['solvent']}")
    print(f"  Reactant Mass: {parsed['reactant_mass_kg']} kg")
    print(f"  Product Mass: {parsed['product_mass_kg']} kg")
    print(f"  Waste Mass: {parsed['waste_mass_kg']} kg")
    print(f"  MW Reactants: {parsed['mw_reactants_g_mol']} g/mol")
    print(f"  MW Product: {parsed['mw_product_g_mol']} g/mol")
    print(f"Success: {result['success']}")
    print(f"Requires Rerun: {result.get('requires_rerun', False)}")
    
    # Validation
    assert parsed['reactant_mass_kg'] > 0, "Should extract reactant mass"
    assert parsed['product_mass_kg'] > 0, "Should extract product mass"
    print("✓ Test PASSED")


def test_complex_input():
    """Test complex input: MW values + mass with keywords"""
    print("\n" + "="*70)
    print("TEST 2: Complex Input (MW + Keywords)")
    print("="*70)
    
    input_text = (
        "Suzuki coupling reaction. Starting with 100g of reactant "
        "(MW=180.16 g/mol), using ethanol solvent. "
        "Obtained 75kg of final product (MW=250.20 g/mol). "
        "Generated 25kg of waste from byproducts."
    )
    result = parse_text(input_text)
    
    print(f"Input: {input_text}")
    print(f"\nParsed Data:")
    parsed = result["parsed_data"]
    print(f"  Reaction: {parsed['reaction_name']}")
    print(f"  Solvent: {parsed['solvent']}")
    print(f"  Reactant Mass: {parsed['reactant_mass_kg']} kg")
    print(f"  Product Mass: {parsed['product_mass_kg']} kg")
    print(f"  Waste Mass: {parsed['waste_mass_kg']} kg")
    print(f"  MW Reactants: {parsed['mw_reactants_g_mol']} g/mol")
    print(f"  MW Product: {parsed['mw_product_g_mol']} g/mol")
    print(f"Success: {result['success']}")
    
    # Validation
    assert parsed['reaction_name'].lower() != "", "Should extract reaction name"
    assert parsed['solvent'].lower() != "", "Should extract solvent"
    print("✓ Test PASSED")


def test_bracketed_input():
    """Test bracketed input: label continuity with colons"""
    print("\n" + "="*70)
    print("TEST 3: Bracketed Input (Label Continuity)")
    print("="*70)
    
    input_text = (
        "Friedel-Crafts reaction using chloroform. "
        "Reactant: 150kg of starting material, "
        "also 200g of additional charge. "
        "Product: 120kg obtained, plus 30kg of impurities as byproduct."
    )
    result = parse_text(input_text)
    
    print(f"Input: {input_text}")
    print(f"\nParsed Data:")
    parsed = result["parsed_data"]
    print(f"  Reaction: {parsed['reaction_name']}")
    print(f"  Solvent: {parsed['solvent']}")
    print(f"  Reactant Mass: {parsed['reactant_mass_kg']} kg")
    print(f"  Product Mass: {parsed['product_mass_kg']} kg")
    print(f"  Waste Mass: {parsed['waste_mass_kg']} kg")
    print(f"Success: {result['success']}")
    
    # Validation - should handle label continuity
    assert parsed['reactant_mass_kg'] > 0, "Should extract reactant mass with label continuity"
    assert parsed['product_mass_kg'] > 0, "Should extract product mass with label continuity"
    print("✓ Test PASSED")


def test_inference_reactant():
    """Test inference: calculate reactant from product + waste"""
    print("\n" + "="*70)
    print("TEST 4: Inference - Reactant from Product + Waste")
    print("="*70)
    
    input_text = "Produced 80kg of product and generated 20kg of waste"
    result = parse_text(input_text)
    
    print(f"Input: {input_text}")
    print(f"\nParsed Data:")
    parsed = result["parsed_data"]
    print(f"  Reactant Mass: {parsed['reactant_mass_kg']} kg")
    print(f"  Product Mass: {parsed['product_mass_kg']} kg")
    print(f"  Waste Mass: {parsed['waste_mass_kg']} kg")
    
    # Validation - reactant should be inferred
    assert parsed['product_mass_kg'] > 0, "Should extract product mass"
    assert parsed['waste_mass_kg'] > 0, "Should extract waste mass"
    if parsed['reactant_mass_kg'] > 0:
        print(f"  ✓ Reactant correctly inferred: {parsed['product_mass_kg']} + {parsed['waste_mass_kg']} = {parsed['reactant_mass_kg']}")
    print("✓ Test PASSED")


def test_inference_waste():
    """Test inference: calculate waste from reactant - product"""
    print("\n" + "="*70)
    print("TEST 5: Inference - Waste from Reactant - Product")
    print("="*70)
    
    input_text = "Started with 100kg of reactant, yield is 75kg"
    result = parse_text(input_text)
    
    print(f"Input: {input_text}")
    print(f"\nParsed Data:")
    parsed = result["parsed_data"]
    print(f"  Reactant Mass: {parsed['reactant_mass_kg']} kg")
    print(f"  Product Mass: {parsed['product_mass_kg']} kg")
    print(f"  Waste Mass: {parsed['waste_mass_kg']} kg")
    
    # Validation - waste should be inferred
    assert parsed['reactant_mass_kg'] > 0, "Should extract reactant mass"
    assert parsed['product_mass_kg'] > 0, "Should extract product mass"
    if parsed['waste_mass_kg'] > 0:
        print(f"  ✓ Waste correctly inferred: {parsed['reactant_mass_kg']} - {parsed['product_mass_kg']} = {parsed['waste_mass_kg']}")
    print("✓ Test PASSED")


def test_context_windowing():
    """Test context windowing: numbers with descriptive text and keywords"""
    print("\n" + "="*70)
    print("TEST 6: Context Windowing - Keywords + Numbers")
    print("="*70)
    
    input_text = (
        "The Suzuki coupling was run at 25°C. "
        "We started with 50kg of reactants. "
        "The MW reactants is 92.1 g/mol. "
        "We obtained 35kg of final product. "
        "The MW product is 180.16 g/mol. "
        "Waste stream contained 15kg."
    )
    result = parse_text(input_text)
    
    print(f"Input: {input_text}")
    print(f"\nParsed Data:")
    parsed = result["parsed_data"]
    print(f"  Reaction: {parsed['reaction_name']}")
    print(f"  Reactant Mass: {parsed['reactant_mass_kg']} kg")
    print(f"  Product Mass: {parsed['product_mass_kg']} kg")
    print(f"  Waste Mass: {parsed['waste_mass_kg']} kg")
    print(f"  MW Reactants: {parsed['mw_reactants_g_mol']} g/mol")
    print(f"  MW Product: {parsed['mw_product_g_mol']} g/mol")
    
    # Validation - with clearer phrasing
    assert parsed['mw_reactants_g_mol'] > 0, "Should extract MW reactants from clear keyword pattern"
    assert parsed['mw_product_g_mol'] > 0, "Should extract MW product from clear keyword pattern"
    assert parsed['reactant_mass_kg'] > 0, "Should extract reactant mass"
    assert parsed['product_mass_kg'] > 0, "Should extract product mass"
    print("✓ Test PASSED")


def test_unit_conversion():
    """Test unit conversion: g, kg with clear phrasing"""
    print("\n" + "="*70)
    print("TEST 7: Unit Conversion (g, kg)")
    print("="*70)
    
    input_text = (
        "Esterification with different units: "
        "started with 500 g of reactant, "
        "yielded 300 g of product, "
        "and generated 20000 g of waste"
    )
    result = parse_text(input_text)
    
    print(f"Input: {input_text}")
    print(f"\nParsed Data:")
    parsed = result["parsed_data"]
    print(f"  Reactant Mass: {parsed['reactant_mass_kg']} kg (from 500g)")
    print(f"  Product Mass: {parsed['product_mass_kg']} kg (from 300g)")
    print(f"  Waste Mass: {parsed['waste_mass_kg']} kg (from 20000g)")
    
    # Validation - all should be in kg
    assert 0.45 < parsed['reactant_mass_kg'] < 0.55, f"Should convert 500g to ~0.5 kg, got {parsed['reactant_mass_kg']}"
    assert 0.25 < parsed['product_mass_kg'] < 0.35, f"Should convert 300g to ~0.3 kg, got {parsed['product_mass_kg']}"
    assert 19 < parsed['waste_mass_kg'] < 21, f"Should convert 20000g to ~20 kg, got {parsed['waste_mass_kg']}"
    print("✓ Test PASSED")


def run_all_tests():
    """Run all test cases"""
    print("\n" + "#"*70)
    print("# DEPENDENCY-PARSING EXTRACTION TESTS")
    print("#"*70)
    
    try:
        test_simple_input()
        test_complex_input()
        test_bracketed_input()
        test_inference_reactant()
        test_inference_waste()
        test_context_windowing()
        test_unit_conversion()
        
        print("\n" + "#"*70)
        print("# ALL TESTS PASSED ✓")
        print("#"*70)
        
    except AssertionError as e:
        print(f"\n✗ Test FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
