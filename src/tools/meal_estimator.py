from pydantic import BaseModel, Field

from agno.agent import Agent
from agno.models.openai import OpenAIChat


class MealEstimate(BaseModel):
    calories: int = Field(..., description="Calorias estimadas")
    protein_g: float = Field(..., description="Proteina en gramos")
    carbs_g: float = Field(..., description="Carbohidratos en gramos")
    fat_g: float = Field(..., description="Grasa en gramos")
    meal_type: str | None = Field(None, description="Tipo de comida")
    prep_time_mins: int | None = Field(None, description="Tiempo de preparacion")


_estimator = Agent(
    name="Estimador de Comidas",
    model=OpenAIChat(id="gpt-5.2"),
    output_schema=MealEstimate,
    markdown=False,
    instructions="""
Estima macros y tipo de comida segun nombre, descripcion e ingredientes.
Responde con JSON valido segun el esquema.
Usa meal_type en: desayuno, almuerzo, cena, snack.
Si no sabes el tiempo de preparacion, deja prep_time_mins en null.
""",
)


def estimate_meal_fields(name: str, description: str, ingredients: list[str]) -> MealEstimate:
    prompt = (
        "Nombre: " + name + "\n"
        "Descripcion: " + description + "\n"
        "Ingredientes: " + ", ".join(ingredients)
    )
    return _estimator.run(prompt).content
