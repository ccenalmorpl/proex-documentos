from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.documentos.schemas import HealthResponse
from app.documentos import router as documentos_router
from app.empresas import router as empresas_router
from app.pedidos import router as pedidos_router
from datetime import datetime
import uvicorn
import logging

logging.basicConfig(level=settings.log_level, format=settings.log_format)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Microservicio para generación de certificados (Origen / Sanitario) por contenedores",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.include_router(documentos_router.router, prefix="/api/v1/documentos", tags=["documentos"])
logger.info("Documentos router registered at /api/v1/documentos")

app.include_router(empresas_router.router, prefix="/api/v1/empresas", tags=["empresas"])
logger.info("Empresas router registered at /api/v1/empresas")

app.include_router(pedidos_router.router, prefix="/api/v1/pedidos", tags=["pedidos"])
logger.info("Pedidos router registered at /api/v1/pedidos")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        version=settings.version,
        timestamp=datetime.now()
    )


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.version,
        "docs": "/docs"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
