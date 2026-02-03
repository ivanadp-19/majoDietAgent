from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Sex(str, Enum):
    MALE = "masculino"
    FEMALE = "femenino"


class Objective(str, Enum):
    LOSE_WEIGHT = "bajar_peso"
    GAIN_WEIGHT = "subir_peso"
    MAINTAIN = "mantener"
    GAIN_MUSCLE = "ganar_musculo"


class ActivityLevel(str, Enum):
    SEDENTARY = "sedentario"
    LIGHT = "ligero"
    MODERATE = "moderado"
    ACTIVE = "activo"
    VERY_ACTIVE = "muy_activo"


class PatientData(BaseModel):
    """Datos del paciente."""

    nombre: str
    edad: int
    sexo: Sex
    peso_kg: float
    altura_cm: float
    objetivo: Objective
    nivel_actividad: ActivityLevel = ActivityLevel.SEDENTARY
    condiciones: list[str] = Field(default_factory=list)
    alergias: list[str] = Field(default_factory=list)
    restricciones: list[str] = Field(default_factory=list)
    preferencias: list[str] = Field(default_factory=list)


class NutritionalRequirements(BaseModel):
    """Requerimientos nutricionales calculados."""

    tmb: float
    tdee: float
    calorias_objetivo: int
    proteina_g: int
    carbohidratos_g: int
    grasa_g: int
    fibra_g: int
    notas: list[str] = Field(default_factory=list)


class MealSlot(BaseModel):
    """Una comida en el plan."""

    meal_id: Optional[int] = None
    nombre: str
    tipo: str
    calorias: int
    proteina_g: float
    carbohidratos_g: float
    grasa_g: float
    ingredientes: list[str] = Field(default_factory=list)


class DayPlan(BaseModel):
    """Plan de un dia."""

    dia: str
    comidas: list[MealSlot]
    total_calorias: int = 0
    total_proteina: float = 0
    total_carbohidratos: float = 0
    total_grasa: float = 0


class WeeklyPlan(BaseModel):
    """Plan semanal completo."""

    paciente: str
    objetivo: str
    requerimientos: NutritionalRequirements
    dias: list[DayPlan]
