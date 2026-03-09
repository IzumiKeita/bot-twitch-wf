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

   - **TWITCH_TOKEN**: Necesitas un token de acceso (es como una contraseña para bots).
     - Ve a [https://twitchapps.com/tmi/](https://twitchapps.com/tmi/)
     - Conecta tu cuenta de Twitch (la del bot o la tuya).
     - Copia el texto que empieza por `oauth:...` y pégalo después del `=`.
   
   - **TWITCH_USERNAME**: El nombre de usuario de la cuenta de Twitch que usará el bot (puede ser tu propia cuenta o una cuenta secundaria para el bot).
   
   - **TARGET_CHANNEL**: El nombre de tu canal de Twitch (donde quieres que el bot hable). Escríbelo en minúsculas (sin el `#`, el bot lo pone solo).

   **Ejemplo de cómo debe quedar el archivo .env:**
   ```env
   TWITCH_TOKEN=oauth:a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5
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
  - Tu token de Twitch ha caducado o está mal copiado. Vuelve a generar uno en [twitchapps.com/tmi](https://twitchapps.com/tmi/) y actualiza el archivo `.env`.

- **El bot no responde en el chat:**
  - Asegúrate de que el `TARGET_CHANNEL` sea correcto (el nombre de tu canal).
  - El bot puede tardar unos segundos en conectarse.

¡Disfruta de tu Warframe Helper! 🚀
