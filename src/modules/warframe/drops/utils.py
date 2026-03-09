import re

TRANSLATIONS = {
    "Blueprint": "Plano",
    "Chassis": "Chasis",
    "Neuroptics": "Neurópticas",
    "Systems": "Sistemas",
    "Relic": "Reliquia",
    "Intact": "Intacta",
    "Exceptional": "Excepcional",
    "Flawless": "Impecable",
    "Radiant": "Radiante",
    "Rotation": "Rotación",
    "Common": "Común",
    "Uncommon": "Poco Común",
    "Rare": "Rara",
    "Legendary": "Legendaria",
    "Assassination": "Asesinato",
    "Capture": "Captura",
    "Defense": "Defensa",
    "Exterminate": "Exterminio",
    "Survival": "Supervivencia",
    "Spy": "Espionaje",
    "Disruption": "Interrupción",
    "Interception": "Interceptación",
    "Sabotage": "Sabotaje"
}

PARTS_ES_TO_EN = {
    "sistemas": "Systems",
    "chasis": "Chassis",
    "neuropticas": "Neuroptics",
    "neurópticas": "Neuroptics",
    "plano": "Blueprint",
    "reliquia": "Relic",
    "cabeza": "Neuroptics", # Alias común
    "casco": "Neuroptics"   # Alias común
}

def translate_common_terms(text):
    # 1. Regex para casos complejos (ej: "Wisp Neuroptics Blueprint")
    
    # Neurópticas
    match = re.search(r'(.+) Neuroptics Blueprint', text)
    if match: return f"Plano de Neurópticas de {match.group(1)}"
    
    # Chasis
    match = re.search(r'(.+) Chassis Blueprint', text)
    if match: return f"Plano de Chasis de {match.group(1)}"
    
    # Sistemas
    match = re.search(r'(.+) Systems Blueprint', text)
    if match: return f"Plano de Sistemas de {match.group(1)}"
    
    # Neurópticas (sin Blueprint)
    match = re.search(r'(.+) Neuroptics', text)
    if match: return f"Neurópticas de {match.group(1)}"
    
    # Chasis (sin Blueprint)
    match = re.search(r'(.+) Chassis', text)
    if match: return f"Chasis de {match.group(1)}"
    
    # Sistemas (sin Blueprint)
    match = re.search(r'(.+) Systems', text)
    if match: return f"Sistemas de {match.group(1)}"
    
    # Plano general (al final)
    match = re.search(r'(.+) Blueprint', text)
    if match: return f"Plano de {match.group(1)}"

    # 2. Reemplazo directo de términos
    for eng, esp in TRANSLATIONS.items():
        text = text.replace(eng, esp)
    return text
