from backend.app.parsers import parse_fields


def test_parse_required_label_fields():
    text = """ACME SPIRITS
40% ALC/VOL
750 mL
GOVERNMENT WARNING
Women should not drink alcoholic beverages during pregnancy.
Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery.
"""

    fields = parse_fields(text, "Acme Spirits")

    assert fields["abv"] == "40% ALC/VOL"
    assert fields["net_contents"] == "750 mL"
    assert fields["government_warning"]["ok"] is True
    assert fields["brand_match"] is True
