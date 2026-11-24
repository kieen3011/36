"""FastAPI adapter cho dashboard web Chu de 36."""

from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, StrictInt, field_validator

from web_service import simulate_session


class SimulationRequest(BaseModel):
    """Payload dau vao cua mot phien mo phong web."""

    mssv: Annotated[str, Field(min_length=1, max_length=64)]
    steps: Annotated[StrictInt, Field(ge=1, le=200)] = 10

    @field_validator("mssv")
    @classmethod
    def validate_mssv(cls, value):
        """Chuan hoa MSSV va tu choi chuoi rong."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("mssv must not be blank")
        return cleaned


app = FastAPI(
    title="IoT Warehouse Monitoring System",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health():
    """Tra ve trang thai san sang cua API."""
    return {"status": "ok", "service": "topic36-api"}


@app.post("/api/simulate")
def simulate(payload: SimulationRequest):
    """Chay session deterministic va tra du lieu dashboard."""
    return simulate_session(payload.mssv, payload.steps)


@app.exception_handler(Exception)
async def handle_unexpected_error(_request: Request, _error: Exception):
    """Khong de lo stack trace cho loi khong du kien."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Khong the xu ly yeu cau mo phong"},
    )


DIST_DIRECTORY = Path(__file__).resolve().parent / "dist"
if DIST_DIRECTORY.is_dir():
    app.mount("/", StaticFiles(directory=DIST_DIRECTORY, html=True), name="frontend")
