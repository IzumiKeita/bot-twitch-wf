
import os
import sys

# Importamos warframe_drops y warframe_api directamente
from .drops import drops_manager
from . import api as warframe_api

class WarframeModule:
    """Módulo específico para Warframe."""
    SYSTEM_PROMPT = """
    [WARFRAME MODE ACTIVATED]
    Eres 'Ordis' o una IA de Cephalon. Tu conocimiento sobre Warframe es absoluto.
    - Usa términos como 'Tenno', 'Operador', 'Warframe'.
    - Si te preguntan por drops, sé preciso.
    - Si te preguntan por estado del mundo (Cetus, Vallis), usa la información más reciente.
    """
    
    def __init__(self, bot_instance):
        self.bot = bot_instance

    def handle_message(self, message, user):
        """Maneja mensajes entrantes para detectar comandos."""
        if not message.startswith("!"):
            return None
            
        parts = message.split()
        command = parts[0].lower()
        args = parts[1:]
        
        return self.handle_command(command, args, {"user": user})

    def handle_command(self, command, args, context):
        """Maneja comandos específicos de Warframe."""
        if command in ["!drop", "!farm", "!donde"]:
            if not args:
                return "Uso: !drop <item> (ej: !drop wisp)"
            return drops_manager.get_formatted_response(" ".join(args))
        
        elif command in ["!recurso", "!res"]:
             if not args:
                return "Uso: !recurso <nombre> (ej: !recurso oxium)"
             return drops_manager.get_formatted_response(" ".join(args), category='resource')

        elif command == "!mod":
             if not args:
                return "Uso: !mod <nombre> (ej: !mod mordisco)"
             return drops_manager.get_formatted_response(" ".join(args), category='mod')

        elif command in ["!arcano", "!arcanos"]:
             if not args:
                return "Uso: !arcano <nombre> (ej: !arcano gracia)"
             return drops_manager.get_formatted_response(" ".join(args), category='arcane')

        elif command in ["!info", "!reliquia", "!relic"]:
            if not args:
                return "Uso: !info <reliquia> (ej: !info Neo T1)"
            return drops_manager.get_relic_contents(" ".join(args))

        elif command in ["!cetus", "!vallis", "!deimos", "!baro", "!sortie", "!archon", "!circuito", "!circuito_steel"]:
            # Usar warframe_api para estos comandos de estado
            if command == "!cetus":
                return warframe_api.get_cetus_status()
            elif command == "!vallis":
                return warframe_api.get_vallis_status()
            elif command == "!deimos":
                return warframe_api.get_cambion_status()
            elif command == "!baro":
                return warframe_api.get_baro_status()
            elif command == "!sortie":
                return warframe_api.get_sortie_status()
            elif command == "!archon":
                return warframe_api.get_archon_status()
            elif command == "!circuito":
                if args:
                    return warframe_api.find_circuit_rotation(" ".join(args))
                return warframe_api.get_circuit_status(mode='normal')
            elif command == "!circuito_steel":
                if args:
                    return warframe_api.find_circuit_rotation(" ".join(args))
                return warframe_api.get_circuit_status(mode='steel')
            
            # Fallback a status completo si no coincide (aunque no debería llegar aquí por la lista)
            status = warframe_api.get_warframe_status()
            return f"Estado Warframe: {status}" 

        return None

MODULE_CLASS = WarframeModule
