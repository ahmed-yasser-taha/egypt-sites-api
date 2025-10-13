from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from typing import List, Optional

# Load environment variables
load_dotenv()

app = FastAPI(title="Egypt Sites API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Pydantic models
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
    image_link: Optional[str] = None

class SiteResponse(BaseModel):
    status: str
    data: List[Site]
    count: int
class SingleSiteResponse(BaseModel):
    status: str
    data: Site

# Endpoints
@app.get("/", response_model=dict)
async def root():
    return {
        "message": "Egypt Sites API",
        "version": "1.1.0",
        "description": "API for Egyptian historical sites, museums, tourist attractions, and detailed local place instructions.",
        "endpoints": {
            "GET /": "API documentation",
            "GET /sites": "Get all sites (supports ?limit=50&offset=0 for pagination)",
            "GET /site/{site_id}": "Get specific site by ID",
            "GET /categories": "Get all available categories",
            "GET /category/{category_name}": "Get sites by category",
            "GET /instructions": "Get all place instructions (supports ?limit=50&offset=0 for pagination)",
            "GET /instructions/{instruction_id}": "Get specific instruction by ID"
        },
        "interactive_docs": {
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        },
        "example_usage": {
            "get_all_sites": "/sites?limit=10&offset=0",
            "get_site_by_id": "/site/1",
            "get_categories": "/categories",
            "get_museums": "/category/Museums",
            "get_historical_sites": "/category/Historical_Sites",
            "get_all_instructions": "/instructions?limit=10&offset=0",
            "get_instruction_by_id": "/instructions/1"
        }
    }

 
@app.get("/sites", response_model=SiteResponse)
async def get_all_sites(limit: int = 50, offset: int = 0):
    """
    Get all sites with pagination
    """
    try:
        response = supabase.table("egypt_sites")\
            .select("*")\
            .range(offset, offset + limit - 1)\
            .execute()
        
        sites = [Site(**site) for site in response.data]
        
        return {
            "status": "success",
            "data": sites,
            "count": len(sites)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/site/{site_id}", response_model=SingleSiteResponse)
async def get_site_by_id(site_id: int):
    """
    Get a single site by ID
    """
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

@app.get("/category/{category_name}", response_model=SiteResponse)
async def get_sites_by_category(category_name: str):
    """
    Get all sites by category
    """
    try:
        # Clean category name and replace spaces with underscores for URL
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

@app.get("/categories", response_model=dict)
async def get_all_categories():
    """
    Get all available categories
    """
    try:
        response = supabase.table("egypt_sites")\
            .select("category")\
            .execute()
        
        categories = list(set([site["category"] for site in response.data]))
        
        return {
            "status": "success",
            "categories": categories,
            "count": len(categories)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# Pydantic model for instructions
class Instruction(BaseModel):
    id: Optional[int] = None
    image_url: Optional[str] = None
    place: Optional[str] = None
    instructions: Optional[str] = None
    source: Optional[str] = None

class InstructionResponse(BaseModel):
    status: str
    data: List[Instruction]
    count: int

class SingleInstructionResponse(BaseModel):
    status: str
    data: Instruction


@app.get("/instructions", response_model=InstructionResponse)
async def get_all_instructions(limit: int = 50, offset: int = 0):
    """
    Get all place instructions with pagination
    """
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
    """
    Get a single place instruction by ID
    """
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
