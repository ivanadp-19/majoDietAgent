import json

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from src.db.queries import search_meals
from src.db.supabase_client import get_supabase_client


def buscar_comidas(
    debe_incluir: list[str] | None = None,
    excluir: list[str] | None = None,
    max_calorias: int | None = None,
    min_proteina: float | None = None,
    tipo_comida: str | None = None,
    limite: int = 10,
) -> str:
    """
    Buscar comidas en la base de datos.
    """
    meals = search_meals(
        must_include=debe_incluir,
        exclude=excluir,
        max_calories=max_calorias,
        min_protein=min_proteina,
        meal_type=tipo_comida,
        limit=limite,
    )

    simplified = []
    for meal in meals:
        ingredients = [
            mi["ingredients"]["canonical_name"]
            for mi in meal.get("meal_ingredients", [])
            if mi.get("ingredients")
        ]
        simplified.append(
            {
                "id": meal["id"],
                "nombre": meal["name"],
                "tipo": meal["meal_type"],
                "calorias": meal["calories"],
                "proteina_g": meal["protein_g"],
                "carbohidratos_g": meal["carbs_g"],
                "grasa_g": meal["fat_g"],
                "ingredientes": ingredients,
                "etiquetas": meal.get("tags", []),
            }
        )

    return json.dumps(simplified, indent=2)


def listar_ingredientes_disponibles() -> str:
    """
    Lista todos los ingredientes disponibles en la base de datos.
    """
    supabase = get_supabase_client()
    result = supabase.table("ingredients").select("canonical_name").execute()
    ingredients = [row["canonical_name"] for row in result.data]
    return json.dumps(ingredients, indent=2)


diet_planner = Agent(
    name="Planificador de Dietas",
    model=OpenAIChat(id="gpt-5.2"),
    tools=[buscar_comidas, listar_ingredientes_disponibles],
    instructions="""
Eres un nutricionista experto y planificador de dietas. Tu trabajo es ayudar a los usuarios a crear planes de alimentacion balanceados basados en sus objetivos y preferencias.

## TU PROCESO

1. Entender los objetivos del usuario:
   - Bajar de peso? Ganar musculo? Mantenerse?
   - Cuantas calorias diarias necesita?
   - Restricciones alimentarias? (vegetariano, sin gluten, sin lactosa, etc.)
   - Preferencias de ingredientes?

2. Buscar comidas apropiadas:
   - Usa la herramienta buscar_comidas para encontrar opciones
   - Filtra por tipo de comida, calorias, proteina, ingredientes

3. Crear un plan balanceado:
   - Distribuye las calorias a lo largo del dia
   - Balancea los macronutrientes
   - Asegura variedad en las comidas

## DISTRIBUCION DE MACROS TIPICA

Objetivo | Proteina | Carbohidratos | Grasa
Bajar de peso | 40% | 30% | 30%
Ganar musculo | 30% | 45% | 25%
Mantenimiento | 25% | 50% | 25%

## DISTRIBUCION CALORICA DIARIA

- Desayuno: 25% de las calorias
- Almuerzo: 35% de las calorias
- Cena: 30% de las calorias
- Snacks: 10% de las calorias

## FORMATO DE RESPUESTA

Cuando presentes un plan de dieta, usa este formato:

Plan de alimentacion para [Objetivo]

Calorias diarias: X kcal
Distribucion de macros: X% proteina, X% carbohidratos, X% grasa

Desayuno (~X kcal)
- [Nombre de la comida]
- Macros: Xg proteina, Xg carbos, Xg grasa

Almuerzo (~X kcal)
- [Nombre de la comida]
- Macros: Xg proteina, Xg carbos, Xg grasa

Cena (~X kcal)
- [Nombre de la comida]
- Macros: Xg proteina, Xg carbos, Xg grasa

Snack (~X kcal)
- [Nombre de la comida]

Total del dia: X kcal | Xg proteina | Xg carbos | Xg grasa

## IMPORTANTE

- SIEMPRE busca primero en la base de datos antes de recomendar
- Si no encuentras suficientes opciones, dile al usuario que tipo de comidas faltan
- Se amigable y motivador
- Responde SIEMPRE en espanol
""",
    markdown=True,
)
