import pytest
from sinhala_ocr.equation_benchmark import score_equations, tokens


def record(reference, prediction):
    return {"id": "1", "document_id": "synthetic", "split": "test",
            "reference": reference, "prediction": prediction}


def test_equation_metrics_measure_real_differences():
    exact = score_equations([record("x^2", "x^2")])
    assert exact["exact_match_rate"] == 1
    assert exact["latex_character_error_rate"] == 0
    changed = score_equations([record("x^2", "x^3")])
    assert changed["exact_match_rate"] == 0
    assert changed["latex_character_error_rate"] == pytest.approx(1 / 3)
    assert changed["latex_token_error_rate"] == pytest.approx(1 / 3)
    invalid = score_equations([record("x^2", r"\bad{x}")])
    assert invalid["preview_valid_rate"] == invalid["editable_conversion_rate"] == 0
    assert tokens(r"\text{a b}") != tokens(r"\text{ab}")


def test_empty_leaked_and_duplicate_benchmarks_rejected():
    with pytest.raises(ValueError):
        score_equations([])
    leaked = record("x", "x")
    leaked["split"] = "train"
    with pytest.raises(ValueError):
        score_equations([leaked])
    with pytest.raises(ValueError):
        score_equations([record("x", "x"), record("x", "x")])
