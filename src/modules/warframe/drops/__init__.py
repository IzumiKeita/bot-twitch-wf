import os
import threading
import time
import sqlite3

from .database import init_db, update_translations, save_to_db, translate_item_name
from .scraper import update_from_web, update_from_json
from .logic import get_formatted_response, get_relic_contents

# Definir ruta de la DB en la carpeta /data del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
DB_PATH = os.path.join(BASE_DIR, 'data', 'drop_wf.db')
JSON_SOURCE_PATH = os.path.join(BASE_DIR, 'data', 'warframe_drops_backup.json')
URL = "https://www.warframe.com/droptables"

class WarframeDropManager:
    def __init__(self):
        self.db_path = DB_PATH
        self.lock = threading.Lock()
        init_db(self.db_path)

    def update_database(self):
        """Ejecuta la actualización de la base de datos (y traducciones)."""
        # Verificar si la DB necesita actualización (vacía o > 48h)
        needs_update = False
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT count(*) FROM drops")
                count = c.fetchone()[0]
                if count == 0:
                    needs_update = True
                else:
                    c.execute("SELECT value FROM meta WHERE key='last_update'")
                    last_update = c.fetchone()
                    if last_update:
                        last_ts = float(last_update[0])
                        if time.time() - last_ts > 48 * 3600:
                            needs_update = True
                    else:
                        needs_update = True
        except sqlite3.OperationalError:
            needs_update = True

        if needs_update:
            print("[DROPS] Iniciando actualización de base de datos...")
            # Ejecutar scrape en un hilo separado para no bloquear el bot
            thread = threading.Thread(target=self._run_update_process)
            thread.start()
        else:
            print("[DROPS] Base de datos actualizada recientemente.")

    def _run_update_process(self):
        """Proceso real de actualización (scraping + traducciones)."""
        # 1. Actualizar traducciones primero (rápido)
        update_translations(self.db_path)
        
        # 2. Actualizar drops (prioridad JSON local, luego web)
        drops = None
        if os.path.exists(JSON_SOURCE_PATH):
             drops = update_from_json(JSON_SOURCE_PATH)
             if drops:
                 save_to_db(self.db_path, drops, self.lock)
                 return

        drops = update_from_web(URL)
        if drops:
            save_to_db(self.db_path, drops, self.lock)

    def get_formatted_response(self, query, category=None):
        return get_formatted_response(self.db_path, query, category)

    def get_relic_contents(self, query):
        return get_relic_contents(self.db_path, query)

    def translate_item_name(self, english_name):
        return translate_item_name(self.db_path, english_name)

# Exportar instancia única para uso global
drops_manager = WarframeDropManager()
