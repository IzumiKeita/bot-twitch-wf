import requests
import time
import json
import re
from datetime import datetime, timedelta

# URL oficial de Digital Extremes (Source of Truth)
WF_API_URL = "http://content.warframe.com/dynamic/worldState.php"

# Rotaciones conocidas del Circuito (Normal - Warframes)
CIRCUIT_ROTATIONS_NORMAL = [
    ["Excalibur", "Trinity", "Ember"],
    ["Loki", "Mag", "Rhino"],
    ["Ash", "Frost", "Nyx"],
    ["Saryn", "Vauban", "Nova"],
    ["Nekros", "Valkyr", "Oberon"],
    ["Hydroid", "Mirage", "Limbo"],
    ["Mesa", "Chroma", "Atlas"],
    ["Ivara", "Inaros", "Titania"],
    ["Nidus", "Octavia", "Harrow"],
    ["Gara", "Khora", "Revenant"],
    ["Garuda", "Baruuk", "Hildryn"]
]

# Rotaciones conocidas del Circuito (Steel Path - Incarnon Genesis)
CIRCUIT_ROTATIONS_STEEL = [
    ["Braton", "Lato", "Skana", "Paris", "Kunai"],
    ["Boar", "Gammacor", "Angstrum", "Gorgon", "Anku"],
    ["Bo", "Latron", "Furis", "Furax", "Strun"],
    ["Lex", "Magistar", "Boltor", "Bronco", "Ceramic Dagger"],
    ["Torid", "Dual Toxocyst", "Dual Ichor", "Miter", "Atomos"],
    ["Ack & Brunt", "Soma", "Vasto", "Nami Solo", "Burston"],
    ["Zylok", "Sibear", "Dread", "Despair", "Hate"],
    ["Dera", "Sybaris", "Cestra", "Sicarus", "Okina"]
]

