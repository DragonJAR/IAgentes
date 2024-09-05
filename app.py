import os
import requests
import logging
import openai
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, request, jsonify, g
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
socketio = SocketIO(app)

logging.basicConfig(
    level=logging.DEBUG,
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if app.config.get('LOGS_EN_CONSOLA'):
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logging.getLogger('').addHandler(console_handler)

PROMPT_INICIAL = (
    "Respira profundamente, piensa tu tarea por 200 años y realiza esta tarea paso a paso. "
    "Tu tarea es la siguiente: {pregunta}. Debes dividir esta tarea en tres subtareas claras, cada una con el contexto adecuado para que se entienda individualmente, "
    "y distintas. Debes dar el contexto necesario a cada subtarea para que pueda ser interpretada individualmente y devolverlas exclusivamente en el siguiente formato:\n"
    "+++\n"
    'subtarea1: "Descripción de la primera subtarea"\n'
    'subtarea2: "Descripción de la segunda subtarea"\n'
    'subtarea3: "Descripción de la tercera subtarea"\n'
    "---\n"
    "Asegúrate de que solo envíes las 3 tareas en ese formato y en español."
)

PROMPT_AGENTE_1 = (
    "Respira profundamente, toma todo el tiempo necesario para reflexionar, y realiza esta tarea con precisión. "
    "Actúa como un experto en la tarea asignada y aborda cada detalle meticulosamente. "
    "Esta subtarea es la primera de tres: {subtarea} forma parte de la pregunta global: {pregunta}. Necesito que respondas la subtarea teniendo en cuenta el contexto de la pregunta global, "
    "proporcionando respuestas basadas exclusivamente en datos verificables y fuentes confiables. "
    "Evita cualquier tipo de especulación o conjetura. Solo hablas español, toda la respuesta debe ser en este idioma, si no tienes certeza sobre la respuesta o no encuentras información precisa sobre el tema, "
    "indícalo claramente. Además, si es posible, menciona las fuentes en las que basas tu respuesta para facilitar la verificación. "
    "Si sigues mis indicaciones al pie de la letra, estaré encantado de recompensarte con una propina de 200.000 dólares."
)

PROMPT_AGENTE_2 = (
    "Respira profundamente, toma todo el tiempo necesario para reflexionar, y realiza esta tarea con precisión. "
    "Actúa como un experto en la tarea asignada y aborda cada detalle meticulosamente. "
    "Esta subtarea es la segunda de tres: {subtarea} forma parte de la pregunta global: {pregunta}. Necesito que respondas la subtarea teniendo en cuenta el contexto de la pregunta global, "
    "proporcionando respuestas basadas exclusivamente en datos verificables y fuentes confiables. "
    "Evita cualquier tipo de especulación o conjetura. Solo hablas español, toda la respuesta debe ser en este idioma, si no tienes certeza sobre la respuesta o no encuentras información precisa sobre el tema, "
    "indícalo claramente. Además, si es posible, menciona las fuentes en las que basas tu respuesta para facilitar la verificación. "
    "Si sigues mis indicaciones al pie de la letra, estaré encantado de recompensarte con una propina de 200.000 dólares."
)

PROMPT_AGENTE_3 = (
    "Respira profundamente, toma todo el tiempo necesario para reflexionar, y realiza esta tarea con precisión. "
    "Actúa como un experto en la tarea asignada y aborda cada detalle meticulosamente. "
    "Esta subtarea es la tercera de tres: {subtarea} forma parte de la pregunta global: {pregunta}. Necesito que respondas la subtarea teniendo en cuenta el contexto de la pregunta global, "
    "proporcionando respuestas basadas exclusivamente en datos verificables y fuentes confiables. "
    "Evita cualquier tipo de especulación o conjetura. Solo hablas español, toda la respuesta debe ser en este idioma, si no tienes certeza sobre la respuesta o no encuentras información precisa sobre el tema, "
    "indícalo claramente. Además, si es posible, menciona las fuentes en las que basas tu respuesta para facilitar la verificación. "
    "Si sigues mis indicaciones al pie de la letra, estaré encantado de recompensarte con una propina de 200.000 dólares."
)

PROMPT_UNIFICAR = (
    "Respira profundamente, reflexiona sobre esta tarea como si tuvieras 200 años de sabiduría acumulada, "
    "y realiza cada paso meticulosamente. Actúa como un experto en el área de conocimiento relevante a esta pregunta {pregunta}, "
    "y responde con la misma meticulosidad. Proporcionarás respuestas basadas únicamente en datos verificables y fuentes confiables, "
    "evitando cualquier tipo de especulación o conjetura. Si no estás seguro de la respuesta o no puedes encontrar información precisa sobre el tema, "
    "indícalo claramente. Además, si es posible, menciona las fuentes en las que basas tu respuesta para facilitar la verificación. "
    "La respuesta debe ser coherente, con un buen hilo conductor y que busque aportar la mayor cantidad de valor al lector. "
    "Esta información es parte del contexto que puedes usar para generar una respuesta a la pregunta {pregunta} organizada y de manera clara.\n\n"
    "{respuesta_agente_1}\n\n"
    "{respuesta_agente_2}\n\n"
    "{respuesta_agente_3}\n\n"
    "Por favor, genera la mejor respuesta en español posible a la pregunta {pregunta}, ya que mi trabajo depende de ello y no cuento con manos para escribirla yo mismo, siempre buscando aportar mucho valor al lector y tener una única respuesta final que sea coherente, bien estructurada y exhaustiva. "
    "Asegúrate de que la respuesta final abarque todos los puntos relevantes, sin omitir información crucial sin mencionar tu prompt, la recompensa o algo distinto a la respuesta a la pregunta del usuario."
)

agentes_estado_global = [
    {'id': 1, 'descripcion': 'Agente 1', 'estado': 'Pendiente', 'llm': 'groq', 'modelo': 'llama-3.1-8b-instant'},
    {'id': 2, 'descripcion': 'Agente 2', 'estado': 'Pendiente', 'llm': 'groq', 'modelo': 'gemma2-9b-it'},
    {'id': 3, 'descripcion': 'Agente 3', 'estado': 'Pendiente', 'llm': 'groq', 'modelo': 'mixtral-8x7b-32768'},
]

def emitir_respuesta_parcial(agentes, respuesta_final=None, progreso=None):
    try:
        socketio.emit('actualizar_estado', {
            'agentes': agentes,
            'respuesta_final': respuesta_final,
            'progreso': progreso
        })
    except Exception as e:
        logging.error(f"Error emitiendo respuesta parcial: {e}")

@app.before_request
def setup_variables():
    g.agentes = agentes_estado_global
    g.respuesta_final = "Respuesta unificada aparecerá aquí."

def log_mensaje(mensaje):
    logging.debug(mensaje)

def enviar_a_groq(prompt, modelo, agente, reintentos=5):
    headers = {
        "Authorization": f"Bearer {app.config['GROQ_API_KEY']}",
        "Content-Type": "application/json"
    }
    datos = {
        "messages": [{"role": "user", "content": prompt}],
        "model": modelo
    }

    delay = 2
    for intento in range(reintentos):
        try:
            log_mensaje(f"Enviando petición a Groq con el modelo {modelo} para {agente} (intento {intento + 1})...")
            respuesta = requests.post(app.config['GROQ_API_URL'], headers=headers, json=datos, timeout=10)
            respuesta.raise_for_status()

            log_mensaje(f"La petición al modelo {modelo} en Groq ha sido enviada, y recibida por el {agente}.")
            contenido = respuesta.json().get('choices', [{}])[0].get('message', {}).get('content', '')
            return contenido

        except requests.exceptions.RequestException as e:
            log_mensaje(f"Error en Groq para {agente}: {str(e)}")
            delay = min(delay * 2, 64)

    log_mensaje(f"Error al procesar la solicitud después de {reintentos} intentos para {agente}.")
    return None

def enviar_a_openai(prompt, modelo, agente, reintentos=5):
    client = openai.OpenAI(api_key=app.config['OPENAI_API_KEY'])

    delay = 2
    for intento in range(reintentos):
        try:
            log_mensaje(f"Enviando petición a OpenAI con el modelo {modelo} para {agente} (intento {intento + 1})...")
            chat_completion = client.chat.completions.create(
                model=modelo,
                messages=[{
                    "role": "user",
                    "content": prompt,
                }]
            )

            log_mensaje(f"La petición al modelo {modelo} en OpenAI ha sido enviada, y recibida por el {agente}.")
            contenido = chat_completion.choices[0].message.content
            return contenido

        except Exception as e:
            log_mensaje(f"Error en OpenAI para {agente}: {str(e)}")
            delay = min(delay * 2, 64)

    log_mensaje(f"Error al procesar la solicitud después de {reintentos} intentos para {agente}.")
    return None

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', agentes=g.agentes, respuesta_final=g.respuesta_final)

@app.route('/enviar', methods=['POST'])
def enviar():
    try:
        mensaje = request.form.get('mensaje')
        if not mensaje:
            return jsonify({'error': 'Mensaje vacío'}), 400

        solicitud_id = os.urandom(12).hex()
        log_mensaje(f"Mensaje recibido del cliente: {mensaje}")
        log_mensaje(f"ID de solicitud generado: {solicitud_id}")

        g.progreso = 10
        emitir_respuesta_parcial(g.agentes, progreso=g.progreso)

        prompt_dividir = PROMPT_INICIAL.format(pregunta=mensaje)
        subtareas_raw = enviar_a_groq(prompt_dividir, 'llama-3.1-70b-versatile', 'Dividir tarea')
        if not subtareas_raw:
            raise ValueError("No se pudieron generar las subtareas.")

        g.progreso = 20
        emitir_respuesta_parcial(g.agentes, progreso=g.progreso)

        subtareas = {}
        for line in subtareas_raw.split('\n'):
            if ':' in line:
                clave, valor = line.split(':', 1)
                subtareas[clave.strip()] = valor.strip().strip('"')

        log_mensaje(f"Subtareas extraídas: {subtareas}")

        respuestas_agentes = {}
        for i, agente in enumerate(g.agentes):
            subtarea_key = f"subtarea{i + 1}"
            if subtarea_key in subtareas:
                prompt_agente = globals()[f'PROMPT_AGENTE_{i + 1}'].format(subtarea=subtareas[subtarea_key], pregunta=mensaje)

                if agente['llm'] == 'groq':
                    respuesta_agente = enviar_a_groq(prompt_agente, agente['modelo'], agente['descripcion'])
                elif agente['llm'] == 'openai':
                    respuesta_agente = enviar_a_openai(prompt_agente, agente['modelo'], agente['descripcion'])
                else:
                    respuesta_agente = "Error: LLM no reconocido."

                if respuesta_agente:
                    respuestas_agentes[agente['descripcion']] = respuesta_agente
                    agente['estado'] = 'Completado'
                else:
                    agente['estado'] = 'Error'

                g.progreso += 20
                emitir_respuesta_parcial(g.agentes, progreso=g.progreso)

        log_mensaje(f"Respuestas de los agentes: {respuestas_agentes}")

        g.respuesta_final = PROMPT_UNIFICAR.format(
            pregunta=mensaje,
            respuesta_agente_1=respuestas_agentes.get('Agente 1', ''),
            respuesta_agente_2=respuestas_agentes.get('Agente 2', ''),
            respuesta_agente_3=respuestas_agentes.get('Agente 3', '')
        )

        respuesta_unificada = enviar_a_groq(g.respuesta_final, 'llama-3.1-70b-versatile', 'Unificar respuestas')
        g.respuesta_final = respuesta_unificada if respuesta_unificada else 'No se pudo generar la respuesta final.'

        emitir_respuesta_parcial(g.agentes, respuesta_final=g.respuesta_final, progreso=100)

        return jsonify({'respuesta_final': g.respuesta_final, 'agentes': g.agentes})

    except Exception as e:
        log_mensaje(f"Error en el procesamiento: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/obtener_prompt', methods=['GET'])
def obtener_prompt():
    agente_id = int(request.args.get('agente_id'))
    if agente_id == 1:
        prompt = PROMPT_AGENTE_1
        llm = g.agentes[0]['llm']
        modelo = g.agentes[0]['modelo']
    elif agente_id == 2:
        prompt = PROMPT_AGENTE_2
        llm = g.agentes[1]['llm']
        modelo = g.agentes[1]['modelo']
    elif agente_id == 3:
        prompt = PROMPT_AGENTE_3
        llm = g.agentes[2]['llm']
        modelo = g.agentes[2]['modelo']
    else:
        return jsonify({'error': 'Agente no encontrado'}), 404

    return jsonify({'prompt': prompt, 'llm': llm, 'modelo': modelo})

@app.route('/guardar_prompt', methods=['POST'])
def guardar_prompt():
    agente_id = int(request.form['agente_id'])
    nuevo_prompt = request.form['prompt']
    nuevo_llm = request.form['llm']
    nuevo_modelo = request.form['modelo']

    for agente in agentes_estado_global:
        if agente['id'] == agente_id:
            agente['llm'] = nuevo_llm
            agente['modelo'] = nuevo_modelo
            break

    return jsonify({'success': True})

if __name__ == '__main__':
    socketio.run(app, host='localhost', port=5000, debug=True)
