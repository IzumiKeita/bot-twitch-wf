import sqlite3
import re
import json
import os
import unicodedata
import difflib
from src.modules.warframe.api import check_prime_resurgence
from .database import translate_item_name
from .utils import translate_common_terms, PARTS_ES_TO_EN

# Cache for translations: normalized_spanish -> english_name
TRANSLATIONS_CACHE = {}

def normalize_text(text):
    """Normalize text: lowercase and remove accents."""
    if not text: return ""
    text = text.lower()
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def load_translations_cache(db_path):
    """Load all translations into memory for fast, fuzzy lookup."""
    global TRANSLATIONS_CACHE
    if TRANSLATIONS_CACHE: return # Already loaded
    
    try:
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT spanish_name, english_name FROM translations")
            rows = c.fetchall()
            for sp, en in rows:
                if sp:
                    norm = normalize_text(sp)
                    TRANSLATIONS_CACHE[norm] = en
                    # Also map original lowercase just in case
                    TRANSLATIONS_CACHE[sp.lower()] = en
    except Exception as e:
        print(f"[ERROR] Failed to load translations cache: {e}")

def load_json_config(filename):
    """Load configuration from a JSON file in the config directory."""
    config_path = os.path.abspath(os.path.join("config", filename))
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load {filename}: {e}")
    return {}

# --- MANUAL OVERRIDES FOR ITEMS NOT IN OFFICIAL DROP TABLES ---
# Key: Query (normalized to lowercase), Value: Response String
MANUAL_DROPS = load_json_config("manual_drops.json")

# --- MANUAL RESOURCE MAP (Region Drops not in Drop Tables) ---
MANUAL_RESOURCES = load_json_config("manual_resources.json")

# --- PHONETIC OVERRIDES (Fix common STT errors) ---
PHONETIC_OVERRIDES = {
    "voy brain": "volt prime",
    "boy brain": "volt prime",
    "bolt brain": "volt prime",
    "void brain": "volt prime",
    "volt brain": "volt prime",
    "sarin prime": "saryn prime",
    "wis prime": "wisp prime",
    "gause prime": "gauss prime",
    "rine prime": "rhino prime",
    "rino prime": "rhino prime",
}

