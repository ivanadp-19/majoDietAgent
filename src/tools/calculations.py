from src.schemas.patient import ActivityLevel, Objective, PatientData, Sex, NutritionalRequirements


ACTIVITY_MULTIPLIERS = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHT: 1.375,
    ActivityLevel.MODERATE: 1.55,
    ActivityLevel.ACTIVE: 1.725,
    ActivityLevel.VERY_ACTIVE: 1.9,
}

OBJECTIVE_ADJUSTMENTS = {
    Objective.LOSE_WEIGHT: -500,
    Objective.GAIN_WEIGHT: 300,
    Objective.MAINTAIN: 0,
    Objective.GAIN_MUSCLE: 200,
}


def calcular_requerimientos(patient: PatientData) -> NutritionalRequirements:
    """
    Calcula requerimientos nutricionales usando Mifflin-St Jeor.
    """
    notas = []

    if patient.sexo == Sex.MALE:
        tmb = (10 * patient.peso_kg) + (6.25 * patient.altura_cm) - (5 * patient.edad) + 5
    else:
        tmb = (10 * patient.peso_kg) + (6.25 * patient.altura_cm) - (5 * patient.edad) - 161

    tdee = tmb * ACTIVITY_MULTIPLIERS[patient.nivel_actividad]
    calorias_objetivo = tdee + OBJECTIVE_ADJUSTMENTS[patient.objetivo]

    condiciones_lower = [c.lower() for c in patient.condiciones]
    if "hipotiroidismo" in condiciones_lower:
        calorias_objetivo -= 100
        notas.append("Ajuste -100 kcal por hipotiroidismo")

    if "diabetes" in condiciones_lower or "resistencia a la insulina" in condiciones_lower:
        notas.append("Priorizar carbohidratos complejos, bajo indice glucemico")

    if "hipertension" in condiciones_lower:
        notas.append("Limitar sodio a <2000mg/dia")

    if "enfermedad renal" in condiciones_lower:
        notas.append("Moderar proteina segun indicacion medica")

    min_calorias = 1200 if patient.sexo == Sex.FEMALE else 1500
    if calorias_objetivo < min_calorias:
        calorias_objetivo = min_calorias
        notas.append(f"Ajustado al minimo saludable: {min_calorias} kcal")

    calorias_objetivo = int(calorias_objetivo)

    if patient.objetivo == Objective.LOSE_WEIGHT:
        proteina_pct, carbs_pct, grasa_pct = 0.35, 0.35, 0.30
    elif patient.objetivo == Objective.GAIN_MUSCLE:
        proteina_pct, carbs_pct, grasa_pct = 0.30, 0.45, 0.25
    elif patient.objetivo == Objective.GAIN_WEIGHT:
        proteina_pct, carbs_pct, grasa_pct = 0.25, 0.45, 0.30
    else:
        proteina_pct, carbs_pct, grasa_pct = 0.25, 0.50, 0.25

    proteina_g = int((calorias_objetivo * proteina_pct) / 4)
    carbohidratos_g = int((calorias_objetivo * carbs_pct) / 4)
    grasa_g = int((calorias_objetivo * grasa_pct) / 9)
    fibra_g = 25 if patient.sexo == Sex.FEMALE else 30

    return NutritionalRequirements(
        tmb=round(tmb, 1),
        tdee=round(tdee, 1),
        calorias_objetivo=calorias_objetivo,
        proteina_g=proteina_g,
        carbohidratos_g=carbohidratos_g,
        grasa_g=grasa_g,
        fibra_g=fibra_g,
        notas=notas,
    )


def calcular_imc(peso_kg: float, altura_cm: float) -> tuple[float, str]:
    """Calcula IMC y categoria."""
    altura_m = altura_cm / 100
    imc = peso_kg / (altura_m**2)

    if imc < 18.5:
        categoria = "Bajo peso"
    elif imc < 25:
        categoria = "Normal"
    elif imc < 30:
        categoria = "Sobrepeso"
    elif imc < 35:
        categoria = "Obesidad grado I"
    elif imc < 40:
        categoria = "Obesidad grado II"
    else:
        categoria = "Obesidad grado III"

    return round(imc, 1), categoria
