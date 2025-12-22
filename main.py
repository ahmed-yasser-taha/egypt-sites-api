from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from typing import List, Optional, Any, Union
import json

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Egypt Sites API", version="1.2.0")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# ---------------------------------------------------------
# Pydantic Models (The Fix is Here)
# ---------------------------------------------------------

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

    # -------------------------------
    # Handle image_link as List[str]
    # -------------------------------
    image_link: List[str] = Field(default_factory=list)

    @field_validator('image_link', mode='before')
    @classmethod
    def ensure_list_of_strings(cls, v):
        """
        Robustly handle image_link from Supabase:
        - None -> empty list
        - List[str] -> return as is
        - JSON string representing list -> parse it
        - Single string -> wrap in list
        """
        if v is None:
            return []
        if isinstance(v, list):
            # Ensure all elements are strings
            return [str(item) for item in v]
        if isinstance(v, str):
            v = v.strip()
            if not v or v.lower() == "null":
                return []
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
                return [v]
            except json.JSONDecodeError:
                return [v]
        # Unexpected type -> return empty list
        return []

class SiteResponse(BaseModel):
    status: str
    data: List[Site]
    count: int

class SingleSiteResponse(BaseModel):
    status: str
    data: Site

# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------

# Root endpoint
@app.get("/", response_model=dict)
async def root():
    return {
        "message": "Egypt Sites API",
        "version": "1.2.0",
        "description": "API for Egyptian historical sites, museums, and tourist attractions.",
        "endpoints": {
            "GET /": "API documentation",
            "GET /sites": "Get all sites (supports pagination)",
            "GET /site/{site_id}": "Get specific site by ID",
            "GET /categories": "Get all available categories",
            "GET /category/{category_name}": "Get sites by category",
            "GET /instructions": "Get all place instructions",
            "GET /instructions/{instruction_id}": "Get specific instruction by ID"
        }
    }

# Get all sites
@app.get("/sites", response_model=SiteResponse)
async def get_all_sites(limit: int = 50, offset: int = 0):
    try:
        response = supabase.table("egypt_sites")\
            .select("*")\
            .range(offset, offset + limit - 1)\
            .execute()

        # Pass data directly to Pydantic. The validator handles the types.
        sites = [Site(**site) for site in response.data]

        return {
            "status": "success",
            "data": sites,
            "count": len(sites)
        }
    except Exception as e:
        # Log error for debugging
        print(f"Server Error in /sites: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Get site by ID
@app.get("/site/{site_id}", response_model=SingleSiteResponse)
async def get_site_by_id(site_id: int):
    try:
        response = supabase.table("egypt_sites")\
            .select("*")\
            .eq("id", site_id)\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Site not found")

        site = Site(**response.data[0])

        return {
            "status": "success",
            "data": site
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Get sites by category
@app.get("/category/{category_name}", response_model=SiteResponse)
async def get_sites_by_category(category_name: str):
    try:
        # Convert URL slug to DB format (e.g. "ancient_egypt" -> "Ancient Egypt")
        clean_category = category_name.replace("_", " ").title()

        response = supabase.table("egypt_sites")\
            .select("*")\
            .eq("category", clean_category)\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail=f"No sites found for category: {clean_category}")

        sites = [Site(**site) for site in response.data]

        return {
            "status": "success",
            "data": sites,
            "count": len(sites)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Get all categories
@app.get("/categories", response_model=dict)
async def get_all_categories():
    try:
        response = supabase.table("egypt_sites")\
            .select("category")\
            .execute()

        # Extract unique categories
        categories = list(set([site["category"] for site in response.data if site["category"]]))

        return {
            "status": "success",
            "categories": categories,
            "count": len(categories)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ---------------------------------------------------------
# Instruction Endpoints
# ---------------------------------------------------------

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
    try:
        response = supabase.table("places_instructions")\
            .select("*")\
            .range(offset, offset + limit - 1)\
            .execute()

        data = [Instruction(**row) for row in response.data]

        return {
            "status": "success",
            "data": data,
            "count": len(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/instructions/{instruction_id}", response_model=SingleInstructionResponse)
async def get_instruction_by_id(instruction_id: int):
    try:
        response = supabase.table("places_instructions")\
            .select("*")\
            .eq("id", instruction_id)\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Instruction not found")

        instruction = Instruction(**response.data[0])

        return {
            "status": "success",
            "data": instruction
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Main entry point
if __name__ == "__main__":
    import uvicorn
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8000)
