from fastapi import FastAPI

from app.api.classify import router as classify_router
from app.api.extract import router as extract_router
from app.api.risk import router as risk_router
from app.api.review import router as review_router

from app.config import SERVER_HOST, SERVER_PORT

app = FastAPI(
    title="Contract AI Service",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "Contract AI Service Running"
    }


# 注册接口
app.include_router(classify_router)
app.include_router(extract_router)
app.include_router(risk_router)
app.include_router(review_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True
    )