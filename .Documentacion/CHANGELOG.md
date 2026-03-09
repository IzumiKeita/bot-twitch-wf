# Registro de Cambios

## 2026-03-09
- Preparación del repositorio para GitHub:
  - Creación de `.gitignore` para excluir archivos sensibles y temporales.
  - Estandarización de `requirements.txt` con versiones fijas.
  - Inicialización del control de versiones Git.
- Actualización de Documentación:
  - Se actualizó `README.md` y `.env.example` para reflejar el nuevo sistema de autenticación, eliminando referencias a la herramienta descontinuada `twitchapps.com/tmi`.
  - Se documentó el uso del generador de tokens integrado (Opción 2 del menú).
  - Se limpió el archivo `.env.example` eliminando configuraciones de IA no utilizadas (LM Studio) para evitar confusiones.

## 2026-03-08
- Mejora en `bot.py`:
  - Ahora genera un archivo `.env` completo (basado en `.env.example`) si no se encuentra ninguno al iniciar.
  - Validación de variables de entorno mejorada.
- Creación de `.env.example`:
  - Plantilla limpia y documentada para distribución. Contiene todos los campos necesarios vacíos para que el usuario final los rellene.
- Mejora en `auth_twitch.py`:
  - Detección automática de usuario y canal.
  - Ejecución en hilo secundario.
- Mejora crítica en `start_bot.bat`:
  - Menú principal y detección de Python.
- Actualización de `requirements.txt`: Se añadió `flask`.
- Corrección de errores de sintaxis en el lanzador.
- Actualización completa del README.md.
