from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MealType(str, Enum):
    BREAKFAST = "desayuno"
    LUNCH = "almuerzo"
    DINNER = "cena"
    SNACK = "snack"


class ExtractedMeal(BaseModel):
    """Schema for a meal extracted from document."""

    name: str = Field(..., description="Nombre de la comida")
    description: str = Field(..., description="Descripcion breve de la comida")
    meal_type: MealType = Field(...)
    calories: int = Field(..., description="Calorias estimadas")
    protein_g: float = Field(..., description="Proteina en gramos")
    carbs_g: float = Field(..., description="Carbohidratos en gramos")
    fat_g: float = Field(..., description="Grasa en gramos")
    fiber_g: Optional[float] = Field(None, description="Fibra en gramos")
    ingredients: list[str] = Field(..., description="Lista de ingredientes")
    tags: list[str] = Field(
        default_factory=list,
        description="Etiquetas como 'vegano', 'alto-en-proteina'",
    )
    prep_time_mins: Optional[int] = Field(
        None, description="Tiempo de preparacion en minutos"
    )


class ExtractedMealsResponse(BaseModel):
    """Response schema for meal extraction."""

    meals: list[ExtractedMeal]
    extraction_notes: Optional[str] = Field(
        None, description="Notas sobre la extraccion"
    )
