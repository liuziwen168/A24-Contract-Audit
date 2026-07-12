from fastapi import FastAPI

from app.api.classify import router as classify_router
from app.api.extract import router as extract_router

app = FastAPI(
    title="Contract AI Service",
    version="0.1.0"
)

app.include_router(classify_router)
app.include_router(extract_router)

@app.get("/")
def root():
    return {
        "message": "AI Service Running"
    }