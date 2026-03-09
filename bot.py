import os
import sys
import socket
import time
import threading
from dotenv import load_dotenv

# Añadir el directorio actual al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.modules.warframe import WarframeModule
except ImportError as e:
    print(f"Error importando módulo Warframe: {e}")
    print("Asegúrate de que la carpeta 'src' y 'src/modules/warframe' existan.")
    input("Presiona Enter para salir...")
    sys.exit(1)

# Cargar variables de entorno
load_dotenv()

# Configuración
HOST = "irc.chat.twitch.tv"
PORT = 6667
TOKEN = os.getenv("TWITCH_TOKEN")
USERNAME = os.getenv("TWITCH_USERNAME")
CHANNEL = os.getenv("TARGET_CHANNEL")

# Validación precisa de variables
missing_vars = []
if not TOKEN: missing_vars.append("TWITCH_TOKEN")
if not USERNAME: missing_vars.append("TWITCH_USERNAME")
if not CHANNEL: missing_vars.append("TARGET_CHANNEL")

if missing_vars:
    print("\n" + "="*50)
    print(" [ERROR] FALTAN VARIABLES DE CONFIGURACIÓN EN .ENV")
    print("="*50)
    print(f"Las siguientes variables no se encontraron o están vacías: {', '.join(missing_vars)}")
    print("\nSolución:")
    print("1. Ejecuta 'start_bot.bat' y selecciona la opción 2 (Generador de Token).")
    print("   Esto configurará automáticamente el Token, Usuario y Canal.")
    print("2. O edita manualmente el archivo '.env' y añade los valores faltantes.")
    print("="*50 + "\n")
    
    # Crear .env completo desde plantilla si no existe
    if not os.path.exists(".env"):
        example_path = ".env.example"
        if os.path.exists(example_path):
            try:
                with open(example_path, "r", encoding="utf-8") as f_src:
                    content = f_src.read()
                with open(".env", "w", encoding="utf-8") as f_dst:
                    f_dst.write(content)
                print(f"[INFO] Se ha creado un archivo '.env' nuevo basado en '{example_path}'.")
                print("Por favor, ábrelo y completa tus datos.")
            except Exception as e:
                print(f"[WARN] No se pudo copiar .env.example: {e}")
        else:
            # Fallback básico si no existe .env.example
            with open(".env", "w") as f:
                f.write("TWITCH_TOKEN=oauth:tutokenaqui\nTWITCH_USERNAME=tuusuario\nTARGET_CHANNEL=canalobjetivo\nTWITCH_CLIENT_ID=\nTWITCH_CLIENT_SECRET=\n")
            print("Se ha creado un archivo .env de ejemplo básico. Edítalo con tus datos.")
    
    input("Presiona Enter para salir...")
    sys.exit(1)

# Asegurar formato de canal
if not CHANNEL.startswith("#"):
    CHANNEL = "#" + CHANNEL

class StandaloneBot:
    def __init__(self):
        self.irc = socket.socket()
        self.warframe_module = WarframeModule(self) # Pasar self como instancia del bot
        self.running = True

    def connect(self):
        print(f"Conectando a {HOST}:{PORT} como {USERNAME}...")
        try:
            self.irc = socket.socket()
            self.irc.connect((HOST, PORT))
            self.irc.send(f"PASS {TOKEN}\n".encode("utf-8"))
            self.irc.send(f"NICK {USERNAME}\n".encode("utf-8"))
            
            # --- CRITICAL FIX: Request Capabilities ---
            # Esto es necesario para ver los mensajes de los usuarios correctamente
            # y recibir metadata extra si fuera necesario.
            self.irc.send(b"CAP REQ :twitch.tv/membership twitch.tv/tags twitch.tv/commands\r\n")
            
            self.irc.send(f"JOIN {CHANNEL}\n".encode("utf-8"))
            print(f"¡Conectado a {CHANNEL}!")
            return True
        except Exception as e:
            print(f"Fallo de conexión: {e}")
            return False

    def send_message(self, message):
        try:
            # Límite de Twitch: ~500 caracteres. Usamos 450 para seguridad.
            # Dividir mensaje en chunks si es muy largo
            max_length = 450
            chunks = [message[i:i+max_length] for i in range(0, len(message), max_length)]
            
            for chunk in chunks:
                self.irc.send(f"PRIVMSG {CHANNEL} :{chunk}\r\n".encode("utf-8"))
                print(f"Bot: {chunk}")
                time.sleep(0.5) # Pequeña pausa para evitar flood limit
                
        except Exception as e:
            print(f"Error enviando mensaje: {e}")

    def run(self):
        if not self.connect():
            input("Presiona Enter para salir...")
            return

        print("Bot en ejecución. Presiona Ctrl+C para detener.")
        print(f"Esperando mensajes en {CHANNEL}...")
        
        readbuffer = ""
        while self.running:
            try:
                # Usar errors='ignore' para evitar crasheos con emojis raros
                chunk = self.irc.recv(2048).decode("utf-8", errors='ignore')
                if not chunk:
                    print("Conexión perdida (buffer vacío). Reconectando...")
                    time.sleep(2) # Esperar un poco antes de reconectar
                    self.connect()
                    continue
                    
                readbuffer = readbuffer + chunk
                temp = readbuffer.split("\n")
                readbuffer = temp.pop()

                for line in temp:
                    # Parseo básico de IRC para Twitch con Tags
                    # Ejemplo: @badge-info=;badges=broadcaster/1;color=#0000FF;... :usuario!usuario@usuario.tmi.twitch.tv PRIVMSG #canal :mensaje
                    
                    if line.startswith("PING"):
                        self.irc.send(b"PONG :tmi.twitch.tv\r\n")
                        continue
                        
                    # Extraer usuario y mensaje
                    user = ""
                    message = ""
                    
                    try:
                        parts = line.split(":", 2)
                        if "PRIVMSG" in line:
                            # Formato complejo con tags
                            if "PRIVMSG" in parts[1]: 
                                # ... :usuario! ... PRIVMSG ...
                                user_part = parts[1].split("!")[0]
                                user = user_part
                                message = parts[2]
                            else:
                                # Formato simple (a veces pasa en servidores antiguos o sin tags)
                                # :usuario!usuario@... PRIVMSG #canal :mensaje
                                if len(parts) >= 3:
                                    user = parts[1].split("!")[0]
                                    message = parts[2]
                            
                            user = user.strip()
                            message = message.strip()
                            
                            # DEBUG: Ver qué llega realmente
                            # print(f"[RAW] {user}: {message}")
                            
                            if message:
                                # Procesar con módulo Warframe
                                response = self.warframe_module.handle_message(message, user)
                                if response:
                                    self.send_message(response)
                                    
                    except Exception as e:
                        print(f"Error parseando línea: {line} -> {e}")

            except KeyboardInterrupt:
                print("\nDeteniendo bot...")
                self.running = False
            except Exception as e:
                print(f"Error en bucle principal: {e}")
                time.sleep(1)

if __name__ == "__main__":
    bot = StandaloneBot()
    bot.run()
