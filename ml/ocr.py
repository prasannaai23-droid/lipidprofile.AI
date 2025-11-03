import pytesseract
from PIL import Image, ImageOps, ImageFilter
import re
import io

# Set this to your tesseract install path if necessary
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def preprocess_image(image_path):
    img = Image.open(image_path)
    # convert to grayscale, increase contrast, filter to improve OCR
    img = ImageOps.grayscale(img)
    img = img.filter(ImageFilter.SHARPEN)
    return img

def extract_values_from_imagefile(image_path):
    img = preprocess_image(image_path)
    text = pytesseract.image_to_string(img)
    return extract_values_from_text(text)

def extract_values_from_bytes(image_bytes):
    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.grayscale(img)
    img = img.filter(ImageFilter.SHARPEN)
    text = pytesseract.image_to_string(img)
    return extract_values_from_text(text)

def extract_values_from_text(text):
    # Print raw OCR for debugging
    # print("OCR TEXT:\n", text)

    def find_num(patterns):
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                try:
                    return float(m.group(1))
                except:
                    pass
        return None

    ldl = find_num([r"LDL[^0-9]*?([0-9]{2,4}\.?\d*)", r"LDL-C[^0-9]*?([0-9]{2,4}\.?\d*)"])
    hdl = find_num([r"HDL[^0-9]*?([0-9]{2,4}\.?\d*)"])
    trig = find_num([r"TRI[Gg]?[Yy]?[Ll]?[Ee]?[Rr]?[Ii]?[Dd]?[Ee]?[Ss]?\s*[:=]?\s*([0-9]{2,4}\.?\d*)", r"Triglycerides[^0-9]*?([0-9]{2,4}\.?\d*)", r"TRIG[^0-9]*?([0-9]{2,4}\.?\d*)"])

    # return parsed floats or None
    return {
        "ldl": ldl,
        "hdl": hdl,
        "trig": trig,
        "raw_text": text
    }
