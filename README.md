# Bot de Warframe Standalone para Twitch

¡Hola! Este es un bot de Twitch diseñado para ayudarte a ti y a tus espectadores con información rápida sobre Warframe. Es ligero, fácil de usar y no requiere una instalación complicada.

## ¿Qué puede hacer este bot?

- **Buscar Drops:** Encuentra dónde caen partes de Warframes, armas y más.
- **Información de Reliquias:** Muestra qué contiene una reliquia específica.
- **Estados de Mundos Abiertos:** Te dice si es de día o de noche en Cetus, el clima en Vallis, o el ciclo de Deimos.
- **Eventos:** Información sobre Baro Ki'Teer, Incursiones (Sorties), Cacerías de Arcontes y el Circuito.

---

## 🛠️ Instalación Paso a Paso

### 1. Requisitos Previos

Necesitas tener instalado **Python** en tu computadora.
- Descarga Python (versión 3.10 o superior) desde [python.org](https://www.python.org/downloads/).
- **IMPORTANTE:** Al instalar, asegúrate de marcar la casilla que dice **"Add Python to PATH"** antes de darle a "Install Now".

### 2. Descargar el Bot

Si te han pasado este archivo como un `.zip`, descomprímelo en una carpeta (por ejemplo, en tu Escritorio o Documentos).

### 3. Instalar Dependencias

El bot necesita algunas "librerías" para funcionar.
1. Abre la carpeta del bot.
2. Haz clic derecho en un espacio vacío y selecciona "Abrir en Terminal" (o escribe `cmd` en la barra de dirección de la carpeta y presiona Enter).
3. Escribe el siguiente comando y presiona Enter:
   ```bash
   pip install -r requirements.txt
   ```
   Espera a que termine de instalarse todo.

---

## ⚙️ Configuración

Para que el bot se conecte a tu chat de Twitch, necesitas configurarlo.

1. En la carpeta del bot, verás un archivo llamado `.env.example`.
2. Haz una copia de ese archivo y cámbiale el nombre a `.env` (sin el `.example`).
3. Abre el archivo `.env` con el Bloc de Notas.
4. Rellena los datos:

   Existen dos formas de obtener tu token:

   **Opción A: Método Automático (Recomendado)**
   Este método usa el generador incluido en el bot. Es más seguro y no dependes de terceros.
   1. Ve a la [Consola de Desarrolladores de Twitch](https://dev.twitch.tv/console).
   2. Inicia sesión y pulsa en **"Register Your Application"**.
   3. Rellena los datos:
      - **Name**: Un nombre único (ej: `MiBotWarframe_TuNombre`).
      - **OAuth Redirect URLs**: Escribe `http://localhost:3000` y dale a "Add".
      - **Category**: Selecciona "Chat Bot".
      - Pulsa "Create".
   4. En tu nueva aplicación, pulsa "Manage".
   5. Copia el **Client ID** y pégalo en tu archivo `.env`.
   6. Pulsa en "New Secret", acepta, copia el **Client Secret** y pégalo en tu `.env`.
   7. Guarda el archivo `.env`.
   8. Ejecuta `start_bot.bat` y selecciona la **Opción 2**. ¡El token se guardará solo!

   **Opción B: Método Rápido (Herramienta de Terceros)**
   Si no quieres crear una aplicación, puedes usar un generador externo confiable.
   1. Ve a [Twitch Token Generator](https://twitchtokengenerator.com/).
   2. Selecciona "Custom Scope Token".
   3. Activa las casillas `chat:read` y `chat:edit`.
   4. Genera el token, autoriza y copia el "Access Token".
   5. Pégalo en tu `.env` donde dice `TWITCH_TOKEN=oauth:tu_token_aqui`.

   **Ejemplo de cómo debe quedar el archivo .env (Opción A):**
   ```env
   # Credenciales de la App (para el generador automático)
   TWITCH_CLIENT_ID=tu_cliente_id_largo
   TWITCH_CLIENT_SECRET=tu_secreto_largo
   
   # El bot rellenará esto solo tras usar la Opción 2 del menú
   TWITCH_TOKEN=
   
   TWITCH_USERNAME=MiBotDeWarframe
   TARGET_CHANNEL=mi_canal_de_twitch
   ```
5. Guarda el archivo.

---

## ▶️ Cómo Iniciar el Bot

Simplemente haz doble clic en el archivo `start_bot.bat`.
Se abrirá una ventana negra (la consola) que te dirá "Conectado a #tucanal".
¡Listo! El bot ya está escuchando en el chat.

Para apagarlo, simplemente cierra esa ventana o presiona `Ctrl + C`.

---

## 🤖 Lista de Comandos

Aquí tienes todos los comandos que pueden usar tus espectadores:

### Búsquedas de Farm (Drops)
- **`!drop <item>`** / **`!farm <item>`** / **`!donde <item>`**
  - Busca dónde conseguir un objeto, plano o parte.
  - *Ejemplo:* `!drop wisp`, `!farm nikana prime`

### Recursos y Mods
- **`!recurso <nombre>`** / **`!res <nombre>`**
  - Busca dónde farmear recursos específicos.
  - *Ejemplo:* `!recurso oxium`, `!res células orokin`
- **`!mod <nombre>`**
  - Busca dónde cae un mod.
  - *Ejemplo:* `!mod mordisco`, `!mod adaptación`
- **`!arcano <nombre>`**
  - Busca información sobre arcanos.
  - *Ejemplo:* `!arcano gracia`

### Reliquias
- **`!reliquia <nombre>`** / **`!info <nombre>`** / **`!relic <nombre>`**
  - Muestra qué partes contiene una reliquia y sus rarezas.
  - *Ejemplo:* `!reliquia Neo T1`, `!info Axi L4`

### Mundos Abiertos y Eventos
- **`!cetus`**: Muestra si es de día o de noche en las Llanuras de Eidolon.
- **`!vallis`**: Muestra el ciclo de clima en los Valles del Orbe (Cálido/Frío).
- **`!deimos`**: Muestra el ciclo de Vome/Fass en Deriva Cambion.
- **`!baro`**: Te dice cuándo llega el Comerciante del Vacío o qué trae si ya está aquí.
- **`!sortie`**: Muestra la Incursión diaria (misiones y condiciones).
- **`!archon`**: Muestra la Cacería de Arcontes activa.
- **`!circuito`**: Muestra la rotación actual del Circuito (Warframes disponibles).
- **`!circuito_steel`**: Muestra las armas Incarnon disponibles en el Circuito Camino de Acero.

---

## ❓ Solución de Problemas

- **El bot se cierra inmediatamente al abrir:**
  - Asegúrate de haber instalado Python y las dependencias (`pip install ...`).
  - Revisa que el archivo `.env` esté bien escrito y guardado.

- **Error "Login authentication failed":**
  - Tu token de Twitch ha caducado o está mal copiado. 
  - Si usas el **Método Automático**, ejecuta `start_bot.bat`, elige la opción 2 y vuelve a autorizar.
  - Si usas el **Método Rápido**, genera uno nuevo en [Twitch Token Generator](https://twitchtokengenerator.com/) y actualiza el `.env`.

- **El bot no responde en el chat:**
  - Asegúrate de que el `TARGET_CHANNEL` sea correcto (el nombre de tu canal).
  - El bot puede tardar unos segundos en conectarse.

¡Disfruta de tu Warframe Helper! 🚀
