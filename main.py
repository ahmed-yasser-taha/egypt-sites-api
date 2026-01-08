from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from typing import List, Optional, Any
import json

# =========================
# Load environment variables
# =========================
load_dotenv()

app = FastAPI(title="Egypt Sites API", version="1.1.0")

# =========================
# CORS middleware
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Supabase client
# =========================
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# =========================================================
# ======================= SITES ============================
# =========================================================

class Site(BaseModel):
    id: Optional[int] = None
    category: Optional[str] = None
    name: str
    latitude: float
    longitude: float
    governorate: Optional[str] = None
    description: Optional[str] = None
    note: Optional[str] = None
    booking: Optional[str] = None
    gmaps_link: Optional[str] = None
    image_link: Optional[List[str]] = None

    @field_validator("image_link", mode="before")
    @classmethod
    def parse_image_link(cls, v: Any):
        if v is None:
            return None
        if isinstance(v, list):
            return v if v else None
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else [v]
            except:
                return [v]
        return None


class SiteResponse(BaseModel):
    status: str
    data: List[Site]
    count: int


class SingleSiteResponse(BaseModel):
    status: str
    data: Site


@app.get("/sites", response_model=SiteResponse)
async def get_all_sites(limit: int = 50, offset: int = 0):
    response = supabase.table("egypt_sites") \
        .select("*") \
        .range(offset, offset + limit - 1) \
        .execute()

    sites = [Site(**row) for row in response.data]

    return {
        "status": "success",
        "data": sites,
        "count": len(sites)
    }


@app.get("/site/{site_id}", response_model=SingleSiteResponse)
async def get_site_by_id(site_id: int):
    response = supabase.table("egypt_sites") \
        .select("*") \
        .eq("id", site_id) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Site not found")

    return {
        "status": "success",
        "data": Site(**response.data[0])
    }


@app.get("/category/{category_name}", response_model=SiteResponse)
async def get_sites_by_category(category_name: str):
    clean_category = category_name.replace("_", " ").title()

    response = supabase.table("egypt_sites") \
        .select("*") \
        .eq("category", clean_category) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="No sites found")

    sites = [Site(**row) for row in response.data]

    return {
        "status": "success",
        "data": sites,
        "count": len(sites)
    }


@app.get("/categories")
async def get_all_categories():
    response = supabase.table("egypt_sites") \
        .select("category") \
        .execute()

    categories = list(set(row["category"] for row in response.data))

    return {
        "status": "success",
        "categories": categories,
        "count": len(categories)
    }

# =========================================================
# =================== INSTRUCTIONS =========================
# =========================================================

class Instruction(BaseModel):
    id: Optional[int] = None
    image_url: Optional[str] = None
    place: Optional[str] = None
    instructions: Optional[str] = None
    source: Optional[str] = None
    is_official_source: Optional[bool] = None


class InstructionResponse(BaseModel):
    status: str
    data: List[Instruction]
    count: int


class SingleInstructionResponse(BaseModel):
    status: str
    data: Instruction


@app.get("/instructions", response_model=InstructionResponse)
async def get_all_instructions(limit: int = 50, offset: int = 0):
    response = supabase.table("places_instructions") \
        .select("*") \
        .range(offset, offset + limit - 1) \
        .execute()

    data = [Instruction(**row) for row in response.data]

    return {
        "status": "success",
        "data": data,
        "count": len(data)
    }


@app.get("/instructions/{instruction_id}", response_model=SingleInstructionResponse)
async def get_instruction_by_id(instruction_id: int):
    response = supabase.table("places_instructions") \
        .select("*") \
        .eq("id", instruction_id) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Instruction not found")

    return {
        "status": "success",
        "data": Instruction(**response.data[0])
    }

# =========================================================
# ===================== GALLERY ============================
# =========================================================

class PlaceGallery(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    images: Optional[List[str]] = None
    created_at: Optional[str] = None

    @field_validator("images", mode="before")
    @classmethod
    def parse_images(cls, v: Any):
        if v is None:
            return None
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else None
            except:
                return None
        return None


class GalleryResponse(BaseModel):
    status: str
    data: List[PlaceGallery]
    count: int


class SingleGalleryResponse(BaseModel):
    status: str
    data: PlaceGallery


@app.get("/gallery", response_model=GalleryResponse)
async def get_gallery():
    response = supabase.table("places_gallery") \
        .select("*") \
        .execute()

    data = [PlaceGallery(**row) for row in response.data]

    return {
        "status": "success",
        "data": data,
        "count": len(data)
    }


@app.get("/gallery/{place_id}", response_model=SingleGalleryResponse)
async def get_gallery_place(place_id: int):
    response = supabase.table("places_gallery") \
        .select("*") \
        .eq("id", place_id) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Place not found")

    return {
        "status": "success",
        "data": PlaceGallery(**response.data[0])
    }


@app.post("/gallery", response_model=SingleGalleryResponse)
async def add_gallery_place(place: PlaceGallery):
    payload = place.dict(exclude={"id", "created_at"})

    response = supabase.table("places_gallery") \
        .insert(payload) \
        .execute()

    return {
        "status": "success",
        "data": PlaceGallery(**response.data[0])
    }


@app.delete("/gallery/{place_id}")
async def delete_gallery_place(place_id: int):
    supabase.table("places_gallery") \
        .delete() \
        .eq("id", place_id) \
        .execute()

    return {"status": "success"}

# =========================================================
# Run server
# =========================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
