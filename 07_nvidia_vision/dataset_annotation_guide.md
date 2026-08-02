# Dataset and annotation guide

> FICTIONAL ENGINEERING PROJECT — NOT FOR CONSTRUCTION

> CONCEPTUAL SAFETY ARCHITECTURE — REQUIRES PROJECT-SPECIFIC RISK ASSESSMENT, DESIGN, VERIFICATION AND VALIDATION BY A QUALIFIED MACHINERY-SAFETY ENGINEER. NO PERFORMANCE LEVEL, SIL, CATEGORY, CE CONFORMITY OR REGULATORY COMPLIANCE IS CLAIMED.

Required classes: bottle, bottle_misaligned, bottle_damage_visible, liquid_region, foam, drip, spill. Each image records bottle SKU, recipe, true fill reference method, camera/lens/light settings, production lot, shift, background, glare, foam, occlusion and synthetic/real provenance.

Splits are grouped by production lot and acquisition session—not random adjacent frames—to prevent leakage. Target policy: 70% train, 15% validation, 15% held-out test after grouping, with a separate commissioning challenge set. Synthetic images may expand edge cases but never replace real held-out validation. No dataset is included, no training was run, and no accuracy/confusion/false-accept/false-reject result exists.
