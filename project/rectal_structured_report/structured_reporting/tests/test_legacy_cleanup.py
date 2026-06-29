from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_old_rectal_mri_package_and_entrypoint_are_removed():
    assert not (ROOT / "rectal_mri_structuring").exists()
    assert not (ROOT / "run_structuring.py").exists()


def test_packaging_only_exposes_generic_structured_reporting_package():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'include = ["structured_reporting*"]' in pyproject
    assert "rectal_mri_structuring" not in pyproject