def get_worldstate():
    """Obtiene el estado mundial crudo desde la API oficial."""
    try:
        response = requests.get(WF_API_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[WARFRAME API] Error obteniendo worldState: {e}")
        return None

def parse_time(timestamp_ms):
    """Convierte timestamp en milisegundos a objeto datetime."""
    return datetime.fromtimestamp(int(timestamp_ms) / 1000)

def format_duration(seconds):
    """Formatea segundos en 'Xh Ym'."""
    if seconds < 0: return "0m"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"

def clean_name(path):
    """Limpia los nombres de recursos/misiones (ej. /Lotus/.../KelaDeThay -> Kela De Thay)."""
    if not path: return "Desconocido"
    # Tomar la última parte del path
    name = path.split('/')[-1]
    
    # Limpieza específica para Bosses (Manejar mayúsculas y prefijos)
    if "SORTIE_BOSS_" in name:
        name = name.replace("SORTIE_BOSS_", "")
    
    name = name.replace("SortieBoss", "").replace("Archon", "")
    
    # Reemplazar guiones bajos con espacios
    name = name.replace("_", " ")
    
    # Separar CamelCase con espacios
    name = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', name)
    
    # Reemplazos específicos comunes
    name = name.replace("Grineer", "").replace("Corpus", "").replace("Infested", "").strip()
    
    # Correcciones finales
    if "H U B" in name: name = name.replace("H U B", "HUB")
    
    # Capitalizar cada palabra para que se vea bonito (Kela De Thay)
    return name.title()

def get_cetus_status():
    """Calcula el ciclo de Cetus basado en las recompensas de sindicato."""
    data = get_worldstate()
    if not data: return None
    
    try:
        # Buscar la sincronización usando las misiones de CetusSyndicate
        cetus_syndicate = next((s for s in data.get('SyndicateMissions', []) if s.get('Tag') == 'CetusSyndicate'), None)
        
        if cetus_syndicate:
            activation = int(cetus_syndicate['Activation']['$date']['$numberLong']) / 1000
            now = time.time()
            cycle_seconds = now - activation
            
            # Ciclo de 150 minutos (9000s)
            # Asumimos que el ciclo de recompensas inicia con el Día
            # Día: 100m (6000s), Noche: 50m (3000s)
            
            # Ajuste: A veces la activación no es exactamente el inicio del día, pero suele serlo.
            # Vamos a usar la fórmula estándar con la activación como ancla.
            
            cycle_pos = cycle_seconds % 9000
            
            if cycle_pos < 6000:
                state = "Día"
                time_left = 6000 - cycle_pos
            else:
                state = "NOCHE (Eidolones)"
                time_left = 9000 - cycle_pos
                
            return f"Cetus: {state} ({format_duration(time_left)} restantes)"
            
    except Exception as e:
        print(f"[WARFRAME API] Error en Cetus: {e}")
    return "Cetus: No disponible"

def get_vallis_status():
    """Calcula el ciclo de Vallis (Estimado)."""
    # Ciclo: 26m 40s (1600s)
    # Frío: 20m (1200s), Cálido: 6m 40s (400s)
    # Referencia: Epoch 0 suele funcionar
    now = time.time()
    cycle_pos = now % 1600
    
    if cycle_pos < 1200:
        state = "Frío"
        time_left = 1200 - cycle_pos
    else:
        state = "Cálido"
        time_left = 1600 - cycle_pos
        
    return f"Orb Vallis: {state} ({format_duration(time_left)} restantes)"

def get_cambion_status():
    """Calcula el ciclo de Cambion Drift (Sincronizado con Cetus)."""
    # Vome (Día) / Fass (Noche)
    # Sincronizado con Cetus: Día -> Vome, Noche -> Fass
    cetus_status = get_cetus_status()
    if not cetus_status: return None
    
    if "Día" in cetus_status:
        state = "Vome (Azul)"
        # Extraer tiempo restante de la string de Cetus es feo, mejor recalcular o asumir
        # Pero reutilicemos la lógica
        return cetus_status.replace("Cetus: Día", f"Cambion Drift: {state}")
    else:
        state = "Fass (Naranja)"
        return cetus_status.replace("Cetus: NOCHE (Eidolones)", f"Cambion Drift: {state}")

def get_baro_status():
    """Verifica el estado del Void Trader (Baro Ki'Teer)."""
    data = get_worldstate()
    if not data: return None
    
    try:
        void_traders = data.get('VoidTraders', [])
        if not void_traders: return "Baro Ki'Teer: No activo"
        
        baro = void_traders[0]
        activation = int(baro['Activation']['$date']['$numberLong']) / 1000
        expiry = int(baro['Expiry']['$date']['$numberLong']) / 1000
        now = time.time()
        
        location = clean_name(baro.get('Node', 'Desconocido'))
        
        # Mapeo de Relés conocidos para nombres más amigables
        relay_map = {
            "SaturnHUB": "Relay Kronia (Saturno)",
            "PlutoHUB": "Relay Orcus (Plutón)",
            "EarthHUB": "Relay Strata (Tierra)",
            "MercuryHUB": "Relay Larunda (Mercurio)",
            "ErisHUB": "Relay Kuiper (Eris)",
            "EuropaHUB": "Relay Leonov (Europa)",
            "VenusHUB": "Relay Vesper (Venus)"
        }
        # Intentar mapear si el nombre limpio coincide con alguna clave (aunque clean_name ya lo procesó un poco)
        # Mejor usar el valor crudo del nodo para el mapeo
        raw_node = baro.get('Node', '')
        if raw_node in relay_map:
            location = relay_map[raw_node]
        
        if now < activation:
            time_left = activation - now
            return f"Baro Ki'Teer: Llega en {format_duration(time_left)} a {location}"
        elif now < expiry:
            time_left = expiry - now
            return f"Baro Ki'Teer: ACTIVO en {location} ({format_duration(time_left)} restantes)"
        else:
            return "Baro Ki'Teer: Se ha ido"
            
    except Exception as e:
        print(f"[WARFRAME API] Error en Baro: {e}")
    return None

def get_sortie_status():
    """Obtiene la Sortie actual."""
    data = get_worldstate()
    if not data: return None
    
    try:
        sorties = data.get('Sorties', [])
        if not sorties: return "Sortie: No disponible"
        
        sortie = sorties[0]
        boss = clean_name(sortie.get('Boss', 'Desconocido'))
        expiry = int(sortie['Expiry']['$date']['$numberLong']) / 1000
        now = time.time()
        time_left = format_duration(expiry - now)
        
        # Misiones (opcional, por ahora solo el Boss y tiempo)
        return f"Sortie: {boss} ({time_left} restantes)"
        
    except Exception as e:
        print(f"[WARFRAME API] Error en Sortie: {e}")
    return None

def get_archon_status():
    """Obtiene la Cacería de Arconte actual."""
    data = get_worldstate()
    if not data: return None
    
    try:
        # LiteSorties suele ser la Archon Hunt
        archons = data.get('LiteSorties', [])
        if not archons: return "Arconte: No disponible"
        
        archon = archons[0]
        boss = clean_name(archon.get('Boss', 'Desconocido'))
        expiry = int(archon['Expiry']['$date']['$numberLong']) / 1000
        now = time.time()
        time_left = format_duration(expiry - now)
        
        return f"Arconte: {boss} ({time_left} restantes)"
        
    except Exception as e:
        print(f"[WARFRAME API] Error en Arconte: {e}")
    return None

def check_prime_resurgence(warframe_name):
    """Verifica si un Warframe está actualmente en Prime Resurgence (Varzia)."""
    if not warframe_name: return False
    
    data = get_worldstate()
    if not data: return False
    
    # Normalizar nombre buscado (ej: "Atlas Prime" -> "atlas")
    target = warframe_name.lower().replace(" prime", "").strip()
    
    try:
        traders = data.get('PrimeVaultTraders', [])
        if not traders: return False
        
        now = time.time() * 1000 # MS
        
        for trader in traders:
            # Verificar si el trader está activo
            activation = int(trader.get('Activation', {}).get('$date', {}).get('$numberLong', 0))
            expiry = int(trader.get('Expiry', {}).get('$date', {}).get('$numberLong', 0))
            
            if not (activation <= now <= expiry):
                continue
                
            # Buscar en el Manifiesto (Items disponibles)
            manifest = trader.get('Manifest', [])
            for item in manifest:
                item_type = item.get('ItemType', '').lower()
                # Buscamos el nombre del warframe en el path del item
                # Ej: .../MPVAtlasPrimeSinglePack
                if target in item_type:
                    return True
                    
            # Fallback: Revisar ScheduleInfo por si acaso el Manifest no es explícito
            # (Aunque Manifest debería tener todo)
            schedule = trader.get('ScheduleInfo', [])
            for entry in schedule:
                 # Verificar si esta entrada del calendario es la actual
                 entry_expiry = int(entry.get('Expiry', {}).get('$date', {}).get('$numberLong', 0))
                 if entry_expiry > now:
                     featured = entry.get('FeaturedItem', '').lower()
                     if target in featured:
                         return True
                     # Solo revisamos el PRIMER item futuro (el actual), no todos los futuros
                     break

    except Exception as e:
        print(f"[WARFRAME API] Error en Resurgence: {e}")
        
    return False

def get_warframe_status():
    """Obtiene un resumen general del estado de Warframe."""
    cetus = get_cetus_status()
    vallis = get_vallis_status()
    cambion = get_cambion_status()
    
    parts = []
    if cetus: parts.append(cetus)
    if vallis: parts.append(vallis)
    if cambion: parts.append(cambion)
    
    if not parts:
        return "No pude obtener el estado de Warframe (API caída)."
        
    return " | ".join(parts)

def get_circuit_status(mode='normal'):
    """Obtiene la rotación actual del Circuito (Normal o Steel Path)."""
    data = get_worldstate()
    if not data: return None
    
    try:
        choices = data.get('EndlessXpChoices', [])
        if not choices: return "Circuito: No disponible"
        
        # Normal Circuit: Category "EXC_NORMAL" -> Warframes
        # Steel Path Circuit: Category "EXC_HARD" -> Incarnon Adapters
        
        target_category = "EXC_NORMAL" if mode == 'normal' else "EXC_HARD"
        
        rotation = next((c for c in choices if c.get('Category') == target_category), None)
        
        if not rotation: return f"Circuito ({mode}): No encontrado"
        
        items = rotation.get('Choices', [])
        
        # Limpiar nombres
        clean_items = []
        for item in items:
            # item suele ser un string directo como "Hydroid" o "Braton"
            # Pero a veces puede ser un path "/Lotus/..."
            clean = clean_name(item)
            clean_items.append(clean)
            
        items_str = ", ".join(clean_items)
        
        if mode == 'normal':
            return f"Circuito (Warframes): {items_str}"
        else:
            return f"Circuito (Steel Path - Incarnon): {items_str}"
            
    except Exception as e:
        print(f"[WARFRAME API] Error en Circuito: {e}")
        return None

def find_circuit_rotation(query):
    """Busca cuándo aparecerá un Warframe o Arma Incarnon en el Circuito."""
    if not query: return None
    target = query.lower().strip()
    
    # Obtener el estado actual para saber en qué semana estamos
    data = get_worldstate()
    if not data: return "No pude conectar con la API para verificar la rotación actual."
    
    try:
        choices = data.get('EndlessXpChoices', [])
        if not choices: return "Circuito no disponible en la API."
        
        # 1. Determinar semana actual NORMAL (Warframes)
        current_normal_idx = -1
        normal_rotation = next((c for c in choices if c.get('Category') == "EXC_NORMAL"), None)
        if normal_rotation:
            current_offerings = [clean_name(x) for x in normal_rotation.get('Choices', [])]
            # Buscar coincidencia en nuestras listas constantes
            for idx, week_items in enumerate(CIRCUIT_ROTATIONS_NORMAL):
                # Usamos intersección porque a veces la API usa nombres ligeramente distintos o el orden varía
                # Si hay al menos 2 coincidencias, asumimos que es esa semana
                matches = sum(1 for item in current_offerings if any(w_item.lower() == item.lower() for w_item in week_items))
                if matches >= 2:
                    current_normal_idx = idx
                    break
        
        # 2. Determinar semana actual STEEL PATH (Incarnon)
        current_steel_idx = -1
        steel_rotation = next((c for c in choices if c.get('Category') == "EXC_HARD"), None)
        if steel_rotation:
            current_offerings = [clean_name(x) for x in steel_rotation.get('Choices', [])]
            for idx, week_items in enumerate(CIRCUIT_ROTATIONS_STEEL):
                matches = sum(1 for item in current_offerings if any(w_item.lower() == item.lower() for w_item in week_items))
                if matches >= 2:
                    current_steel_idx = idx
                    break

        # 3. Buscar el objetivo en las listas
        
        # Buscar en Normal (Warframes)
        found_normal_idx = -1
        for idx, week_items in enumerate(CIRCUIT_ROTATIONS_NORMAL):
            if any(target in item.lower() for item in week_items):
                found_normal_idx = idx
                break
        
        # Buscar en Steel (Incarnon)
        found_steel_idx = -1
        for idx, week_items in enumerate(CIRCUIT_ROTATIONS_STEEL):
            if any(target in item.lower() for item in week_items):
                found_steel_idx = idx
                break
                
        results = []
        
        # Resultado Warframe
        if found_normal_idx != -1:
            if current_normal_idx != -1:
                weeks_left = (found_normal_idx - current_normal_idx) % len(CIRCUIT_ROTATIONS_NORMAL)
                week_items = ", ".join(CIRCUIT_ROTATIONS_NORMAL[found_normal_idx])
                if weeks_left == 0:
                    results.append(f"✅ **{query.title()}** está disponible ESTA SEMANA en el Circuito Normal ({week_items}).")
                elif weeks_left == 1:
                    results.append(f"⏳ **{query.title()}** vuelve la PRÓXIMA SEMANA al Circuito Normal ({week_items}).")
                else:
                    results.append(f"📅 **{query.title()}** vuelve en {weeks_left} semanas al Circuito Normal ({week_items}).")
            else:
                results.append(f"❓ **{query.title()}** está en la rotación del Circuito Normal, pero no pude determinar la semana actual.")

        # Resultado Incarnon
        if found_steel_idx != -1:
            if current_steel_idx != -1:
                weeks_left = (found_steel_idx - current_steel_idx) % len(CIRCUIT_ROTATIONS_STEEL)
                week_items = ", ".join(CIRCUIT_ROTATIONS_STEEL[found_steel_idx])
                if weeks_left == 0:
                    results.append(f"✅ **{query.title()} (Incarnon)** está disponible ESTA SEMANA en Steel Path ({week_items}).")
                elif weeks_left == 1:
                    results.append(f"⏳ **{query.title()} (Incarnon)** vuelve la PRÓXIMA SEMANA a Steel Path ({week_items}).")
                else:
                    results.append(f"📅 **{query.title()} (Incarnon)** vuelve en {weeks_left} semanas a Steel Path ({week_items}).")
            else:
                results.append(f"❓ **{query.title()} (Incarnon)** está en la rotación Steel Path, pero no pude determinar la semana actual.")
                
        if results:
            return "\n".join(results)
            
        return f"❌ No encontré '{query}' en las rotaciones del Circuito (Normal o Steel Path)."

    except Exception as e:
        print(f"[WARFRAME API] Error predicción Circuito: {e}")
        return "Error calculando la rotación."

