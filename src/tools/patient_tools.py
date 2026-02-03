import json

from src.schemas.patient import ActivityLevel, Objective, PatientData, Sex
from src.tools.calculations import calcular_imc, calcular_requerimientos


def _normalize_value(value: str) -> str:
    normalized = value.strip().lower()
    normalized = normalized.replace("-", "_").replace(" ", "_")
    return normalized


def _normalize_sexo(value: str) -> Sex:
    normalized = _normalize_value(value)
    if normalized in {"masculino", "hombre", "male", "m"}:
        return Sex.MALE
    if normalized in {"femenino", "mujer", "female", "f"}:
        return Sex.FEMALE
    return Sex(normalized)


def _normalize_objetivo(value: str) -> Objective:
    normalized = _normalize_value(value)
    mapping = {
        "perder_peso": "bajar_peso",
        "bajar_peso": "bajar_peso",
        "bajar": "bajar_peso",
        "subir_peso": "subir_peso",
        "ganar_peso": "subir_peso",
        "mantener": "mantener",
        "mantenimiento": "mantener",
        "ganar_musculo": "ganar_musculo",
        "aumentar_musculo": "ganar_musculo",
        "ganar_masa_muscular": "ganar_musculo",
    }
    return Objective(mapping.get(normalized, normalized))


def _normalize_actividad(value: str) -> ActivityLevel:
    normalized = _normalize_value(value)
    mapping = {
        "sedentario": "sedentario",
        "ligero": "ligero",
        "moderado": "moderado",
        "activo": "activo",
        "muy_activo": "muy_activo",
        "muy_activa": "muy_activo",
        "very_active": "muy_activo",
    }
    return ActivityLevel(mapping.get(normalized, normalized))


def registrar_paciente(
    nombre: str,
    edad: int,
    sexo: str,
    peso_kg: float,
    altura_cm: float,
    objetivo: str,
    nivel_actividad: str = "sedentario",
    condiciones: list[str] | None = None,
    alergias: list[str] | None = None,
    restricciones: list[str] | None = None,
    preferencias: list[str] | None = None,
) -> str:
    """
    Registra los datos de un paciente y calcula sus requerimientos nutricionales.
    """
    patient = PatientData(
        nombre=nombre,
        edad=edad,
        sexo=_normalize_sexo(sexo),
        peso_kg=peso_kg,
        altura_cm=altura_cm,
        objetivo=_normalize_objetivo(objetivo),
        nivel_actividad=_normalize_actividad(nivel_actividad),
        condiciones=condiciones or [],
        alergias=alergias or [],
        restricciones=restricciones or [],
        preferencias=preferencias or [],
    )

    reqs = calcular_requerimientos(patient)
    imc, imc_categoria = calcular_imc(peso_kg, altura_cm)

    result = {
        "paciente": {
            "nombre": patient.nombre,
            "edad": patient.edad,
            "sexo": patient.sexo.value,
            "peso_kg": patient.peso_kg,
            "altura_cm": patient.altura_cm,
            "imc": imc,
            "imc_categoria": imc_categoria,
            "objetivo": patient.objetivo.value,
            "nivel_actividad": patient.nivel_actividad.value,
            "condiciones": patient.condiciones,
            "alergias": patient.alergias,
            "restricciones": patient.restricciones,
            "preferencias": patient.preferencias,
        },
        "requerimientos": {
            "tmb_kcal": reqs.tmb,
            "tdee_kcal": reqs.tdee,
            "calorias_objetivo": reqs.calorias_objetivo,
            "proteina_g": reqs.proteina_g,
            "carbohidratos_g": reqs.carbohidratos_g,
            "grasa_g": reqs.grasa_g,
            "fibra_g": reqs.fibra_g,
            "notas": reqs.notas,
        },
        "distribucion_comidas": {
            "desayuno": {
                "calorias": int(reqs.calorias_objetivo * 0.25),
                "proteina_g": int(reqs.proteina_g * 0.25),
            },
            "almuerzo": {
                "calorias": int(reqs.calorias_objetivo * 0.35),
                "proteina_g": int(reqs.proteina_g * 0.35),
            },
            "cena": {
                "calorias": int(reqs.calorias_objetivo * 0.30),
                "proteina_g": int(reqs.proteina_g * 0.30),
            },
            "snack": {
                "calorias": int(reqs.calorias_objetivo * 0.10),
                "proteina_g": int(reqs.proteina_g * 0.10),
            },
        },
    }

    return json.dumps(result, indent=2)
