#!/usr/bin/env python3
import os
import re
from typing import Optional

import cloudinary
from cloudinary import Search
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "dsg6pa4hp"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "573184522222431"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "EoEztHoWoi3aksb8m4kT3uoxQ4Q"),
    secure=True,
)

app = FastAPI(title="Car Image API", version="1.1.0")


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


@app.get("/image")
def get_image(
    brand: str = Query(..., description="Car brand, e.g., Ford"),
    model: str = Query(..., description="Car model, e.g., Focus"),
    year: str = Query(..., description="Year, e.g., 2020"),
    fallback_first: bool = Query(True, description="Return first match if multiple"),
):
    """
    Prioritize brand+model. Try exact year; otherwise select the closest available year.
    """

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

    b = f"brand:{norm(brand)}"
    m = f"model:{norm(model)}"
    y = f"year:{norm(year)}"

    # 1) exact brand+model+year
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
        raise HTTPException(status_code=500, detail=str(e))

    exact_resources = exact_res.get("resources", [])
    if exact_resources:
        if fallback_first:
            res = exact_resources[0]
            return JSONResponse({
                "url": res.get("secure_url"),
                "public_id": res.get("public_id"),
                "tags": res.get("tags", []),
                "count": len(exact_resources)
            })
        return JSONResponse({
            "results": [
                {"url": r.get("secure_url"), "public_id": r.get("public_id"), "tags": r.get("tags", [])}
                for r in exact_resources
            ],
            "count": len(exact_resources),
        })

    # 2) brand+model; choose closest year
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
        raise HTTPException(status_code=500, detail=str(e))

    bm_resources = bm_res.get("resources", [])
    if not bm_resources:
        # fallback: brand+year then filter by model tokens
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
            raise HTTPException(status_code=500, detail=str(e))

        resources = by_res.get("resources", [])
        if not resources:
            raise HTTPException(status_code=404, detail="No image found for brand/model")

        model_token = norm(model)
        def matches(r):
            pid = r.get("public_id", "").lower()
            if model_token and model_token in pid:
                return True
            tags = [t.lower() for t in r.get("tags", [])]
            return any(t.startswith("model:") and model_token in t for t in tags)

        filtered = [r for r in resources if matches(r)] or resources
        res = filtered[0]
        return JSONResponse({
            "url": res.get("secure_url"),
            "public_id": res.get("public_id"),
            "tags": res.get("tags", []),
            "count": len(filtered)
        })

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
            scored.append((abs(yr - requested_year), -yr, r))
        if scored:
            scored.sort(key=lambda t: (t[0], t[1]))
            best = scored[0][2]
            return JSONResponse({
                "url": best.get("secure_url"),
                "public_id": best.get("public_id"),
                "tags": best.get("tags", []),
                "count": len(bm_resources)
            })

    # if no parseable year or no year tags, return first brand+model match
    res = bm_resources[0]
    return JSONResponse({
        "url": res.get("secure_url"),
        "public_id": res.get("public_id"),
        "tags": res.get("tags", []),
        "count": len(bm_resources)
    })


# To run: uvicorn api_service:app --reload --port 8000
