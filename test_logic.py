import sys
import os

# Ajustar path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.modules.warframe.drops import drops_manager

print("--- Probando lógica de drops ---")
try:
    # Prueba 1: Drop conocido
    query = "wisp"
    print(f"Buscando '{query}'...")
    response = drops_manager.get_formatted_response(query)
    print(f"Respuesta: {response}")
    
    # Prueba 2: Reliquia
    query = "Neo T1"
    print(f"\nBuscando reliquia '{query}'...")
    response = drops_manager.get_relic_contents(query)
    print(f"Respuesta: {response}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n--- Fin de la prueba ---")
