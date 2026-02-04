import json

import openai
from agno.workflow import StepInput, StepOutput

from src.config import EMBEDDING_MODEL, OPENAI_API_KEY
from src.db.queries import check_meal_exists, save_meal
from src.schemas.meal import ExtractedMeal, ExtractedMealsResponse

if OPENAI_API_KEY is None:
    raise ValueError("OPENAI_API_KEY is required")

openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)


def generate_embedding(meal: ExtractedMeal) -> list[float]:
    """Generate embedding for a meal using Spanish text."""
    ingredient_names = [item.name for item in meal.ingredients]
    embedding_text = (
        f"{meal.name}. {meal.description}\n"
        f"Tipo: {meal.meal_type.value}\n"
        f"Ingredientes: {', '.join(ingredient_names)}\n"
        f"Etiquetas: {', '.join(meal.tags)}\n"
        f"Calorias: {meal.calories}, Proteina: {meal.protein_g}g, "
        f"Carbohidratos: {meal.carbs_g}g, Grasa: {meal.fat_g}g"
    )

    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=embedding_text,
    )
    return response.data[0].embedding


def save_meals_to_db(step_input: StepInput) -> StepOutput:
    """
    Paso 3: Generar embeddings y guardar comidas en Supabase.
    """
    try:
        previous_content = step_input.previous_step_content

        if isinstance(previous_content, str):
            data = json.loads(previous_content)
            meals_response = ExtractedMealsResponse(**data)
        elif isinstance(previous_content, ExtractedMealsResponse):
            meals_response = previous_content
        else:
            meals_response = ExtractedMealsResponse(**previous_content)

        source_doc = step_input.additional_data.get("file_path", "desconocido")

        saved_meals = []
        skipped_meals = []
        errors = []

        for meal in meals_response.meals:
            try:
                if check_meal_exists(meal.name):
                    skipped_meals.append(meal.name)
                    continue

                embedding = generate_embedding(meal)

                meal_id = save_meal(
                    meal=meal,
                    embedding=embedding,
                    source_document=source_doc,
                )

                saved_meals.append(
                    {
                        "id": meal_id,
                        "name": meal.name,
                    "ingredients_count": len(meal.ingredients),
                    }
                )
            except Exception as exc:
                errors.append(f"{meal.name}: {exc}")

        summary_lines = [
            "Extraccion completada",
            f"Guardadas: {len(saved_meals)} comidas",
            f"Omitidas (duplicados): {len(skipped_meals)} comidas",
            f"Errores: {len(errors)}",
            "",
            "Comidas guardadas:",
        ]
        summary_lines.extend(
            [
                f"- {m['name']} (ID: {m['id']}, {m['ingredients_count']} ingredientes)"
                for m in saved_meals
            ]
        )

        if skipped_meals:
            summary_lines.append("")
            summary_lines.append("Omitidas (ya existen):")
            summary_lines.extend([f"- {name}" for name in skipped_meals])

        if errors:
            summary_lines.append("")
            summary_lines.append("Errores:")
            summary_lines.extend([f"- {err}" for err in errors])

        return StepOutput(content="\n".join(summary_lines))
    except Exception as exc:
        return StepOutput(
            content=f"Error guardando comidas: {exc}",
            success=False,
        )
