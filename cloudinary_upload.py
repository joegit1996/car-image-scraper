#!/usr/bin/env python3
import os
import re
import unicodedata
from typing import Tuple, List, Optional
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "dsg6pa4hp"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "573184522222431"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "EoEztHoWoi3aksb8m4kT3uoxQ4Q"),
    secure=True,
)

BASE_DIR = os.path.dirname(__file__)
IMAGES_DIR = os.path.join(BASE_DIR, "car_images")


def parse_filename(filename: str) -> Tuple[str, str, str]:
    """Parse our filename pattern into brand, model, year.
    Expected: Brand_Model_..._Year.ext. We take last 4-digit token as year.
    """
    name = os.path.splitext(os.path.basename(filename))[0]
    tokens = re.split(r"[_\s]+", name)
    year = ""
    # Find last 4-digit token
    for tok in reversed(tokens):
        if re.fullmatch(r"\d{4}", tok):
            year = tok
            break
    brand = tokens[0]
    # model is everything between brand and year
    if year and year in tokens:
        year_idx = len(tokens) - 1 - tokens[::-1].index(year)
        model_tokens = tokens[1:year_idx]
    else:
        model_tokens = tokens[1:]
    model = "_".join(model_tokens)
    return brand, model, year


def tags_for(brand: str, model: str, year: str) -> List[str]:
    # normalize to lower kebab
    norm = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return [
        f"brand:{norm(brand)}",
        f"model:{norm(model)}",
        f"year:{norm(year)}" if year else "year:unknown",
        "source:izmostock",
    ]


def make_safe_public_id(text: str) -> str:
    # strip extension and slugify to ASCII-safe characters
    stem = os.path.splitext(os.path.basename(text))[0]
    # Normalize accents
    normalized = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode("ascii")
    # Replace disallowed chars with underscore (allow letters, numbers, hyphen, underscore)
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", normalized)
    # Collapse repeated underscores
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe or "image"


def upload_all(limit: Optional[int] = None, start_at_filename: Optional[str] = None):
    files = [
        os.path.join(IMAGES_DIR, f)
        for f in os.listdir(IMAGES_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    ]
    files.sort()

    # Resume logic: if start_at_filename provided, skip until that basename is reached
    if start_at_filename:
        start_basename = os.path.basename(start_at_filename)
        try:
            start_idx = next(i for i, p in enumerate(files) if os.path.basename(p) == start_basename)
            files = files[start_idx:]
        except StopIteration:
            pass  # if not found, continue from beginning

    if limit:
        files = files[:limit]

    total = len(files)
    for idx, path in enumerate(files, 1):
        brand, model, year = parse_filename(path)
        public_id = make_safe_public_id(path)
        tags = tags_for(brand, model, year)
        print(f"[{idx}/{total}] Uploading {path} -> public_id={public_id}")
        try:
            res = cloudinary.uploader.upload(
                path,
                folder="izmostock",
                public_id=public_id,
                overwrite=True,
                use_filename=False,
                unique_filename=False,
                tags=tags,
            )
            print("  ->", res.get("secure_url"))
        except Exception as e:
            print(f"  !! Failed: {e}")
            # continue to next file


if __name__ == "__main__":
    # By default, continue from beginning with a safety limit to avoid accidental full blast.
    upload_all(limit=50)
