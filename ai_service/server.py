from fastapi import FastAPI
from pydantic import BaseModel

from services.compatibility_service import rank_outfit_candidates
from services.item_analysis_service import analyze_item_image
from services.visual_search_service import rank_visual_candidates


app = FastAPI(title="ReBloom AI Service")


class ProductPayload(BaseModel):
    product_id: int
    image_url: str | None = None
    category: str | None = None
    subcategory: str | None = None
    color: str | None = None
    title: str | None = None


class OutfitRankRequest(BaseModel):
    base_product: ProductPayload
    candidates: list[ProductPayload]
    limit: int = 6


class VisualSearchRequest(BaseModel):
    query_image: str
    candidates: list[ProductPayload]
    limit: int = 12


class AnalyzeItemRequest(BaseModel):
    query_image: str


def dump_model(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/outfit-rank")
def outfit_rank(payload: OutfitRankRequest):
    ranked = rank_outfit_candidates(
        dump_model(payload.base_product),
        [dump_model(candidate) for candidate in payload.candidates],
        limit=payload.limit,
    )
    return {"ranked": ranked}


@app.post("/visual-search")
def visual_search(payload: VisualSearchRequest):
    ranked, preprocessing, predicted = rank_visual_candidates(
        payload.query_image,
        [dump_model(candidate) for candidate in payload.candidates],
        limit=payload.limit,
    )
    return {"ranked": ranked, "preprocessing": preprocessing, "predicted": predicted}


@app.post("/analyze-item")
def analyze_item(payload: AnalyzeItemRequest):
    return analyze_item_image(payload.query_image)
