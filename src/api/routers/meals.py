from fastapi import APIRouter, BackgroundTasks, HTTPException

from src.api.schemas import (
    MealCreate,
    MealResponse,
    MealUpdate,
    MealsListResponse,
    MealsSearchRequest,
)
from src.db.queries import create_meal, delete_meal, get_meal_by_id, search_meals, update_meal
from src.tools.meal_estimator import estimate_meal_fields

router = APIRouter()


def _meal_to_response(meal: dict) -> MealResponse:
    ingredients = [
        mi["ingredients"]["canonical_name"]
        for mi in meal.get("meal_ingredients", [])
        if mi.get("ingredients")
    ]
    return MealResponse(
        id=meal["id"],
        name=meal["name"],
        description=meal.get("description"),
        meal_type=meal.get("meal_type"),
        calories=meal.get("calories"),
        protein_g=meal.get("protein_g"),
        carbs_g=meal.get("carbs_g"),
        fat_g=meal.get("fat_g"),
        fiber_g=meal.get("fiber_g"),
        prep_time_mins=meal.get("prep_time_mins"),
        servings=meal.get("servings"),
        tags=meal.get("tags", []),
        ingredients=ingredients,
    )


@router.post("", response_model=MealResponse)
def create_meal_endpoint(
    payload: MealCreate, background_tasks: BackgroundTasks
) -> MealResponse:
    meal_data = payload.model_dump(exclude={"ingredients"})
    ingredient_entries = [
        {"name": item.name, "quantity": item.quantity, "unit": item.unit}
        for item in payload.ingredients
    ]
    meal_id = create_meal(meal_data, ingredient_entries)
    meal = get_meal_by_id(meal_id)
    if not meal:
        raise HTTPException(status_code=500, detail="Meal creation failed")

    missing_fields = [
        key
        for key in ["calories", "protein_g", "carbs_g", "fat_g", "meal_type", "prep_time_mins"]
        if meal.get(key) is None
    ]
    if missing_fields:
        background_tasks.add_task(
            _estimate_and_update_meal,
            meal_id,
            meal.get("name"),
            meal.get("description"),
            [item.name for item in payload.ingredients],
            missing_fields,
        )

    return _meal_to_response(meal)


@router.get("/{meal_id}", response_model=MealResponse)
def get_meal_endpoint(meal_id: int) -> MealResponse:
    meal = get_meal_by_id(meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    return _meal_to_response(meal)


@router.get("", response_model=MealsListResponse)
def list_meals_endpoint(
    must_include: list[str] | None = None,
    exclude: list[str] | None = None,
    max_calories: int | None = None,
    min_protein: float | None = None,
    meal_type: str | None = None,
    limit: int = 10,
    cursor: int | None = None,
    q: str | None = None,
) -> MealsListResponse:
    meals = search_meals(
        must_include=must_include,
        exclude=exclude,
        max_calories=max_calories,
        min_protein=min_protein,
        meal_type=meal_type,
        limit=limit,
        cursor=cursor,
        name_query=q,
    )
    items = [_meal_to_response(meal) for meal in meals]
    next_cursor = items[-1].id if items else None
    return MealsListResponse(items=items, next_cursor=next_cursor)


@router.get("/search", response_model=MealsListResponse)
def search_meals_endpoint(
    must_include: list[str] | None = None,
    exclude: list[str] | None = None,
    max_calories: int | None = None,
    min_protein: float | None = None,
    meal_type: str | None = None,
    limit: int = 10,
    cursor: int | None = None,
    q: str | None = None,
) -> MealsListResponse:
    meals = search_meals(
        must_include=must_include,
        exclude=exclude,
        max_calories=max_calories,
        min_protein=min_protein,
        meal_type=meal_type,
        limit=limit,
        cursor=cursor,
        name_query=q,
    )
    items = [_meal_to_response(meal) for meal in meals]
    next_cursor = items[-1].id if items else None
    return MealsListResponse(items=items, next_cursor=next_cursor)


@router.post("/search", response_model=MealsListResponse)
def search_meals_post(payload: MealsSearchRequest) -> MealsListResponse:
    meals = search_meals(
        must_include=payload.must_include,
        exclude=payload.exclude,
        max_calories=payload.max_calories,
        min_protein=payload.min_protein,
        meal_type=payload.meal_type,
        limit=payload.limit,
        cursor=payload.cursor,
        name_query=payload.q,
    )
    items = [_meal_to_response(meal) for meal in meals]
    next_cursor = items[-1].id if items else None
    return MealsListResponse(items=items, next_cursor=next_cursor)


def _estimate_and_update_meal(
    meal_id: int,
    name: str | None,
    description: str | None,
    ingredients: list[str],
    missing_fields: list[str],
) -> None:
    estimate = estimate_meal_fields(
        name=name or "",
        description=description or "",
        ingredients=ingredients,
    )
    update_data: dict[str, object] = {}
    if "calories" in missing_fields:
        update_data["calories"] = estimate.calories
    if "protein_g" in missing_fields:
        update_data["protein_g"] = estimate.protein_g
    if "carbs_g" in missing_fields:
        update_data["carbs_g"] = estimate.carbs_g
    if "fat_g" in missing_fields:
        update_data["fat_g"] = estimate.fat_g
    if "meal_type" in missing_fields and estimate.meal_type:
        update_data["meal_type"] = estimate.meal_type
    if "prep_time_mins" in missing_fields and estimate.prep_time_mins:
        update_data["prep_time_mins"] = estimate.prep_time_mins

    if update_data:
        update_meal(meal_id, update_data, ingredient_names=None)


@router.put("/{meal_id}", response_model=MealResponse)
def update_meal_endpoint(meal_id: int, payload: MealUpdate) -> MealResponse:
    existing = get_meal_by_id(meal_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Meal not found")

    meal_data = payload.model_dump(exclude_unset=True, exclude={"ingredients"})
    ingredient_names = None
    if payload.ingredients is not None:
        ingredient_names = [
            {"name": item.name, "quantity": item.quantity, "unit": item.unit}
            for item in payload.ingredients
        ]

    update_meal(meal_id, meal_data, ingredient_names)
    updated = get_meal_by_id(meal_id)
    if not updated:
        raise HTTPException(status_code=500, detail="Meal update failed")
    return _meal_to_response(updated)


@router.delete("/{meal_id}")
def delete_meal_endpoint(meal_id: int) -> dict:
    existing = get_meal_by_id(meal_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Meal not found")
    delete_meal(meal_id)
    return {"status": "deleted", "meal_id": meal_id}
