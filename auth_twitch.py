import os
import requests
import webbrowser
from flask import Flask, request
from dotenv import load_dotenv
import json
import threading
import time
import sys

# Cargar variables de entorno (busca .env en el directorio actual)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(ROOT_DIR, '.env')
load_dotenv(ENV_PATH)

CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')
REDIRECT_URI = os.getenv('TWITCH_REDIRECT_URI', 'http://localhost:3000')
SCOPES = 'chat:read chat:edit'

app = Flask(__name__)
# Desactivar logs de Flask para mantener la consola limpia
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def update_env_file(key, value):
    """Actualiza o añade una clave en el archivo .env"""
    lines = []
    key_found = False
    
    # Leer archivo existente
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
    # Preparar el nuevo contenido
    new_lines = []
    for line in lines:
        # Si la línea comienza con la clave (y no está comentada), la reemplazamos
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            key_found = True
        else:
            new_lines.append(line)
    
    # Si no se encontró, se añade al final
    if not key_found:
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines.append('\n')
        new_lines.append(f"{key}={value}\n")
            
    # Escribir todo de nuevo
    with open(ENV_PATH, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

def get_user_info(access_token):
    """Obtiene información del usuario usando la API de Twitch"""
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {access_token}'
    }
    try:
        response = requests.get('https://api.twitch.tv/helix/users', headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data['data']:
                return data['data'][0]['login']
    except Exception as e:
        print(f"[ERROR] No se pudo obtener información del usuario: {e}")
    return None

@app.route('/', methods=['GET'])
def index():
    code = request.args.get('code')
    if not code:
        return "Servidor de autenticación de Twitch funcionando. Esperando código de autorización...", 200
    
    # Intercambiar código por token
    token_url = 'https://id.twitch.tv/oauth2/token'
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI
    }
    
    try:
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data['access_token']
            full_token = f"oauth:{access_token}"
            
            print(f"\n¡TOKEN OBTENIDO!: {full_token}")
            print(f"Actualizando archivo .env...")
            update_env_file("TWITCH_TOKEN", full_token)
            
            # --- NUEVO: OBTENER Y GUARDAR USUARIO AUTOMÁTICAMENTE ---
            print("Obteniendo información del usuario...")
            username = get_user_info(access_token)
            
            msg_extra = ""
            if username:
                print(f"Usuario detectado: {username}")
                update_env_file("TWITCH_USERNAME", username)
                # Por defecto, configuramos el canal objetivo como el mismo canal del usuario
                update_env_file("TARGET_CHANNEL", username)
                print(f"Configuración guardada: TWITCH_USERNAME={username}, TARGET_CHANNEL={username}")
                msg_extra = f"<p>Usuario detectado y configurado: <b>{username}</b></p>"
            else:
                print("[WARN] No se pudo detectar el nombre de usuario automáticamente.")
            
            print(f"Archivo .env actualizado correctamente.\n")
            print(f"=======================================================")
            print(f"   AUTENTICACION COMPLETADA CON EXITO")
            print(f"   Presiona ENTER para volver al menu principal...")
            print(f"=======================================================\n")
            
            return f"""
            <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: green;">¡Autenticación Exitosa!</h1>
                <p>Tu token de acceso es:</p>
                <code style="background: #eee; padding: 10px; font-size: 1.2em;">{full_token}</code>
                {msg_extra}
                <p style="color: blue; font-weight: bold;">¡El archivo .env se ha actualizado automáticamente!</p>
                <p>Ya puedes cerrar esta ventana y presionar ENTER en la consola.</p>
                <script>
                    setTimeout(function() {{
                        window.close();
                    }}, 5000);
                </script>
            </body>
            </html>
            """
        else:
            return f"Error obteniendo token: {response.text}", 400
            
    except Exception as e:
        return f"Error de conexión: {str(e)}", 500

def start_server():
    app.run(port=3000, use_reloader=False)

def run_auth():
    print("Iniciando proceso de autenticación...")
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: Faltan TWITCH_CLIENT_ID o TWITCH_CLIENT_SECRET en el archivo .env")
        print("Por favor, regístrate en https://dev.twitch.tv/console y obtén tus credenciales.")
        input("Presiona Enter para salir...")
        return

    auth_url = f"https://id.twitch.tv/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={SCOPES}"
    
    print("-" * 50)
    print("Abre esta URL en tu navegador para autorizar:")
    print(auth_url)
    print("-" * 50)
    
    # Iniciar servidor Flask en un hilo separado
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True # El hilo morirá cuando el programa principal termine
    server_thread.start()
    
    try:
        webbrowser.open(auth_url)
    except:
        pass
        
    print(f"Esperando respuesta en {REDIRECT_URI}...")
    print("\n[INFO] El servidor esta corriendo en segundo plano.")
    input("Presiona ENTER en cualquier momento para detener el servidor y volver al menu...\n")
    print("Cerrando servidor...")
    sys.exit(0)

if __name__ == '__main__':
    run_auth()
