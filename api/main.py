#!/usr/bin/env python3
import os
import re
from typing import Optional

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

app = FastAPI(title="Car Image API", version="1.2.0")


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


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
    Prioritizes brand+model. If exact year not available, picks the closest available year for that brand+model.
    """
    # Validate Cloudinary config
    if not all([
        os.environ.get("CLOUDINARY_CLOUD_NAME"),
        os.environ.get("CLOUDINARY_API_KEY"),
        os.environ.get("CLOUDINARY_API_SECRET"),
    ]):
        raise HTTPException(
            status_code=500,
            detail="Cloudinary configuration missing. Please set environment variables.",
        )

    def extract_year_from_tags(tags):
        for t in tags or []:
            if t.lower().startswith("year:"):
                val = t.split(":", 1)[1]
                if val.isdigit():
                    try:
                        return int(val)
                    except ValueError:
                        return None
        return None

    # Normalized tokens
    b = f"brand:{norm(brand)}"
    m = f"model:{norm(model)}"
    y = f"year:{norm(year)}"

    # 1) Try exact brand+model+year
    expr_exact = f'tags="{b}" AND tags="{m}" AND tags="{y}"'
    try:
        exact_res = (
            Search()
            .expression(expr_exact)
            .with_field("tags")
            .max_results(200)
            .sort_by("public_id", "desc")
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary search error: {str(e)}")

    exact_resources = exact_res.get("resources", [])
    if exact_resources:
        if fallback_first:
            res = exact_resources[0]
            return JSONResponse(
                {
                    "url": res.get("secure_url"),
                    "public_id": res.get("public_id"),
                    "tags": res.get("tags", []),
                    "count": len(exact_resources),
                    "query": {"brand": brand, "model": model, "year": year},
                }
            )
        return JSONResponse(
            {
                "results": [
                    {
                        "url": r.get("secure_url"),
                        "public_id": r.get("public_id"),
                        "tags": r.get("tags", []),
                    }
                    for r in exact_resources
                ],
                "count": len(exact_resources),
                "query": {"brand": brand, "model": model, "year": year},
            }
        )

    # 2) Fallback: brand+model only, then choose closest year
    expr_bm = f'tags="{b}" AND tags="{m}"'
    try:
        bm_res = (
            Search()
            .expression(expr_bm)
            .with_field("tags")
            .max_results(200)
            .sort_by("public_id", "desc")
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary search error: {str(e)}")

    bm_resources = bm_res.get("resources", [])
    if not bm_resources:
        # As a last resort, try brand+year and filter by model tokens in pid/tags
        expr_by = f'tags="{b}" AND tags="{y}"'
        try:
            by_res = (
                Search()
                .expression(expr_by)
                .with_field("tags")
                .max_results(200)
                .sort_by("public_id", "desc")
                .execute()
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Cloudinary search error: {str(e)}")

        resources = by_res.get("resources", [])
        if not resources:
            raise HTTPException(
                status_code=404,
                detail=f"No image found for brand/model: {brand} {model}",
            )

        model_token = norm(model)
        def matches(r):
            pid = r.get("public_id", "").lower()
            if model_token and model_token in pid:
                return True
            tags = [t.lower() for t in r.get("tags", [])]
            return any(t.startswith("model:") and model_token in t for t in tags)

        filtered = [r for r in resources if matches(r)] or resources
        res = filtered[0]
        return JSONResponse(
            {
                "url": res.get("secure_url"),
                "public_id": res.get("public_id"),
                "tags": res.get("tags", []),
                "count": len(filtered),
                "query": {"brand": brand, "model": model, "year": year},
            }
        )

    # Compute closest year among bm_resources
    try:
        requested_year = int(norm(year))
    except ValueError:
        requested_year = None

    if requested_year is not None:
        scored = []
        for r in bm_resources:
            yr = extract_year_from_tags(r.get("tags", []))
            if yr is None:
                continue
            scored.append((abs(yr - requested_year), -yr, r))  # prefer newer on tie

        if scored:
            scored.sort(key=lambda t: (t[0], t[1]))
            best = scored[0][2]
            return JSONResponse(
                {
                    "url": best.get("secure_url"),
                    "public_id": best.get("public_id"),
                    "tags": best.get("tags", []),
                    "count": len(bm_resources),
                    "query": {"brand": brand, "model": model, "year": year},
                }
            )

    # If requested year not parseable or no year tags, just return first bm match
    res = bm_resources[0]
    return JSONResponse(
        {
            "url": res.get("secure_url"),
            "public_id": res.get("public_id"),
            "tags": res.get("tags", []),
            "count": len(bm_resources),
            "query": {"brand": brand, "model": model, "year": year},
        }
    )


# This is required for Vercel
handler = app

