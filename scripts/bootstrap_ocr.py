"""Install pinned OCR language data on the data volume, outside worker execution."""
import hashlib
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    "eng": "7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2",
    "vie": "79df64caf7bcfb2a27df5042ecb6121e196eada34da774956995747636d5bfa1",
}


def main():
    destination = ROOT / "data/tessdata"
    destination.mkdir(parents=True, exist_ok=True)
    for language, expected in MODELS.items():
        path = destination / f"{language}.traineddata"
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == expected:
            print(f"{language}: verified")
            continue
        url = f"https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/4.1.0/{language}.traineddata"
        with urlopen(url, timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != expected:
            raise RuntimeError(f"Checksum mismatch: {language}")
        path.write_bytes(data)
        print(f"{language}: installed and verified")


if __name__ == "__main__":
    main()
