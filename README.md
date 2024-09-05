# IAgentes - Multiagente de LLM para mejorar las respuestas

![IAgentes Logo](static/IAgentes.png)

**IAgentes** es una aplicación web sencilla que, mediante una interfaz tipo chat, permite tomar una solicitud específica, dividirla en subtareas, y enviar cada subtarea a un modelo de LLM (Large Language Model) diferente. Luego, se recopilan todas las respuestas como contexto para ofrecer una solución más completa que si se enviara a un solo modelo LLM. La aplicación fue desarrollada principalmente para probar las capacidades de **v0.dev** y en poco tiempo se obtuvo este resultado. Funciona con **Flask** y **Flask-SocketIO**, lo que permite la comunicación en tiempo real entre el cliente y los agentes. Estos agentes interactúan con diferentes APIs (Groq y OpenAI) para obtener respuestas precisas y unificarlas en una única respuesta final.

[![Ver el video](https://img.youtube.com/vi/gpcyIe4PRf8/0.jpg)](https://youtu.be/gpcyIe4PRf8)

## Estructura del Proyecto

El proyecto está organizado de la siguiente manera:

```
/IAgentes
│
├── app.py                      # Archivo principal de la aplicación Flask
├── config.py                   # Archivo de configuración donde se definen las APIs y los logs
├── /templates
│   └── index.html              # Plantilla HTML principal de la interfaz web
├── /static
│   ├── styles.css              # Estilos CSS para la interfaz de usuario
│   ├── IAgentes.png            # Imagen del logo utilizada en el README y la interfaz
│   └── scripts.js              # Lógica del frontend con JQuery y Socket.IO
└── app.log                     # Archivo de logs para el registro de errores y eventos
```

## Requerimientos

Este proyecto requiere las siguientes dependencias:

- Python 3.8 o superior
- Flask 2.x
- Flask-SocketIO
- requests
- openai

Instala las dependencias con `pip`:

```bash
pip install flask flask-socketio requests openai
```

## Configuración

El archivo `config.py` contiene las configuraciones necesarias para la aplicación, incluyendo las claves API y las URLs de los servicios Groq y OpenAI.

Ejemplo de configuración (`config.py`):

```python
import os

class Config:
    GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "AQUI-PONES-LA-API")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "AQUI-PONES-LA-API")
    LOGS_EN_CONSOLA = os.getenv("LOGS_EN_CONSOLA", "True").lower() in ["true", "1", "t"]
```

Asegúrate de configurar las variables de entorno con las claves API de Groq y OpenAI.

## Ejecución

Para ejecutar la aplicación, sigue estos pasos:

1. Clona el repositorio:
    ```bash
    git clone https://github.com/tu_usuario/IAgentes.git
    ```

2. Navega al directorio del proyecto:
    ```bash
    cd IAgentes
    ```

3. Instala las dependencias requeridas:
    ```bash
    pip install -r requirements.txt
    ```

4. Ejecuta la aplicación Flask con Socket.IO:
    ```bash
    python app.py
    ```

La aplicación estará disponible en `http://localhost:5000`.

## Funcionalidad

La funcionalidad principal de esta herramienta es proporcionar una interfaz web que permite ingresar una pregunta o tarea compleja. Dicha tarea será dividida en subtareas específicas, que serán distribuidas entre los agentes. A cada agente se le puede cambiar tanto el prompt como el modelo LLM a utilizar. Los agentes retornan respuestas parciales que luego se unifican y se entregan como contexto a un modelo final que generará una respuesta mucho más completa y especializada, comparada con el uso de un solo modelo LLM.

## Logs

El archivo `app.log` almacena todos los eventos y errores registrados por la aplicación. Si la opción `LOGS_EN_CONSOLA` está habilitada como `True` en `config.py`, los logs también se imprimirán en la consola.
