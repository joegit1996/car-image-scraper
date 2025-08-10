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
    
    Example: /image?brand=ford&model=focus&year=2020
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
    
    # brand/year tags
    b = f"brand:{norm(brand)}"
    y = f"year:{norm(year)}"
    model_token = norm(model)

    # First: fetch candidates by brand+year only
    expr = f'tags="{b}" AND tags="{y}"'

    try:
        results = (
            Search()
            .expression(expr)
            .with_field("tags")
            .max_results(200)
            .sort_by("public_id", "desc")
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary search error: {str(e)}")

    resources = results.get("resources", [])
    if not resources:
        raise HTTPException(
            status_code=404, 
            detail=f"No image found for brand: {brand}, year: {year}"
        )

    # Filter by model token in public_id or in tags that look like model:*
    def matches(r) -> bool:
        pid = r.get("public_id", "").lower()
        if model_token and model_token in pid:
            return True
        tags = [t.lower() for t in r.get("tags", [])]
        return any(t.startswith("model:") and model_token in t for t in tags)

    filtered = [r for r in resources if matches(r)] or resources

    if fallback_first:
        res = filtered[0]
        return JSONResponse({
            "url": res.get("secure_url"),
            "public_id": res.get("public_id"),
            "tags": res.get("tags", []),
            "count": len(filtered),
            "query": {
                "brand": brand,
                "model": model, 
                "year": year
            }
        })

    return JSONResponse({
        "results": [
            {"url": r.get("secure_url"), "public_id": r.get("public_id"), "tags": r.get("tags", [])}
            for r in filtered
        ],
        "count": len(filtered),
        "query": {
            "brand": brand,
            "model": model,
            "year": year
        }
    })


# This is required for Vercel
handler = app
