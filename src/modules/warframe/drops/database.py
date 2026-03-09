import sqlite3
import os
import requests
import time

def init_db(db_path):
    """Inicializa la base de datos si no existe."""
    dir_name = os.path.dirname(db_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    try:
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS drops
                         (source TEXT, item TEXT, rarity TEXT, chance REAL, category TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS translations
                         (english_name TEXT PRIMARY KEY, spanish_name TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS meta
                         (key TEXT PRIMARY KEY, value TEXT)''')
            conn.commit()
    except Exception as e:
        print(f"[DROPS] Error inicializando DB: {e}")

def update_translations(db_path):
    """Actualiza la tabla de traducciones usando la API de Warframe Market (v2)."""
    print("[DROPS] Actualizando traducciones desde Warframe Market API v2...")
    try:
        url = "https://api.warframe.market/v2/items"
        headers = {
            'Language': 'es',
            'platform': 'pc'
        }
        # Intentar obtener la lista de items
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"[DROPS] Error al obtener traducciones: {response.status_code}")
            return

        data_json = response.json()
        items_data = data_json.get('data', [])
        
        if not items_data:
            print("[DROPS] No se encontraron items en la respuesta de WFM.")
            return

        print(f"[DROPS] Procesando {len(items_data)} traducciones...")
        
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            # Insertar o reemplazar traducciones
            count = 0
            for item in items_data:
                i18n = item.get('i18n', {})
                en_name = i18n.get('en', {}).get('name')
                es_name = i18n.get('es', {}).get('name')
                
                if en_name and es_name:
                    c.execute("INSERT OR REPLACE INTO translations (english_name, spanish_name) VALUES (?, ?)", (en_name, es_name))
                    count += 1
            
            conn.commit()
            print(f"[DROPS] Traducciones actualizadas: {count} items insertados.")
            
    except Exception as e:
        print(f"[DROPS] Excepción actualizando traducciones: {e}")

def translate_item_name(db_path, english_name):
    """Traduce el nombre del item usando la base de datos."""
    try:
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT spanish_name FROM translations WHERE english_name = ?", (english_name,))
            res = c.fetchone()
            if res:
                return res[0]
    except Exception:
        pass
    return english_name

def save_to_db(db_path, drops_list, lock=None):
    if not drops_list: return False
    try:
        # Context manager for lock if provided
        class DummyLock:
            def __enter__(self): pass
            def __exit__(self, exc_type, exc_val, exc_tb): pass
            
        lock_ctx = lock if lock else DummyLock()
        
        with lock_ctx:
            with sqlite3.connect(db_path) as conn:
                c = conn.cursor()
                c.execute("DELETE FROM drops")
                c.executemany("INSERT INTO drops VALUES (?,?,?,?,?)", drops_list)
                c.execute("REPLACE INTO meta (key, value) VALUES ('last_update', ?)", (str(time.time()),))
                conn.commit()
        print(f"[DROPS] Base de datos guardada exitosamente. {len(drops_list)} registros.")
        return True
    except Exception as e:
        print(f"[DROPS] Error guardando en DB: {e}")
        return False
