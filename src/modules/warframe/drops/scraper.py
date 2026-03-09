import requests
import json
import re
from bs4 import BeautifulSoup
import os

def update_from_json(json_path):
    print(f"[DROPS] Intentando cargar datos desde {json_path}...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        new_drops = []
        for entry in data:
            # Limpiar HTML tags de 'place' (ej: <b>Survival</b>)
            raw_place = entry.get('place', 'Unknown')
            place = re.sub(r'<[^>]+>', '', raw_place).strip()
            
            # Limpiar prefijos basura comunes en el JSON
            place = re.sub(r'^(Disclaimer|Table of Contents|Missions|Relics|Keys|Sortie|Cetus|Solaris|Deimos):\s*', '', place, flags=re.IGNORECASE)
            
            # Quitar paréntesis externos si quedaron solos (ej: "(Jupiter/...)")
            if place.startswith('(') and place.endswith(')'):
                place = place[1:-1].strip()

            item = entry.get('item', 'Unknown')
            rarity = entry.get('rarity', 'Unknown')
            # Convertir chance a float para ordenar correctamente
            chance = entry.get('chance')
            try:
                chance_val = float(chance) if chance is not None else 0.0
            except (ValueError, TypeError):
                chance_val = 0.0
            
            # Categoría simple
            category = "General"
            if "Relic" in item: category = "Relics"
            elif "Mod" in item: category = "Mods"
            elif "Blueprint" in item: category = "Blueprints"
            elif "Arcane" in item: category = "Arcanes"
            
            new_drops.append((place, item, rarity, chance_val, category))
        
        return new_drops
        
    except Exception as e:
        print(f"[DROPS] Error cargando JSON local: {e}")
        return None

def update_from_web(url):
    """Descarga y parsea la tabla de drops oficial."""
    print("[DROPS] Iniciando scraping web...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        new_drops = []
        
        for header in soup.find_all('h3'):
            source_name = header.get_text(strip=True)
            table = header.find_next('table')
            if not table: continue
            
            rows = table.find_all('tr')
            current_sub_source = "" # Para rotaciones A, B, C dentro de una misión
            
            for row in rows:
                cols = row.find_all(['td', 'th'])
                if not cols: continue
                
                text_cols = [c.get_text(strip=True) for c in cols]
                
                # Caso: Header de Rotación/Subsección dentro de la tabla (th colspan)
                if cols[0].name == 'th' and len(text_cols) == 1:
                    current_sub_source = f" ({text_cols[0]})"
                    continue
                
                # Caso: Header de columnas (Item, Rarity, Chance)
                if "Item" in text_cols[0] or "Chance" in text_cols[-1]:
                    continue
                    
                # Caso: Fila de datos
                full_source = f"{source_name}{current_sub_source}"
                
                if len(text_cols) >= 3:
                    item = text_cols[0]
                    rarity = text_cols[1]
                    chance = text_cols[2]
                    new_drops.append((full_source, item, rarity, chance, 'General'))
                elif len(text_cols) == 2:
                    item = text_cols[0]
                    chance = text_cols[1]
                    new_drops.append((full_source, item, 'Unknown', chance, 'General'))

        if new_drops:
            return new_drops
        else:
            print("[DROPS] Advertencia: No se pudieron extraer drops. La estructura de la web pudo haber cambiado.")
            return None

    except Exception as e:
        print(f"[DROPS] Error crítico actualizando DB desde web: {e}")
        return None
