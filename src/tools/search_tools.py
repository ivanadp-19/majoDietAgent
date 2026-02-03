import json

from src.db.queries import search_meals
from src.db.supabase_client import get_supabase_client


def buscar_comidas(
    tipo_comida: str | None = None,
    max_calorias: int | None = None,
    min_calorias: int | None = None,
    min_proteina: float | None = None,
    max_carbohidratos: float | None = None,
    debe_incluir: list[str] | None = None,
    excluir: list[str] | None = None,
    tags: list[str] | None = None,
    limite: int = 5,
) -> str:
    """
    Busca comidas en la base de datos segun criterios especificos.
    """
    meals = search_meals(
        must_include=debe_incluir,
        exclude=excluir,
        max_calories=max_calorias,
        min_protein=min_proteina,
        meal_type=tipo_comida,
        limit=limite * 2,
    )

    if min_calorias:
        meals = [meal for meal in meals if meal.get("calories", 0) >= min_calorias]

    if max_carbohidratos:
        meals = [meal for meal in meals if meal.get("carbs_g", 0) <= max_carbohidratos]

    if tags:
        tags_lower = [tag.lower() for tag in tags]
        meals = [
            meal
            for meal in meals
            if any(tag in [t.lower() for t in meal.get("tags", [])] for tag in tags_lower)
        ]

    meals = meals[:limite]

    results = []
    for meal in meals:
        ingredients = [
            mi["ingredients"]["canonical_name"]
            for mi in meal.get("meal_ingredients", [])
            if mi.get("ingredients")
        ]
        results.append(
            {
                "id": meal["id"],
                "nombre": meal["name"],
                "descripcion": meal.get("description", ""),
                "tipo": meal["meal_type"],
                "calorias": meal["calories"],
                "proteina_g": float(meal["protein_g"]) if meal["protein_g"] else 0,
                "carbohidratos_g": float(meal["carbs_g"]) if meal["carbs_g"] else 0,
                "grasa_g": float(meal["fat_g"]) if meal["fat_g"] else 0,
                "ingredientes": ingredients,
                "etiquetas": meal.get("tags", []),
            }
        )

    if not results:
        return json.dumps(
            {
                "mensaje": "No se encontraron comidas con esos criterios. Intenta con filtros menos restrictivos.",
                "comidas": [],
            }
        )

    return json.dumps({"comidas": results}, indent=2)


def obtener_detalle_comida(meal_id: int) -> str:
    """
    Obtiene los detalles completos de una comida especifica.
    """
    supabase = get_supabase_client()
    result = (
        supabase.table("meals")
        .select("*, meal_ingredients(quantity, unit, ingredients(canonical_name))")
        .eq("id", meal_id)
        .execute()
    )

    if not result.data:
        return json.dumps({"error": "Comida no encontrada"})

    meal = result.data[0]
    ingredients = [
        {
            "nombre": mi["ingredients"]["canonical_name"],
            "cantidad": mi.get("quantity"),
            "unidad": mi.get("unit"),
        }
        for mi in meal.get("meal_ingredients", [])
        if mi.get("ingredients")
    ]

    return json.dumps(
        {
            "id": meal["id"],
            "nombre": meal["name"],
            "descripcion": meal.get("description"),
            "tipo": meal["meal_type"],
            "calorias": meal["calories"],
            "proteina_g": float(meal["protein_g"]) if meal["protein_g"] else 0,
            "carbohidratos_g": float(meal["carbs_g"]) if meal["carbs_g"] else 0,
            "grasa_g": float(meal["fat_g"]) if meal["fat_g"] else 0,
            "fibra_g": float(meal["fiber_g"]) if meal.get("fiber_g") else 0,
            "tiempo_preparacion_mins": meal.get("prep_time_mins"),
            "porciones": meal.get("servings", 1),
            "ingredientes": ingredients,
            "etiquetas": meal.get("tags", []),
        },
        indent=2,
    )


def listar_ingredientes_disponibles() -> str:
    """
    Lista todos los ingredientes disponibles en la base de datos.
    """
    supabase = get_supabase_client()
    result = (
        supabase.table("ingredients")
        .select("canonical_name")
        .order("canonical_name")
        .execute()
    )
    ingredients = [row["canonical_name"] for row in result.data]
    return json.dumps({"ingredientes": ingredients})


def contar_comidas_por_tipo() -> str:
    """
    Cuenta cuantas comidas hay de cada tipo en la base de datos.
    """
    supabase = get_supabase_client()
    counts = {}
    for tipo in ["desayuno", "almuerzo", "cena", "snack"]:
        result = supabase.table("meals").select("id", count="exact").eq("meal_type", tipo).execute()
        counts[tipo] = result.count
    return json.dumps({"conteo_por_tipo": counts})
