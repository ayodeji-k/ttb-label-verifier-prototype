from app.parsers import parse_fields


WARNING = (
    "GOVERNMENT WARNING: According to the Surgeon General, women should not drink "
    "alcoholic beverages during pregnancy because of the risk of birth defects. "
    "Consumption of alcoholic beverages impairs your ability to drive a car or "
    "operate machinery, and may cause health problems."
)


def test_parse_fields_extracts_required_label_data():
    fields = parse_fields(
        f"Acme Bourbon\n40% alc/vol\n750 ml\n{WARNING}",
        "Acme Bourbon",
    )

    assert fields["abv"] == "40% alc/vol"
    assert fields["net_contents"] == "750 ml"
    assert fields["brand_match"] is True
    assert fields["government_warning"]["ok"] is True


def test_parse_fields_reports_incomplete_warning():
    warning = "GOVERNMENT WARNING: women should not drink alcoholic beverages during pregnancy"

    result = parse_fields(warning)

    assert result["government_warning"]["header_present"] is True
    assert result["government_warning"]["ok"] is False


def test_parse_fields_supports_proof_when_abv_is_missing():
    assert parse_fields("100 proof")["abv"] == "100 proof"
