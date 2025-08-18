import os
import re
from typing import Optional, List

import cloudinary
from cloudinary import Search
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse


# Configure Cloudinary with environment variables
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True,
)

app = FastAPI(title="Car Image API", version="1.3.0")


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

# Common brand aliases → canonical slug used in Cloudinary brand tags
# Extend as needed
BRAND_ALIASES = {
    "mercedes": "mercedes-benz",
    "merc": "mercedes-benz",
    "benz": "mercedes-benz",
    "vw": "volkswagen",
    "chevy": "chevrolet",
    "range-rover": "land-rover",
    "landrover": "land-rover",
    "alfa": "alfa-romeo",
    "bimmer": "bmw",
    "mini-cooper": "mini",
}

def brand_candidates(brand: str) -> List[str]:
    slug = norm(brand)
    candidates: List[str] = []
    alias = BRAND_ALIASES.get(slug)
    if alias and alias != slug:
        candidates.append(alias)
    # Try original normalized brand
    candidates.append(slug)
    # Deduplicate while preserving order
    seen = set()
    unique: List[str] = []
    for c in candidates:
        if c not in seen:
            unique.append(c)
            seen.add(c)
    return unique


@app.get("/")
def root():
    return {"message": "Car Image API - use /image endpoint"}


@app.get("/image")
def get_image(
    brand: str = Query(..., description="Car brand, e.g., Ford"),
    model: str = Query(..., description="Car model, e.g., Focus"),
    year: str = Query(..., description="Year, e.g., 2020"),
    fallback_first: bool = Query(True, description="Return first match if multiple"),
):
    """
    Get car image URL by brand, model, and year.
    Prioritizes brand+model. If exact year not available, returns closest available year for that brand+model.
    """
    # Validate Cloudinary config
    if not all([
        os.environ.get("CLOUDINARY_CLOUD_NAME"),
        os.environ.get("CLOUDINARY_API_KEY"), 
        os.environ.get("CLOUDINARY_API_SECRET")
    ]):
        raise HTTPException(
            status_code=500, 
            detail="Cloudinary configuration missing. Please set environment variables."
        )

    def extract_year_from_tags(tags):
        for t in tags or []:
            if t.lower().startswith("year:"):
                v = t.split(":", 1)[1]
                if v.isdigit():
                    try:
                        return int(v)
                    except ValueError:
                        return None
        return None

    brand_slugs = brand_candidates(brand)
    m = f"model:{norm(model)}"
    y = f"year:{norm(year)}"

    # Helper: model match by tag or substring in public_id
    model_token = norm(model)
    def matches_model(r):
        pid = r.get("public_id", "").lower()
        if model_token and model_token in pid:
            return True
        tags_l = [t.lower() for t in r.get("tags", [])]
        return any(t.startswith("model:") and model_token in t for t in tags_l)

    # Paginated search for all resources under a brand and filter by model
    def fetch_brand_model_matches(expr: str):
        model_matches = []
        cursor = None
        safety_page_cap = 60  # cap to avoid unbounded loops
        page_index = 0
        while True:
            s = (
                Search()
                .expression(expr)
                .with_field("tags")
                .max_results(200)
                .sort_by("public_id", "desc")
            )
            if cursor:
                try:
                    s = s.next_cursor(cursor)  # type: ignore[attr-defined]
                except Exception:
                    # Older SDKs may not expose next_cursor as a builder; fall back to single page
                    break
            try:
                page = s.execute()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Cloudinary search error: {str(e)}")

            resources = page.get("resources", [])
            if resources:
                for res in resources:
                    if matches_model(res):
                        model_matches.append(res)

            cursor = page.get("next_cursor")
            page_index += 1
            if not cursor or page_index >= safety_page_cap:
                break

        return model_matches

    # 1) Exact year within brand candidates, then filter by model
    for bslug in brand_slugs:
        b = f"brand:{bslug}"
        expr_exact = f'tags="{b}" AND tags="{y}"'
        try:
            exact = (
                Search()
                .expression(expr_exact)
                .with_field("tags")
                .max_results(200)
                .sort_by("public_id", "desc")
                .execute()
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Cloudinary search error: {str(e)}")

        exact_resources = exact.get("resources", [])
        exact_filtered = [r for r in exact_resources if matches_model(r)]
        if exact_filtered:
            if fallback_first:
                res = exact_filtered[0]
                return JSONResponse({
                    "url": res.get("secure_url"),
                    "public_id": res.get("public_id"),
                    "tags": res.get("tags", []),
                    "count": len(exact_filtered),
                    "query": {"brand": brand, "model": model, "year": year},
                })
            return JSONResponse({
                "results": [
                    {"url": r.get("secure_url"), "public_id": r.get("public_id"), "tags": r.get("tags", [])}
                    for r in exact_filtered
                ],
                "count": len(exact_filtered),
                "query": {"brand": brand, "model": model, "year": year},
            })

    # 2) Brand across all years (paginated); filter by model; pick closest year
    model_filtered = []
    for bslug in brand_slugs:
        b = f'brand:{bslug}'
        expr_b = f'tags="{b}"'
        model_filtered = fetch_brand_model_matches(expr_b)
        if model_filtered:
            break
    if not model_filtered:
        raise HTTPException(status_code=404, detail=f"No image found for brand/model: {brand} {model}")

    # choose closest year among brand+model filtered
    try:
        requested_year = int(norm(year))
    except ValueError:
        requested_year = None

    if requested_year is not None:
        scored = []
        for r in model_filtered:
            yr = extract_year_from_tags(r.get("tags", []))
            if yr is None:
                continue
            scored.append((abs(yr - requested_year), -yr, r))
        if scored:
            scored.sort(key=lambda t: (t[0], t[1]))
            best = scored[0][2]
            return JSONResponse({
                "url": best.get("secure_url"),
                "public_id": best.get("public_id"),
                "tags": best.get("tags", []),
                "count": len(model_filtered),
                "query": {"brand": brand, "model": model, "year": year},
            })

    # If year cannot be parsed or no year tags, return first brand+model match
    res = model_filtered[0]
    return JSONResponse({
        "url": res.get("secure_url"),
        "public_id": res.get("public_id"),
        "tags": res.get("tags", []),
        "count": len(model_filtered),
        "query": {"brand": brand, "model": model, "year": year},
    })


@app.get("/test")
def test():
    return {"message": "API is working!", "status": "success"}



