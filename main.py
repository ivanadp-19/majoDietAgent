import argparse

from src.utils.document_loader import load_document_text
from src.workflows.diet_planner import diet_planner
from src.workflows.extraction import meal_extraction_workflow


def run_extraction(file_path: str) -> None:
    """Ejecutar el workflow de extraccion de comidas."""
    print(f"\nIniciando extraccion de comidas desde: {file_path}\n")
    print("=" * 50)

    document_text = load_document_text(file_path)

    meal_extraction_workflow.print_response(
        input=document_text,
        additional_data={"file_path": file_path},
        markdown=True,
        stream=True,
    )


def run_diet_planner() -> None:
    """Ejecutar el planificador de dietas interactivo."""
    print("\nPlanificador de Dietas - Modo Interactivo")
    print("=" * 50)
    print("Hola. Soy tu asistente de nutricion.")
    print("Cuentame tus objetivos y te ayudo a crear un plan de alimentacion.")
    print("Escribe 'salir' para terminar.\n")

    while True:
        user_input = input("Tu: ").strip()
        if user_input.lower() in ["salir", "exit", "quit", "q"]:
            print("\nHasta luego. Recuerda mantener una alimentacion balanceada.")
            break

        if not user_input:
            continue

        diet_planner.print_response(user_input, stream=True)
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sistema de Extraccion de Comidas y Planificacion de Dietas"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    extract_parser = subparsers.add_parser(
        "extraer", help="Extraer comidas de un documento"
    )
    extract_parser.add_argument("archivo", help="Ruta al archivo docx")

    subparsers.add_parser("planificar", help="Planificador de dietas interactivo")

    args = parser.parse_args()

    if args.command == "extraer":
        run_extraction(args.archivo)
    elif args.command == "planificar":
        run_diet_planner()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
    