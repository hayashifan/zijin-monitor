from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import config
from database import init_db
from routers import stock, commodity, announcement, fundamental, quant

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown

app = FastAPI(
    title="紫金单股监控器",
    description="紫金矿业(601899/02899)个股监控系统",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.CORS_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(stock.router, prefix="/api/stock", tags=["股票行情"])
app.include_router(commodity.router, prefix="/api/commodity", tags=["大宗商品"])
app.include_router(announcement.router, prefix="/api/announcement", tags=["公告"])
app.include_router(fundamental.router, prefix="/api/fundamental", tags=["基本面"])
app.include_router(quant.router, prefix="/api/quant", tags=["量化分析"])

@app.get("/")
async def root():
    return {"message": "紫金单股监控器 API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, reload=True)
