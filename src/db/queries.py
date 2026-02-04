from typing import Iterable
import re
import unicodedata

from src.db.supabase_client import get_supabase_client
from src.schemas.meal import ExtractedMeal


def check_meal_exists(name: str) -> bool:
    supabase = get_supabase_client()
    result = supabase.table("meals").select("id").eq("name", name).limit(1).execute()
    return bool(result.data)


def _get_or_create_ingredient(canonical_name: str) -> int:
    supabase = get_supabase_client()
    normalized_name = _normalize_ingredient_name(canonical_name)
    existing = (
        supabase.table("ingredients")
        .select("id")
        .eq("canonical_name", normalized_name)
        .limit(1)
        .execute()
    )
    if existing.data:
        return existing.data[0]["id"]

    created = (
        supabase.table("ingredients")
        .insert({"canonical_name": normalized_name})
        .execute()
    )
    return created.data[0]["id"]


INGREDIENT_ALIASES = {
    "pechuga de pollo sin piel": "pollo",
    "pechuga de pollo": "pollo",
    "pollo asado": "pollo",
    "arroz integral": "arroz",
    "arroz blanco": "arroz",
    "cebolla morada": "cebolla",
    "cebolla morada picada": "cebolla",
    "aceite de oliva extra virgen": "aceite de oliva",
    "leche descremada": "leche",
    "leche light": "leche",
    "queso parmesano rallado": "queso parmesano",
    "tomates cherry": "tomate",
    "aguacate maduro": "aguacate",
    "frijoles negros enlatados": "frijoles negros",
}


def _normalize_ingredient_name(value: str) -> str:
    normalized = value.strip().lower()
    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = re.sub(r"\s+", " ", normalized)
    return INGREDIENT_ALIASES.get(normalized, normalized)


def save_meal(meal: ExtractedMeal, embedding: list[float], source_document: str) -> int:
    supabase = get_supabase_client()
    meal_insert = (
        supabase.table("meals")
        .insert(
            {
                "name": meal.name,
                "description": meal.description,
                "meal_type": meal.meal_type.value,
                "calories": meal.calories,
                "protein_g": meal.protein_g,
                "carbs_g": meal.carbs_g,
                "fat_g": meal.fat_g,
                "fiber_g": meal.fiber_g,
                "prep_time_mins": meal.prep_time_mins,
                "tags": meal.tags,
                "source_document": source_document,
                "embedding": embedding,
            }
        )
        .execute()
    )
    meal_id = meal_insert.data[0]["id"]

    for ingredient in meal.ingredients:
        ingredient_id = _get_or_create_ingredient(ingredient.name)
        quantity = ingredient.quantity
        unit = ingredient.unit
        supabase.table("meal_ingredients").insert(
            {
                "meal_id": meal_id,
                "ingredient_id": ingredient_id,
                "quantity": quantity,
                "unit": unit,
            }
        ).execute()

    return meal_id


def get_meal_by_id(meal_id: int) -> dict | None:
    supabase = get_supabase_client()
    result = (
        supabase.table("meals")
        .select("*, meal_ingredients(quantity, unit, ingredients(canonical_name))")
        .eq("id", meal_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def create_meal(meal_data: dict, ingredient_entries: list[dict]) -> int:
    supabase = get_supabase_client()
    result = supabase.table("meals").insert(meal_data).execute()
    meal_id = result.data[0]["id"]

    for ingredient in ingredient_entries:
        ingredient_id = _get_or_create_ingredient(ingredient["name"])
        quantity = ingredient.get("quantity")
        unit = ingredient.get("unit")
        supabase.table("meal_ingredients").insert(
            {
                "meal_id": meal_id,
                "ingredient_id": ingredient_id,
                "quantity": quantity,
                "unit": unit,
            }
        ).execute()

    return meal_id


def update_meal(
    meal_id: int,
    meal_data: dict,
    ingredient_entries: list[dict] | None = None,
) -> None:
    supabase = get_supabase_client()
    if meal_data:
        supabase.table("meals").update(meal_data).eq("id", meal_id).execute()

    if ingredient_entries is not None:
        supabase.table("meal_ingredients").delete().eq("meal_id", meal_id).execute()
        for ingredient in ingredient_entries:
            ingredient_id = _get_or_create_ingredient(ingredient["name"])
            quantity = ingredient.get("quantity")
            unit = ingredient.get("unit")
            supabase.table("meal_ingredients").insert(
                {
                    "meal_id": meal_id,
                    "ingredient_id": ingredient_id,
                    "quantity": quantity,
                    "unit": unit,
                }
            ).execute()


def delete_meal(meal_id: int) -> None:
    supabase = get_supabase_client()
    supabase.table("meals").delete().eq("id", meal_id).execute()


def _filter_by_ingredients(
    meals: Iterable[dict],
    must_include: list[str] | None,
    exclude: list[str] | None,
) -> list[dict]:
    if not must_include and not exclude:
        return list(meals)

    must_include_set = {_normalize_ingredient_name(i) for i in must_include or []}
    exclude_set = {_normalize_ingredient_name(i) for i in exclude or []}

    filtered = []
    for meal in meals:
        ingredients = [
            _normalize_ingredient_name(mi["ingredients"]["canonical_name"])
            for mi in meal.get("meal_ingredients", [])
            if mi.get("ingredients")
        ]
        ingredient_set = set(ingredients)
        if must_include_set and not must_include_set.issubset(ingredient_set):
            continue
        if exclude_set and exclude_set.intersection(ingredient_set):
            continue
        filtered.append(meal)
    return filtered


def search_meals(
    must_include: list[str] | None = None,
    exclude: list[str] | None = None,
    max_calories: int | None = None,
    min_protein: float | None = None,
    meal_type: str | None = None,
    limit: int = 10,
    cursor: int | None = None,
    name_query: str | None = None,
) -> list[dict]:
    supabase = get_supabase_client()
    query = supabase.table("meals").select(
        "*, meal_ingredients(quantity, unit, ingredients(canonical_name))"
    )

    if cursor is not None:
        query = query.gt("id", cursor)
    if name_query:
        query = query.ilike("name", f"%{name_query}%")
    if meal_type:
        query = query.eq("meal_type", meal_type)
    if max_calories is not None:
        query = query.lte("calories", max_calories)
    if min_protein is not None:
        query = query.gte("protein_g", min_protein)

    result = query.order("id", desc=False).limit(limit * 5).execute()
    filtered = _filter_by_ingredients(result.data or [], must_include, exclude)
    return filtered[:limit]
