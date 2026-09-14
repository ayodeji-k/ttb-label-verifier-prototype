from PIL import Image, ImageOps, ImageFilter
import pytesseract


def _preprocess_image(img: Image.Image) -> Image.Image:
    # Convert to grayscale, autocontrast, slight blur to reduce noise
    gray = img.convert("L")
    # Resize if very large (keep ratio)
    max_dim = 1600
    if max(gray.size) > max_dim:
        ratio = max_dim / max(gray.size)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        gray = gray.resize(new_size, Image.LANCZOS)

    gray = ImageOps.autocontrast(gray)
    gray = gray.filter(ImageFilter.MedianFilter(size=3))
    return gray


def ocr_image(img: Image.Image) -> dict:
    """Run lightweight preprocessing and pytesseract OCR.
    Returns a dict with full text and simple word bounding boxes.
    """
    pre = _preprocess_image(img)
    # Use Tesseract's tsv/data output for word-level boxes
    data = pytesseract.image_to_data(pre, output_type=pytesseract.Output.DICT)
    n_boxes = len(data.get("level", []))
    boxes = []
    words = []
    for i in range(n_boxes):
        text = data.get("text", [""])[i]
        conf = int(data.get("conf", ["-1"])[i])
        if text and text.strip():
            x = int(data.get("left", [0])[i])
            y = int(data.get("top", [0])[i])
            w = int(data.get("width", [0])[i])
            h = int(data.get("height", [0])[i])
            boxes.append({"text": text, "conf": conf, "box": [x, y, w, h]})
            words.append(text)

    full_text = "\n".join([w for w in words])
    return {"text": full_text, "boxes": boxes}
