from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date as date_type, timedelta
from app.database import get_db
from app.models.user import User
from app.models.weight_log import WeightLog
from app.schemas.weight_log import (
    WeightLog as WeightLogSchema,
    WeightLogCreate,
    WeightOCRResponse,
    WeightStats,
    WeightHistory
)
from app.api.deps import get_current_user
from app.services.gemini import extract_body_weight_from_image

router = APIRouter()


@router.post("/manual", response_model=WeightLogSchema, status_code=status.HTTP_201_CREATED)
def log_weight_manual(
    weight_log: WeightLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually log body weight."""
    new_log = WeightLog(
        user_id=current_user.id,
        weight=weight_log.weight,
        date=weight_log.date or date_type.today(),
        method=weight_log.method
    )

    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    return new_log


@router.post("/ocr", response_model=WeightOCRResponse)
async def extract_body_weight(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Extract body weight from weighing scale image using OCR."""
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )

    # Read image bytes
    image_bytes = await file.read()

    # Extract weight using Gemini Vision
    weight, confidence, message = extract_body_weight_from_image(image_bytes)

    if weight is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return WeightOCRResponse(
        weight=weight,
        confidence=confidence,
        message=message
    )


@router.get("/history", response_model=WeightHistory)
def get_weight_history(
    days: Optional[int] = None,  # 7, 30, 90, or None for all
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get weight history with statistics."""
    query = db.query(WeightLog).filter(WeightLog.user_id == current_user.id)

    # Filter by date range if specified
    if days:
        start_date = date_type.today() - timedelta(days=days)
        query = query.filter(WeightLog.date >= start_date)

    # Order by date
    logs = query.order_by(WeightLog.date.desc()).all()

    if not logs:
        return WeightHistory(
            logs=[],
            stats=WeightStats(
                lowest=0,
                highest=0,
                average=0,
                current=None,
                change_from_start=None,
                trend="stable"
            )
        )

    # Calculate statistics
    weights = [log.weight for log in logs]
    lowest = min(weights)
    highest = max(weights)
    average = sum(weights) / len(weights)
    current = logs[0].weight  # Most recent (desc order)

    # Calculate change from start
    oldest_weight = logs[-1].weight  # Oldest (desc order)
    change_from_start = current - oldest_weight

    # Determine trend
    if len(logs) >= 3:
        recent_avg = sum([log.weight for log in logs[:3]]) / 3
        older_avg = sum([log.weight for log in logs[-3:]]) / 3
        diff = recent_avg - older_avg

        if diff < -0.5:
            trend = "decreasing"
        elif diff > 0.5:
            trend = "increasing"
        else:
            trend = "stable"
    else:
        trend = "stable"

    stats = WeightStats(
        lowest=round(lowest, 2),
        highest=round(highest, 2),
        average=round(average, 2),
        current=round(current, 2),
        change_from_start=round(change_from_start, 2),
        trend=trend
    )

    return WeightHistory(logs=logs, stats=stats)


@router.get("/latest", response_model=WeightLogSchema)
def get_latest_weight(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the most recent weight log."""
    log = db.query(WeightLog).filter(
        WeightLog.user_id == current_user.id
    ).order_by(WeightLog.date.desc()).first()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No weight logs found"
        )

    return log


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_weight_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a weight log."""
    log = db.query(WeightLog).filter(
        WeightLog.id == log_id,
        WeightLog.user_id == current_user.id
    ).first()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weight log not found"
        )

    db.delete(log)
    db.commit()

    return None
