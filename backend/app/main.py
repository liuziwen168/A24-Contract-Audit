from fastapi import FastAPI


app = FastAPI(title="A24 Contract Audit Backend", version="0.1.0")


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "version": app.version}
