from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from datetime import date as date_type
from app.database import get_db
from app.models.user import User
from app.models.food import FoodItem
from app.models.food_log import FoodLog
from app.schemas.food import (
    FoodItem as FoodItemSchema,
    FoodItemCreate,
    FoodSearch,
    BarcodeSearch,
    FoodWeightOCRResponse
)
from app.schemas.food_log import (
    FoodLog as FoodLogSchema,
    FoodLogCreate,
    FoodLogWithDetails
)
from app.api.deps import get_current_user
from app.services.openfoodfacts import search_food_by_barcode, search_food_by_name
from app.services.gemini import extract_food_weight_from_image

router = APIRouter()


@router.post("/search", response_model=List[FoodItemSchema])
def search_food(
    search: FoodSearch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search for food items by name."""
    # First search local database
    local_results = db.query(FoodItem).filter(
        FoodItem.name.ilike(f"%{search.query}%")
    ).limit(10).all()

    # If not enough local results, search OpenFoodFacts
    if len(local_results) < 5:
        off_results = search_food_by_name(search.query, limit=10)

        # Add OpenFoodFacts results to database
        for item in off_results:
            # Check if already exists
            existing = db.query(FoodItem).filter(
                FoodItem.barcode == item["barcode"]
            ).first()

            if not existing and item["barcode"]:
                new_food = FoodItem(**item)
                db.add(new_food)
                local_results.append(new_food)

        db.commit()

    return local_results


@router.post("/barcode", response_model=FoodItemSchema)
def search_by_barcode(
    search: BarcodeSearch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search for food item by barcode."""
    # First check local database
    food_item = db.query(FoodItem).filter(FoodItem.barcode == search.barcode).first()

    if food_item:
        return food_item

    # Search OpenFoodFacts
    off_result = search_food_by_barcode(search.barcode)

    if not off_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Add to database
    new_food = FoodItem(**off_result)
    db.add(new_food)
    db.commit()
    db.refresh(new_food)

    return new_food


@router.post("/manual", response_model=FoodItemSchema, status_code=status.HTTP_201_CREATED)
def create_food_manual(
    food: FoodItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually create a food item."""
    new_food = FoodItem(**food.dict())
    db.add(new_food)
    db.commit()
    db.refresh(new_food)

    return new_food


@router.post("/ocr-weight", response_model=FoodWeightOCRResponse)
async def extract_food_weight(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Extract food weight from kitchen scale image using OCR."""
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )

    # Read image bytes
    image_bytes = await file.read()

    # Extract weight using Gemini Vision
    weight, confidence, message = extract_food_weight_from_image(image_bytes)

    if weight is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return FoodWeightOCRResponse(
        weight_grams=weight,
        confidence=confidence,
        message=message
    )


@router.post("/log", response_model=FoodLogSchema, status_code=status.HTTP_201_CREATED)
def log_food(
    food_log: FoodLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Log a food item."""
    # Get food item
    food_item = db.query(FoodItem).filter(FoodItem.id == food_log.food_id).first()

    if not food_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food item not found"
        )

    # Calculate calories
    calories = (food_item.calories_per_100g * food_log.weight_grams) / 100

    # Create food log
    new_log = FoodLog(
        user_id=current_user.id,
        food_id=food_log.food_id,
        weight_grams=food_log.weight_grams,
        calories=calories,
        date=food_log.date or date_type.today(),
        weight_method=food_log.weight_method
    )

    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    return new_log


@router.get("/logs", response_model=List[FoodLogWithDetails])
def get_food_logs(
    date: date_type = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get food logs for a specific date (default: today)."""
    if date is None:
        date = date_type.today()

    logs = db.query(FoodLog).filter(
        FoodLog.user_id == current_user.id,
        FoodLog.date == date
    ).all()

    # Enrich with food details
    result = []
    for log in logs:
        food_item = db.query(FoodItem).filter(FoodItem.id == log.food_id).first()
        if food_item:
            # Calculate macros for actual weight
            weight_ratio = log.weight_grams / 100
            result.append(FoodLogWithDetails(
                id=log.id,
                user_id=log.user_id,
                food_id=log.food_id,
                weight_grams=log.weight_grams,
                calories=log.calories,
                date=log.date,
                weight_method=log.weight_method,
                food_name=food_item.name,
                protein=food_item.protein * weight_ratio,
                carbs=food_item.carbs * weight_ratio,
                fat=food_item.fat * weight_ratio
            ))

    return result


@router.delete("/log/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_food_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a food log."""
    log = db.query(FoodLog).filter(
        FoodLog.id == log_id,
        FoodLog.user_id == current_user.id
    ).first()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food log not found"
        )

    db.delete(log)
    db.commit()

    return None