def get_formatted_response(db_path, query, category=None):
    """
    Busca drops y devuelve un string formateado para el chat.
    category: 'mod', 'arcane', 'resource', o None (general)
    """
    # print(f"DEBUG: Searching for '{query}' in {db_path}") 
    if not query or len(query) < 3: return None
    
    # Remove common punctuation that users might type in chat queries
    query = query.replace('?', '').replace('!', '').replace('¿', '').replace('¡', '').strip()
    query_lower = query.lower()

    # Check Phonetic Overrides first
    if query_lower in PHONETIC_OVERRIDES:
        query = PHONETIC_OVERRIDES[query_lower]
        query_lower = query.lower()

    # Normalize common variations
    if query_lower == "cyte 09": query_lower = "cyte-09"
    
    # --- CHECK MANUAL RESOURCES EARLY ---
    if category == 'resource':
        # 1. Check Manual Resource Map first (Region Drops)
        # BUT FIRST: Check if the query is in our "force DB" list (simulated by checking if it was deleted from JSON)
        # Since we deleted them from JSON, if it's NOT in JSON, it falls through to DB.
        # However, "placa de aleacion" might still be matched by fuzzy search below if other keys exist.
        
        if query_lower in MANUAL_RESOURCES:
            return f"Drops para **{query}**: {MANUAL_RESOURCES[query_lower]}"
        
        # 2. Also check common translations if not found directly
        # PROBLEM: This fuzzy match is too aggressive. If "placa de aleacion" was deleted,
        # but "placa" exists (unlikely) or something similar, it might trigger.
        # MORE LIKELY: "Placa de aleación" fails exact match in JSON, falls through to DB,
        # but DB translation fails because of accents/case sensitivity issues in SQLite `LIKE` with non-ASCII.
        
        if len(query_lower) > 3:
            for key in MANUAL_RESOURCES:
                if query_lower in key: # Simple fuzzy match
                    # Verify it's a reasonable match length ratio to avoid "a" matching everything
                    if len(key) < len(query_lower) * 2: 
                        return f"Drops para **{query}** (Detectado como {key}): {MANUAL_RESOURCES[key]}"

    try:
        # Load translation cache first (lazy load)
        load_translations_cache(db_path)
        
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            
            # --- PASO PREVIO: TRADUCCIÓN MANUAL DE PARTES (Español -> Inglés) ---
            query_words = query.lower().split()
            translated_words = []
            for word in query_words:
                translated_words.append(PARTS_ES_TO_EN.get(word, word))
            
            # Query con partes en inglés (ej: "ash prime systems")
            query_parts_en = " ".join(translated_words)
            
            # --- PASO 0: INTENTAR TRADUCIR LA QUERY (Español -> Inglés) ---
            # 1. Búsqueda en caché de memoria (normalizado: sin acentos, minúsculas)
            query_norm = normalize_text(query)
            translation_res = None
            
            if query_norm in TRANSLATIONS_CACHE:
                translation_res = (TRANSLATIONS_CACHE[query_norm],)
            
            # Si no está en caché, intentar búsqueda parcial en DB (LIKE)
            if not translation_res and len(query) > 4:
                # Use LIKE for partial matches
                c.execute("SELECT english_name FROM translations WHERE spanish_name LIKE ? ORDER BY length(spanish_name) ASC LIMIT 1", (f'%{query}%',))
                translation_res = c.fetchone()
            
            final_query = query
            if translation_res:
                final_query = translation_res[0]
            elif query_parts_en != query:
                final_query = query_parts_en
                
            else:
                # Arcanos: "gracia arcana" -> "Arcane Grace" (inversión de orden) o búsqueda sin prefijo
                is_arcane_context = (category == 'arcane') or ("arcano" in query.lower() or "arcana" in query.lower())
                
                if is_arcane_context:
                    # Remove "arcano/a" to get the core name (e.g. "gracia", "energize")
                    clean_q = re.sub(r'\b(arcano|arcana)\b', '', query, flags=re.IGNORECASE).strip()
                    if clean_q:
                         # Try constructing the Spanish full name: "Arcano <Name>"
                         # e.g. "gracia" -> "Arcano Gracia" -> "Arcane Grace"
                         potential_es_name = f"Arcano {clean_q}"
                         c.execute("SELECT english_name FROM translations WHERE spanish_name = ? COLLATE NOCASE", (potential_es_name,))
                         arcane_res = c.fetchone()
                         
                         if arcane_res:
                             final_query = arcane_res[0]
                         else:
                             # Try suffix "Arcana" (e.g. "Gracia Arcana")
                             potential_es_name_suffix = f"{clean_q} Arcana"
                             c.execute("SELECT english_name FROM translations WHERE spanish_name = ? COLLATE NOCASE", (potential_es_name_suffix,))
                             arcane_res = c.fetchone()
                             
                             if arcane_res:
                                 final_query = arcane_res[0]
                             else:
                                 # Try suffix "Arcano"
                                 potential_es_name_suffix_o = f"{clean_q} Arcano"
                                 c.execute("SELECT english_name FROM translations WHERE spanish_name = ? COLLATE NOCASE", (potential_es_name_suffix_o,))
                                 arcane_res = c.fetchone()
                                 
                                 if arcane_res:
                                     final_query = arcane_res[0]
                                 else:
                                      # Try fuzzy match for "Arcano <clean_q>%"
                                      c.execute("SELECT english_name FROM translations WHERE spanish_name LIKE ? COLLATE NOCASE ORDER BY length(spanish_name) ASC LIMIT 1", (f'Arcano {clean_q}%',))
                                      arcane_res = c.fetchone()
                                      if arcane_res:
                                          final_query = arcane_res[0]

            # Detectar si el usuario busca explícitamente algo Prime
            is_prime_query = 'prime' in query.lower() or 'prime' in final_query.lower()
            
            results = []
            limit = 100 
            if category == 'resource':
                limit = 100

            # 1. Construcción de la Query SQL base
            sql_query = "SELECT source, item, rarity, chance FROM drops WHERE item LIKE ?"
            
            # STRICT PRIME FILTER
            if not is_prime_query:
                sql_query += " AND item NOT LIKE '%Prime%'"
            
            params = [f'%{final_query}%']

            if category == 'arcane':
                # Expanded Arcane prefixes to include SP Arcanes, Operator Arcanes, etc.
                arcane_prefixes = [
                    'Arcane', 'Arcano', 'Magus', 'Virtuos', 'Pax', 'Exodia', 
                    'Residual', 'Theorem', 'Primary', 'Secondary', 'Cascadia', 
                    'Emergence', 'Eternal', 'Fractal', 'Molt',
                    'Melee', 'Shotgun', 'Longbow'
                ]
                likes = [f"item LIKE '%{p}%'" for p in arcane_prefixes]
                sql_query += " AND (" + " OR ".join(likes) + ")"
            
            # Ordenamiento
            sql_order = """
                ORDER BY 
                (CASE WHEN item LIKE ? THEN 1 ELSE 0 END) DESC,
                (CASE WHEN item LIKE '%Blueprint%' OR item LIKE '%Plano%' OR item LIKE '%Systems%' OR item LIKE '%Sistemas%' OR item LIKE '%Chassis%' OR item LIKE '%Chasis%' OR item LIKE '%Neuroptics%' OR item LIKE '%Neurópticas%' THEN 1 ELSE 0 END) DESC,
                (CASE WHEN source LIKE '%Relic%' OR source LIKE '%Reliquia%' THEN 0 ELSE 1 END) DESC,
                chance DESC,
                source
            """
            query_start = f"{final_query}%"
            
            # Ejecutar búsqueda principal (STRICT)
            print(f"DEBUG: Executing SQL with final_query='{final_query}'")
            c.execute(f"{sql_query} {sql_order} LIMIT {limit}", params + [query_start])
            results = c.fetchall()
            if results: print(f"DEBUG: First result: {results[0]}")
            else: print("DEBUG: No results found in main query.")

            # 2. Búsqueda Fallback (Si Strict falló)
            if not results and not is_prime_query:
                sql_lax = sql_query.replace(" AND item NOT LIKE '%Prime%'", "")
                c.execute(f"{sql_lax} {sql_order} LIMIT {limit}", params + [query_start])
                results = c.fetchall()
            
            # 3. Fallback de traducción (Si todo lo anterior falló)
            if not results and final_query != query:
                params = [f'%{query}%']
                query_start = f"{query}%"
                
                sql_fallback = sql_query
                is_prime_original = 'prime' in query.lower()
                
                if not is_prime_original and "NOT LIKE '%Prime%'" not in sql_fallback:
                     sql_fallback += " AND item NOT LIKE '%Prime%'"

                c.execute(f"{sql_fallback} {sql_order} LIMIT {limit}", params + [query_start])
                results = c.fetchall()
                
                if not results and not is_prime_original:
                    sql_lax_fallback = sql_fallback.replace(" AND item NOT LIKE '%Prime%'", "")
                    c.execute(f"{sql_lax_fallback} {sql_order} LIMIT {limit}", params + [query_start])
                    results = c.fetchall()

    except Exception as e:
        print(f"Error en DB: {e}")
        return None

    # --- FALLBACK: PRIORITY CHECK FOR MANUAL OVERRIDES (If DB found "junk" only) ---
    if results and query_lower in MANUAL_DROPS:
        # Check if DB results look like actual Warframe components (Parts/BP)
        # This prevents showing only Augment Mods or Skins for frames that are primarily obtained via Dojo/Quest
        has_real_parts = False
        keywords_parts = ['blueprint', 'chassis', 'systems', 'neuroptics', 'plano', 'chasis', 'sistemas', 'neurópticas']
        blacklist_keywords = ['helmet', 'casco', 'skin', 'aspecto', 'ephemera', 'efímero', 'scene', 'escena', 'glyph', 'glifo', 'sigil', 'sello', 'statue', 'estatua', 'poster', 'prex', 'icon', 'icono']
        
        for r in results:
            item_name_lower = r[1].lower()
            if any(k in item_name_lower for k in keywords_parts):
                # Ensure it's not a blacklisted item (e.g. Helmet Blueprint)
                if any(bad in item_name_lower for bad in blacklist_keywords):
                    continue
                has_real_parts = True
                break
        
        # Exception for Kullervo (drops Bane, not parts, but DB result is valid)
        if 'kullervo' in query_lower and any('bane' in r[1].lower() for r in results):
             has_real_parts = True

        # Exception for Yareli (Quest BP exists in DB, but parts are Dojo - prevent partial DB result)
        if 'yareli' in query_lower:
             has_components = False
             for r in results:
                 if any(part in r[1].lower() for part in ['chassis', 'systems', 'neuroptics', 'chasis', 'sistemas', 'neurópticas']):
                     has_components = True
                     break
             if not has_components:
                 has_real_parts = False

        # Exception for Nokko (Force Manual Override for better readability/Shop info)
        if 'nokko' in query_lower:
            has_real_parts = False

        # Exception for Ash (Railjack drops are complex, force manual summary)
        if query_lower == 'ash':
            has_real_parts = False

        # Exception for Ignis/Gorgon (Force manual for event/dojo context)
        if 'ignis' in query_lower or 'gorgon' in query_lower:
            has_real_parts = False

        if not has_real_parts:
            return f"Drops para **{query}**: {MANUAL_DROPS[query_lower]}"

    # --- FALLBACK: CHECK MANUAL OVERRIDES IF DB RETURNED NOTHING ---
    if not results and query_lower in MANUAL_DROPS:
        return f"Drops para **{query}**: {MANUAL_DROPS[query_lower]}"

    if not results:
        # Intento de detección de Primes Vaulted
        if is_prime_query or 'prime' in final_query.lower():
            # Si no hay drops pero parece una búsqueda Prime, verificamos si el item existe en traducciones
            # Esto sugiere que es un item válido pero que no tiene drops activos (Vaulted)
            try:
                with sqlite3.connect(db_path) as conn:
                    c = conn.cursor()
                    # Buscar si existe en traducciones (aunque no tenga drops)
                    c.execute("SELECT english_name FROM translations WHERE english_name LIKE ? LIMIT 1", (f'%{final_query}%',))
                    exists = c.fetchone()
                    if exists:
                        # Verificar si está en Prime Resurgence (Varzia)
                        try:
                            in_resurgence = check_prime_resurgence(final_query)
                            if in_resurgence:
                                return f"**{final_query}**: Resurgimiento Prime"
                        except Exception as e:
                            print(f"[LOGIC] Error checking resurgence: {e}")

                        return f"No encontré drops activos para **{final_query}**. Es muy probable que esté en la **Prime Vault** (Bóveda) y sus reliquias no caigan actualmente."
            except:
                pass

    # --- FORMAT RESULT (If DB found something) ---
    
    # --- Lógica de Filtrado Inteligente (Post-SQL) ---
    # Filtrar drops con chance > 0 y EXCLUIR Conclave (PVP muerto)
    results = [r for r in results if r[3] > 0 and 'conclave' not in r[0].lower()]
    
    if not results:
        # Fallback para Primes Vaulted (si se filtraron por probabilidad 0)
        if is_prime_query or 'prime' in final_query.lower():
            try:
                if check_prime_resurgence(final_query):
                    return f"**{final_query}**: Resurgimiento Prime"
            except: pass

            return f"No encontré drops activos para **{final_query}**. Probablemente esté en la **Prime Vault**."
        
        # --- FUZZY MATCH SUGGESTION ---
        try:
            query_norm_check = normalize_text(query)
            if TRANSLATIONS_CACHE:
                # Buscar en las claves (nombres en español normalizados)
                possible_matches = difflib.get_close_matches(query_norm_check, TRANSLATIONS_CACHE.keys(), n=1, cutoff=0.6)
                if possible_matches:
                    suggestion = TRANSLATIONS_CACHE[possible_matches[0]]
                    return f"No encontré '{query}', ¿quisiste decir **{suggestion}**?"
        except Exception as e:
            print(f"[Fuzzy] Error: {e}")

        return f"No encontré drops con probabilidad válida para '{query}'."

    # 1. Prioridad de Coincidencia Exacta
    exact_matches = [r for r in results if r[1].lower() == final_query.lower()]
    
    # Definir keywords de partes si no están definidas
    keywords_parts = ['Blueprint', 'Chassis', 'Systems', 'Neuroptics', 'Plano', 'Chasis', 'Sistemas', 'Neurópticas']
    
    has_parts_in_results = any(any(k in r[1] for k in keywords_parts) for r in results)
    
    if exact_matches:
        # Si el match exacto NO es una parte, pero tenemos partes en los resultados, priorizamos las partes.
        # Esto soluciona casos como "Excalibur" (Item de Conclave) ocultando los Planos.
        exact_is_part = any(any(k in r[1] for k in keywords_parts) for r in exact_matches)
        
        if not exact_is_part and has_parts_in_results:
             # Filtrar para mostrar solo las partes
             results = [r for r in results if any(k in r[1] for k in keywords_parts)]
        else:
             results = exact_matches
    else:
        starts_with = [r for r in results if r[1].lower().startswith(final_query.lower())]
        if starts_with:
            results = starts_with
    
    # Caso especial !drop (General): Filtrar basura si encontramos partes de Warframe
    if category is None:
        warframe_parts = []
        has_parts = False
        
        keywords_parts = ['Blueprint', 'Chassis', 'Systems', 'Neuroptics', 'Plano', 'Chasis', 'Sistemas', 'Neurópticas']
        
        # Palabras clave a EXCLUIR (Blacklist)
        blacklist_keywords = ['Helmet', 'Casco', 'Skin', 'Aspecto', 'Ephemera', 'Efímero', 'Scene', 'Escena', 'Glyph', 'Glifo', 'Sigil', 'Sello', 'Statue', 'Estatua', 'Poster', 'Prex']
        
        query_asks_blacklist = any(bad.lower() in query.lower() for bad in blacklist_keywords)

        # Heurística: Si los resultados contienen "Neuroptics" (o Neurópticas), asumimos que es un Warframe.
        # Esto evita aplicar el filtro estricto a Armas (que no tienen Neuropticas) o Archwings/Sentinelas (a veces).
        # Solo los Warframes tienen consistentemente Neuropticas.
        has_neuroptics = any('Neuroptics' in r[1] or 'Neurópticas' in r[1] for r in results)

        if has_neuroptics and not query_asks_blacklist:
            for r in results:
                item_name = r[1]
                
                # Si es un Warframe, SOLO queremos las partes principales.
                if any(k in item_name for k in keywords_parts):
                    # Doble chequeo de blacklist por si acaso (ej: "Chassis Skin"?)
                    if any(bad in item_name for bad in blacklist_keywords):
                        continue
                    
                    has_parts = True
                    warframe_parts.append(r)
            
            # Si encontramos partes y validamos que es un Warframe, reemplazamos los resultados.
            if has_parts:
                results = warframe_parts
            
    # --- Lógica de Agrupación por Categoría ---

    # CASO 1: RECURSOS (!recurso)
    if category == 'resource':
        planet_map = {}
        VALID_PLANETS = [
            "Mercury", "Venus", "Earth", "Mars", "Phobos", "Ceres", "Jupiter", "Europa", 
            "Saturn", "Uranus", "Neptune", "Pluto", "Eris", "Sedna", "Void", "Lua", 
            "Kuva Fortress", "Zariman", "Deimos", "Veil Proxima", "Earth Proxima", 
            "Saturn Proxima", "Venus Proxima", "Neptune Proxima", "Pluto Proxima",
            "Sanctum Anatomica", "Duviri"
        ]
        
        for source, item, rarity, chance in results:
            # Skip random containers/crates, but KEEP 'Cache' (Sabotage Caches are valid mission rewards)
            if any(x in source for x in ['Storage Container', 'Crate', 'Carrypod']):
                continue

            # Clean source name (remove Event prefix)
            clean_source = source
            if clean_source.startswith("Event:"):
                clean_source = clean_source.replace("Event:", "").strip()

            planet = clean_source.split('/')[0].strip()
            if '/' not in clean_source: planet = clean_source

            is_valid_planet = any(planet.startswith(p) for p in VALID_PLANETS)
            if not is_valid_planet: continue

            if planet not in planet_map or chance > planet_map[planet]['chance']:
                planet_map[planet] = {'source': source, 'chance': chance, 'item': item}
        
        parts = []
        for planet in sorted(planet_map.keys()):
            data = planet_map[planet]
            src = data['source']
            if '/' in src: mission_info = src.split('/', 1)[1]
            else: mission_info = src
            parts.append(f"{planet}: {mission_info} ({data['chance']:.2f}%)")
        
        if not parts:
            return f"No encontré misiones específicas para **{query}**. Puede que caiga de enemigos."

        return f"Mejores misiones para **{query}**: " + " | ".join(parts)

    # CASO 2: MODS, ARCANOS, GENERAL
    processed_items = []
    
    for source, item, rarity, chance in results:
        # Detectar si es reliquia
        if "Relic" in source or "Reliquia" in source:
            # Clean common quality qualifiers and redundant words
            clean_source = re.sub(r'\s*\((Intact|Exceptional|Flawless|Radiant|Intacta|Excepcional|Impecable|Radiante)\)', '', source, flags=re.IGNORECASE)
            clean_source = re.sub(r'\s*\(.*?\)', '', clean_source) # Remove any other parentheses content just in case
            clean_source = re.sub(r'\s*(Relic|Reliquia)', '', clean_source, flags=re.IGNORECASE).strip()
            
            # Try to extract standard Era Code format (e.g. "Lith V7", "Vanguard M1")
            relic_match = re.search(r'((?:Lith|Meso|Neo|Axi|Requiem|Vanguard)\s+[A-Z0-9]+)', clean_source, re.IGNORECASE)
            if relic_match: 
                source_name = relic_match.group(1)
                # Ensure consistent capitalization (e.g. "lith v7" -> "Lith V7")
                parts = source_name.split()
                if len(parts) == 2:
                    source_name = f"{parts[0].capitalize()} {parts[1].upper()}"
            else: 
                source_name = clean_source
        else:
            source_name = source.split('(')[0].strip()
        
        item_es = translate_item_name(db_path, item)
        item_translated = translate_common_terms(item_es)
        
        clean_name = item_translated
        
        # Extended list of parts to include weapons and companions
        weapon_parts = [
             'Blueprint', 'Chassis', 'Systems', 'Neuroptics', # Warframes
             'Barrel', 'Receiver', 'Stock', 'Handle', 'Link', 'Blade', 'Hilt', 'Grip', 'String', 'Limb', 
             'Ornament', 'Head', 'Motor', 'Pouch', 'Stars', 'Disc', 'Boot', 'Carapace', 'Cerebrum', 
             'Harness', 'Wings', 'Avionics', 'Buckle', 'Ribbon', 'Chain', 'Band'
        ]
        
        is_part = any(x in item for x in weapon_parts)
        
        # Treat the Main BP (which often matches the Warframe name exactly) as a part for cleaning
        if clean_name.lower() == final_query.lower() or clean_name.lower() == query.lower():
             is_part = True
        
        if is_part:
              # 1. Remove "Plano de/del" prefix
              temp_name = re.sub(r'(?i)^plano (de|del)\s+', '', clean_name).strip()
              
              # 2. Remove the Query itself (e.g. "Ash Prime")
              pattern = re.compile(re.escape(final_query), re.IGNORECASE)
              temp_name = pattern.sub("", temp_name).strip()
              
              # 3. Aggressively remove "Prime" and "de" to simplify output
              temp_name = re.sub(r'(?i)\s*prime\b', '', temp_name).strip()
              temp_name = re.sub(r'(?i)\s*\bde\b\s*', ' ', temp_name).strip() 
              temp_name = re.sub(r'\s+', ' ', temp_name).strip()
              
              if not temp_name:
                   clean_name = "Plano Principal"
              elif len(temp_name) > 2:
                   clean_name = temp_name.capitalize()

        
        processed_items.append({
            'source': source_name,
            'item_name': clean_name.strip(),
            'chance': chance,
            'is_relic': "Relic" in source or "Reliquia" in source,
            'original_query': final_query, # To detect redundant names (English DB name)
            'user_query': query, # To detect redundant names (User Input)
            'item_id_en': item # The raw English name from DB
        })

    # --- ADVANCED GROUPING AND FORMATTING ---
    from collections import defaultdict
    import os
    
    # 1. Separate Relics vs Normal Drops
    relic_map = {}
    normal_drops = []
    
    for data in processed_items:
        if data['is_relic']:
            item = data['item_name']
            src = data['source']
            if item not in relic_map: relic_map[item] = []
            if src not in relic_map[item]: relic_map[item].append(src)
        else:
            normal_drops.append(data)
            
    # 2. Group Normal Drops by Prefix Clustering
    grouped_sources = defaultdict(list)
    
    # Sort by source to enable adjacent prefix detection
    normal_drops.sort(key=lambda x: x['source'])
    
    items_to_process = normal_drops[:]
    
    while items_to_process:
        base = items_to_process.pop(0)
        group = [base]
        
        prefix = base['source'] # Default: Full source as key
        
        # Peek at next item to find potential prefix
        if items_to_process:
            next_item = items_to_process[0]
            common = os.path.commonprefix([base['source'], next_item['source']])
            
            # Valid prefix criteria:
            # 1. Length > 5 chars (avoid "The " or short generic prefixes)
            # 2. Must align with word boundary (end in space or punctuation)
            if len(common) > 5:
                # Truncate to last space to ensure word boundary
                last_space = common.rfind(' ')
                if last_space != -1:
                    candidate_prefix = common[:last_space+1]
                    if len(candidate_prefix) > 5:
                        prefix = candidate_prefix
        
        # If we identified a clustering prefix, gather all matching items
        if prefix != base['source']:
            # We already have 'base' in group. Check others.
            i = 0
            while i < len(items_to_process):
                if items_to_process[i]['source'].startswith(prefix):
                    group.append(items_to_process.pop(i))
                    # Since list is sorted, we assume all matches are contiguous. 
                    # But we use while loop with index 0 to pop consistently.
                    # Wait, if we pop(i), the next item shifts to i. So we stay at i.
                else:
                    # Stop at first mismatch because list is sorted
                    break
        
        group_key = prefix.strip()
        
        for data in group:
            src = data['source']
            item_name = data['item_name']
            
            # --- REDUNDANCY CHECK ---
            is_redundant = False
            
            # 1. Check against English Query (DB)
            if data['item_id_en'].lower() == data['original_query'].lower(): is_redundant = True
            
            # 2. Check against User Input (Spanish/English mixed)
            if item_name.lower() == data['user_query'].lower(): is_redundant = True
            if data['user_query'].lower() in item_name.lower() and len(item_name) < len(data['user_query']) + 10: is_redundant = True
            
            # 3. Check against Cleaned English Query
            if data['item_id_en'].lower() in data['original_query'].lower(): is_redundant = True

            if item_name == "Plano Principal": is_redundant = False # Always show "Plano Principal"
            
            chance_val = data['chance']
            if chance_val < 1: chance_str = f"({chance_val:.2f}%)"
            else: chance_str = f"({chance_val:.0f}%)"
            
            if is_redundant:
                display_str = chance_str
            else:
                display_str = f"{item_name} {chance_str}"
                
            # Extract Suffix
            if src.startswith(prefix) and prefix != src:
                suffix = src[len(prefix):].strip()
            else:
                # If prefix == src (no grouping), suffix is empty? 
                # Or rather, the loop logic sets group_key = src in that case.
                # So suffix is empty.
                suffix = ""
                
            grouped_sources[group_key].append({'suffix': suffix, 'display': display_str})

    final_string_parts = []
    
    # 3. Format Normal Drops
    # Use || as separator for groups
    group_strings = []
    
    for base_loc in sorted(grouped_sources.keys()):
        items = grouped_sources[base_loc]
        
        # Format: "Base: Suffix1 (X%) | Suffix2 (Y%)"
        sub_parts = []
        for it in items:
            s = it['suffix']
            d = it['display']
            
            if s:
                # Clean suffix
                s = s.strip()
                if s.startswith(":"): s = s[1:].strip()
                sub_parts.append(f"{s} {d}")
            else:
                sub_parts.append(d)
        
        # Join details with " | "
        details_joined = " | ".join(sub_parts)
        group_strings.append(f"{base_loc}: {details_joined}")
    
    if group_strings:
        final_string_parts.append(" || ".join(group_strings))

    # 4. Format Relics (Legacy Format)
    relic_parts = []
    for item, relics in relic_map.items():
        relics.sort()
        relics_str = ", ".join(relics)
        relic_parts.append(f"{item}: {relics_str}")
    
    if relic_parts:
        prime_label = "📦 **PRIME:** "
        prefix = f" {prime_label}" if group_strings else prime_label
        final_string_parts.append(prefix + " | ".join(relic_parts))
    
    return f"Drops para **{query}**: " + "".join(final_string_parts)

