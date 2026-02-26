import uvicorn
from fastapi import FastAPI

from api.tickets import router as tickets_router
from core.database import init_db

app = FastAPI(title="AI Support System")
app.include_router(tickets_router, prefix="/api")


from core.logger import setup_logger
setup_logger()


@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )