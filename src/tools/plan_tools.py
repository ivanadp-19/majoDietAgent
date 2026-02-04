import json
from typing import Dict, List

from src.db.queries import search_meals
from src.schemas.patient import WeeklyPlan


DAY_NAMES = [
    "Lunes",
    "Martes",
    "Miercoles",
    "Jueves",
    "Viernes",
    "Sabado",
    "Domingo",
]


def _select_meal(
    meals: list[dict],
    used_counts: Dict[str, int],
    max_repeats: int = 2,
) -> dict | None:
    def meal_key(item: dict) -> str:
        name = (item.get("name") or "").strip().lower()
        meal_type = (item.get("meal_type") or "").strip().lower()
        return f"{meal_type}:{name}"

    sorted_meals = sorted(meals, key=lambda m: used_counts.get(meal_key(m), 0))
    for meal in sorted_meals:
        key = meal_key(meal)
        if used_counts.get(key, 0) < max_repeats:
            used_counts[key] = used_counts.get(key, 0) + 1
            return meal
    return None


def generar_plan_semanal(
    calorias_objetivo: int,
    restricciones: list[str] | None = None,
    preferencias: list[str] | None = None,
    paciente: str = "Paciente",
    objetivo: str = "objetivo",
) -> str:
    """
    Genera un plan semanal simple usando comidas disponibles en la base.
    """
    restricciones = restricciones or []
    preferencias = preferencias or []

    distribucion = {
        "desayuno": int(calorias_objetivo * 0.25),
        "almuerzo": int(calorias_objetivo * 0.35),
        "cena": int(calorias_objetivo * 0.30),
        "snack": int(calorias_objetivo * 0.10),
    }

    used_counts: Dict[str, int] = {}
    dias = []

    for dia in DAY_NAMES:
        comidas = []
        total_calorias = 0
        total_proteina = 0.0
        total_carbohidratos = 0.0
        total_grasa = 0.0

        for tipo, kcal in distribucion.items():
            meals = search_meals(
                meal_type=tipo,
                max_calories=kcal + 150,
                exclude=restricciones,
                limit=25,
            )

            if preferencias:
                meals = [
                    meal
                    for meal in meals
                    if any(pref.lower() in [t.lower() for t in meal.get("tags", [])] for pref in preferencias)
                ]

            selected = _select_meal(meals, used_counts)
            if not selected:
                continue

            ingredients = [
                _format_ingredient(
                    mi["ingredients"]["canonical_name"],
                    mi.get("quantity"),
                    mi.get("unit"),
                )
                for mi in selected.get("meal_ingredients", [])
                if mi.get("ingredients")
            ]

            comidas.append(
                {
                    "meal_id": selected["id"],
                    "nombre": selected["name"],
                    "tipo": selected.get("meal_type"),
                    "calorias": selected.get("calories") or 0,
                    "proteina_g": float(selected.get("protein_g") or 0),
                    "carbohidratos_g": float(selected.get("carbs_g") or 0),
                    "grasa_g": float(selected.get("fat_g") or 0),
                    "ingredientes": ingredients,
                }
            )

            total_calorias += selected.get("calories") or 0
            total_proteina += float(selected.get("protein_g") or 0)
            total_carbohidratos += float(selected.get("carbs_g") or 0)
            total_grasa += float(selected.get("fat_g") or 0)

        dias.append(
            {
                "dia": dia,
                "comidas": comidas,
                "total_calorias": total_calorias,
                "total_proteina": round(total_proteina, 1),
                "total_carbohidratos": round(total_carbohidratos, 1),
                "total_grasa": round(total_grasa, 1),
            }
        )

    plan = WeeklyPlan(
        paciente=paciente,
        objetivo=objetivo,
        requerimientos={
            "tmb": 0,
            "tdee": 0,
            "calorias_objetivo": calorias_objetivo,
            "proteina_g": 0,
            "carbohidratos_g": 0,
            "grasa_g": 0,
            "fibra_g": 0,
            "notas": [],
        },
        dias=dias,
    )
    return plan.model_dump_json(indent=2)


def reemplazar_comida(
    plan_json: str,
    dia: str,
    tipo_comida: str,
    max_calorias: int | None = None,
    debe_incluir: list[str] | None = None,
    excluir: list[str] | None = None,
) -> str:
    """
    Reemplaza una comida especifica en un plan semanal.
    """
    plan = json.loads(plan_json)
    days = plan.get("dias", [])

    meals = search_meals(
        meal_type=tipo_comida,
        max_calories=max_calorias,
        must_include=debe_incluir,
        exclude=excluir,
        limit=10,
    )
    if not meals:
        return json.dumps({"error": "No se encontraron comidas alternativas"})

    selected = meals[0]
    ingredients = [
        _format_ingredient(
            mi["ingredients"]["canonical_name"],
            mi.get("quantity"),
            mi.get("unit"),
        )
        for mi in selected.get("meal_ingredients", [])
        if mi.get("ingredients")
    ]

    for day in days:
        if day.get("dia", "").lower() == dia.lower():
            for idx, slot in enumerate(day.get("comidas", [])):
                if slot.get("tipo") == tipo_comida:
                    day["comidas"][idx] = {
                        "meal_id": selected["id"],
                        "nombre": selected["name"],
                        "tipo": selected.get("meal_type"),
                        "calorias": selected.get("calories") or 0,
                        "proteina_g": float(selected.get("protein_g") or 0),
                        "carbohidratos_g": float(selected.get("carbs_g") or 0),
                        "grasa_g": float(selected.get("fat_g") or 0),
                        "ingredientes": ingredients,
                    }
            break

    plan["dias"] = days
    return json.dumps(plan, indent=2)


def _format_ingredient(name: str, quantity: float | None, unit: str | None) -> str:
    if quantity is None and not unit:
        return name
    if unit:
        return f"{name} ({quantity} {unit})" if quantity is not None else f"{name} ({unit})"
    return f"{name} ({quantity})"
