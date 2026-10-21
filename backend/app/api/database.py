
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(
    prefix="/api/database",
    tags=["Database"],
)


@router.get("/health")
def database_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "success",
            "database": "connected",
            "message": "PostgreSQL connection is working",
        }

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(e)}",
        )