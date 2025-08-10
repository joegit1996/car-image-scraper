#!/usr/bin/env python3
import argparse
import os
import re
from typing import List

CAR_IMAGES_DIR = os.path.join(os.path.dirname(__file__), "car_images")


def sanitize(text: str) -> str:
    # match the filename sanitization used in scraper
    text = re.sub(r"[<>:\"/\\|?*]", "_", text)
    text = re.sub(r"\s+", "_", text)
    return text.strip("._").lower()


def find_matches(brand: str, model: str, year: str, limit: int = 10) -> List[str]:
    if not os.path.isdir(CAR_IMAGES_DIR):
        return []

    b = sanitize(brand)
    m = sanitize(model)
    y = sanitize(year)

    results = []
    for fname in os.listdir(CAR_IMAGES_DIR):
        if not fname.lower().endswith((".jpg", ".png", ".jpeg", ".webp")):
            continue
        f = fname.lower()
        # Require all three tokens to appear in filename
        if b in f and m in f and y in f:
            results.append(os.path.join(CAR_IMAGES_DIR, fname))
            if len(results) >= limit:
                break

    # If no results, try looser match: brand + year, and model token-by-token
    if not results:
        model_tokens = [t for t in re.split(r"[_\s-]+", m) if t]
        for fname in os.listdir(CAR_IMAGES_DIR):
            if not fname.lower().endswith((".jpg", ".png", ".jpeg", ".webp")):
                continue
            f = fname.lower()
            if b in f and y in f and all(tok in f for tok in model_tokens):
                results.append(os.path.join(CAR_IMAGES_DIR, fname))
                if len(results) >= limit:
                    break

    return results


def main():
    parser = argparse.ArgumentParser(description="Find downloaded car image by brand, model, and year")
    parser.add_argument("--brand", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--year", required=True)
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    matches = find_matches(args.brand, args.model, args.year, args.limit)
    if not matches:
        print("No matches found.")
        return

    print("Matches:")
    for p in matches:
        print(p)


if __name__ == "__main__":
    main()

