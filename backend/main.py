from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import config
from database import init_db, get_db
from core.db import get_database
from routers import stock, commodity, announcement, fundamental, quant, correlation, technical_indicators, report, fundamental_score, business, mining, events, analyst

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    db = get_database()
    await db.close()

app = FastAPI(
    title="紫金单股监控器",
    description="紫金矿业(601899/02899)个股监控系统",
    version="3.0.0",
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
app.include_router(correlation.router, prefix="/api/correlation", tags=["关联性分析"])
app.include_router(technical_indicators.router, prefix="/api/technical", tags=["技术指标"])
app.include_router(report.router, prefix="/api/report", tags=["定期报告"])
app.include_router(fundamental_score.router, prefix="/api/fundamental-score", tags=["基本面评分"])
app.include_router(business.router, prefix="/api/business", tags=["业务动向"])
app.include_router(mining.router, prefix="/api/mining", tags=["矿业数据"])
app.include_router(events.router, prefix="/api/events", tags=["事件系统"])
app.include_router(analyst.router, prefix="/api/analyst", tags=["券商研报"])

@app.get("/")
async def root():
    return {"message": "紫金单股监控器 API"}

@app.get("/health")
async def health():
    from core.circuit_breaker import get_all_breakers
    return {
        "status": "healthy",
        "version": "3.0.0",
        "deploy_mode": config.DEPLOY_MODE,
        "circuit_breakers": get_all_breakers(),
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, reload=True)
