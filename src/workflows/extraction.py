from agno.workflow import Step, Workflow

from src.steps.extract_meals import meal_extractor
from src.steps.save_to_db import save_meals_to_db

extract_meals_step = Step(
    name="extract_meals",
    description="Extraer comidas desde un documento",
    agent=meal_extractor,
)

save_meals_step = Step(
    name="save_meals",
    description="Guardar comidas en Supabase",
    executor=save_meals_to_db,
)

meal_extraction_workflow = Workflow(
    name="meal_extraction_workflow",
    steps=[extract_meals_step, save_meals_step],
)
