"""Federal Register API routes."""

from fastapi import APIRouter, HTTPException
import aiohttp
import asyncio
from typing import Dict, Any

router = APIRouter(prefix="/api/federal-register", tags=["federal-register"])

BASE_URL = "https://www.federalregister.gov/api/v1"

async def fetch_federal_register(path: str, params: Dict[str, Any] = None) -> Dict:
    """Fetch data from Federal Register API."""
    async with aiohttp.ClientSession() as session:
        params = params or {}
        async with session.get(f"{BASE_URL}/{path}", params=params) as response:
            if response.status != 200:
                raise HTTPException(status_code=response.status, detail="Federal Register API error")
            return await response.json()

@router.get("/stats")
async def get_stats():
    """Get Federal Register statistics."""
    try:
        # Fetch documents and agencies in parallel
        documents, agencies = await asyncio.gather(
            fetch_federal_register("documents/facets", {"fields[]": ["type", "publication_date"]}),
            fetch_federal_register("agencies")
        )

        return {
            "total_documents": documents["count"],
            "documents_by_type": [
                {"type": type_, "count": count}
                for type_, count in documents["facets"]["type"].items()
            ],
            "documents_by_agency": [
                {"agency": agency["name"], "count": agency["document_count"]}
                for agency in sorted(
                    [a for a in agencies if a.get("document_count", 0) > 0],
                    key=lambda x: x.get("document_count", 0),
                    reverse=True
                )[:10]
            ],
            "documents_over_time": [
                {"date": date, "count": count}
                for date, count in documents["facets"]["publication_date"]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 