def get_relic_contents(db_path, query):
    """
    Busca el contenido de una reliquia específica.
    Ej: "Neo T1" -> Lista de items y rarezas.
    """
    if not query or len(query) < 4: return "Por favor especifica la reliquia (ej: !info Neo T1)"
    
    # Normalize input
    query = query.strip()
    
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        
        # 1. Try constructing "Era Code Relic"
        parts = query.split()
        target_source = None
        
        if len(parts) >= 2:
            era = parts[0].capitalize()
            code = parts[1].upper()
            base_name = f"{era} {code}"
            target_base = f"{base_name} Relic"
            
            # Try Exact Match first
            c.execute("SELECT source FROM drops WHERE source = ? LIMIT 1", (target_base,))
            res = c.fetchone()
            
            if res:
                target_source = res[0]
            else:
                # Try with (Intact) suffix - standard in new DB
                target_intact = f"{target_base} (Intact)"
                c.execute("SELECT source FROM drops WHERE source = ? LIMIT 1", (target_intact,))
                res = c.fetchone()
                if res:
                    target_source = res[0]
                else:
                    # Try any quality suffix
                    c.execute("SELECT source FROM drops WHERE source LIKE ? LIMIT 1", (f"{target_base} (%)",))
                    res = c.fetchone()
                    if res:
                        target_source = res[0]
            
            if target_source:
                c.execute("SELECT item, chance FROM drops WHERE source = ? ORDER BY chance DESC", (target_source,))
                results = c.fetchall()
            else:
                results = []
        else:
            results = []
            base_name = query
        
        # 2. Fuzzy fallback if exact construction failed
        if not results:
            # Try finding a relic source that matches the query broadly
            # We look for anything containing the query and "Relic"
            c.execute("SELECT DISTINCT source FROM drops WHERE source LIKE ? AND source LIKE '%Relic%' LIMIT 10", (f"%{query}%",))
            candidates = [row[0] for row in c.fetchall()]
            
            best_candidate = None
            # Prefer (Intact) versions
            for cand in candidates:
                if "(Intact)" in cand:
                    best_candidate = cand
                    break
            
            if not best_candidate and candidates:
                best_candidate = candidates[0]
                
            if best_candidate:
                target_source = best_candidate
                # Extract clean name for display
                base_name = target_source.replace(" Relic", "").replace(" (Intact)", "").split("(")[0].strip()
                c.execute("SELECT item, chance FROM drops WHERE source = ? ORDER BY chance DESC", (target_source,))
                results = c.fetchall()
        
        if not results:
            return f"No encontré la reliquia '**{query}**'. Asegúrate de usar el formato 'Era Código' (ej: Neo T1)."
            
        # Group by Rarity
        common = []
        uncommon = []
        rare = []
        
        for item_en, chance in results:
            # Translate item
            item_es = translate_item_name(db_path, item_en)
            item_clean = translate_common_terms(item_es)
            
            # Use chance to determine tier (Intact values)
            # Common: ~25.33% (Total ~76%)
            # Uncommon: ~11% (Total ~22%)
            # Rare: ~2% (Total ~2%)
            
            if chance > 20:
                common.append(item_clean)
            elif chance > 5:
                uncommon.append(item_clean)
            else:
                rare.append(item_clean)
                
        # Format Output
        response = f"Contenido de **{base_name}**:"
        if rare:
            response += f" 🥇 **Raro**: {', '.join(rare)} |"
        if uncommon:
            response += f" 🥈 **Poco Común**: {', '.join(uncommon)} |"
        if common:
            response += f" 🥉 **Común**: {', '.join(common)}"
            
        return response
