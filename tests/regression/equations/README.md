`x_equals_one.png` is a synthetic image generated locally from the existing equation renderer (not a private document or real exam scan). The identical bundled assets/equation_smoke.png exercises real CPU recognition in source/frozen smoke. TEST_RESULTS.md records a longer synthetic expression that was misrecognized. These fixtures do not establish Sinhala exam accuracy.

# Equation regression data

physics.json is synthetic formula/context data created for this project, representing common A/L Physics notation. It is not a scan or a real recognition evaluation. Automated tests verify local rendering, XML structures and Unicode context. No OCR model was used to produce these sources.

For actual recognition evaluation, use independently transcribed licensed/owner-authorized Sinhala A/L Physics pages outside Git. Preserve original crops, page IDs, inline/display labels, source ground truth, model/version and train/validation/test provenance. Run equation_benchmark on real held-out predictions. Compare visual Word 2019 output manually; XML checks alone cannot establish glyph positioning or native editing behavior.
