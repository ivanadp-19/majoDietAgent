from typing import Optional

from pydantic import BaseModel, Field


class IngredientInput(BaseModel):
    name: str = Field(..., description="Nombre canonico del ingrediente")
    quantity: Optional[float] = Field(None, description="Cantidad")
    unit: Optional[str] = Field(None, description="Unidad")


class MealCreate(BaseModel):
    name: str
    description: Optional[str] = None
    meal_type: Optional[str] = None
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    prep_time_mins: Optional[int] = None
    servings: Optional[int] = 1
    tags: list[str] = Field(default_factory=list)
    ingredients: list[IngredientInput] = Field(default_factory=list)


class MealUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    meal_type: Optional[str] = None
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    prep_time_mins: Optional[int] = None
    servings: Optional[int] = None
    tags: Optional[list[str]] = None
    ingredients: Optional[list[IngredientInput]] = None


class MealResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    meal_type: Optional[str] = None
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    prep_time_mins: Optional[int] = None
    servings: Optional[int] = None
    tags: list[str] = Field(default_factory=list)
    ingredients: list[str] = Field(default_factory=list)


class MealsListResponse(BaseModel):
    items: list[MealResponse]
    next_cursor: Optional[int] = None


class MealsSearchRequest(BaseModel):
    must_include: Optional[list[str]] = None
    exclude: Optional[list[str]] = None
    max_calories: Optional[int] = None
    min_protein: Optional[float] = None
    meal_type: Optional[str] = None
    limit: int = 10
    cursor: Optional[int] = None
    q: Optional[str] = None


class IngestResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    summary: Optional[str] = None
    error: Optional[str] = None
