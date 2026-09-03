import re
from rapidfuzz import fuzz

# Regex patterns
ABV_REGEX = re.compile(r"(?i)(\d{1,2}(?:\.\d)?\s*%)(?:\s*alc\.?\/?vol\.?)?")
PROOF_REGEX = re.compile(r"(?i)(\d{2,3})\s*proof")
NET_REGEX = re.compile(r"(?i)(\d+(?:\.\d+)?\s*(?:ml|mL|l|L|liters|litres|oz|fl oz))")
GOV_WARNING_HEADER = "GOVERNMENT WARNING"
# Minimal fragments to check for the two required sentences
GOV_WARNING_FRAGMENTS = [
    "women should not drink alcoholic beverages during pregnancy",
    "impairs your ability to drive a car or operate machinery",
]


def _find_abv(text: str) -> str | None:
    m = ABV_REGEX.search(text)
    if m:
        return m.group(0).strip()
    m2 = PROOF_REGEX.search(text)
    if m2:
        return f"{m2.group(1).strip()} proof"
    return None


def _find_net(text: str) -> str | None:
    m = NET_REGEX.search(text)
    if m:
        return m.group(0).strip()
    return None


def _check_government_warning(text: str) -> dict:
    t_upper = text.upper()
    header_present = GOV_WARNING_HEADER in t_upper
    fragments_found = [frag for frag in GOV_WARNING_FRAGMENTS if frag in text.lower()]
    return {"header_present": header_present, "fragments_found": fragments_found, "ok": header_present and len(fragments_found) == len(GOV_WARNING_FRAGMENTS)}


def parse_fields(ocr_text: str, application_brand: str | None = None) -> dict:
    # Very simple heuristics: run regex and fuzzy brand match if provided
    abv = _find_abv(ocr_text)
    net = _find_net(ocr_text)
    warning = _check_government_warning(ocr_text)

    brand = None
    brand_score = None
    brand_match = None
    if application_brand:
        # Heuristic: try to find a line in OCR text that looks like a brand candidate
        lines = [l.strip() for l in ocr_text.splitlines() if l.strip()]
        best = ("", 0)
        for ln in lines[:40]:
            s = fuzz.ratio(ln.lower(), application_brand.lower())
            if s > best[1]:
                best = (ln, s)
        brand = best[0] if best[1] > 0 else None
        brand_score = best[1]
        brand_match = brand_score >= 90

    return {
        "brand_candidate": brand,
        "brand_score": brand_score,
        "brand_match": brand_match,
        "abv": abv,
        "net_contents": net,
        "government_warning": warning,
    }
