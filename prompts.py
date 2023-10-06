import uuid
import openai
import json
from flask import request, session
from flask_socketio import emit
from utils import error_log
from dataclasses import dataclass
import os

@dataclass
class Prompt:
    id:str
    title: str
    prompt: str

    def __dict__(self):
        return {
            "id": self.id,
            "title": self.title,
            "prompt": self.prompt,
        }
    

@dataclass
class MessageGPT:
    """ 
    Message Format to send to chatGPT
    ### Parameters
    1. role : can be 'system'(to add context), 'user' (user question) or 'assistant' (chatGPT response)
    2. content : role content's
    """
    role:str
    content:str
    num:int = 1

    def __dict__(self):
        return {
            "role": self.role,
            "content": self.content
        }


def load_prompts() -> list:
    with open("prompts.json", "r", encoding="utf-8") as file:
        prompts = json.loads(file.read())
    return prompts


def save_prompts(prompts:list) -> None:
    with open("prompts.json", "w", encoding="utf-8") as file:
        file.write(json.dumps(prompts))


def get_prompt_by_id(prompt_id:str, prompts:list) -> dict:
    for prompt in prompts:
        if prompt['id'] == prompt_id:
            return prompt


def append_prompt(title:str, question:str) -> str:
    prompts = load_prompts()
    prompt_id = str(uuid.uuid1())
    prompt = Prompt(prompt_id, title, question)
    prompts.append(prompt.__dict__())
    save_prompts(prompts)
    return prompt_id


def update_prompt(prompt_id:str, title:str) -> None:
    prompts = load_prompts()
    prompt = get_prompt_by_id(prompt_id, prompts)
    prompt['title'] = title
    save_prompts(prompts)


def remove_prompt(prompt_id:str) -> None:
    prompts = load_prompts()
    prompt = get_prompt_by_id(prompt_id, prompts)
    prompts.remove(prompt)
    save_prompts(prompts)


def start_interview(position:str, xp_years:str, skills:str) -> None:
    initial_prompt = interview_prompt(position, xp_years, skills)
    messages = []
    message = MessageGPT("user", initial_prompt)
    messages.append(message.__dict__())
    response = send_to_GPT(messages)
    save_interview(messages, response)


def start_interview_2(name:str, xp_years:str, skills:str) -> None:
    msg = f"Hola {name} , soy una analista profesional de habilidades y me llamo Kari . Para evaluar tus habilidades te hare 10 preguntas tipo test y solo tendrás que clicar encima de la respuesta correcta , una vez terminado esas 10 preguntas pasaremos al nivel 2 que tendrá otras 10 preguntas. al finalizar te dare la puntuación de tus respuesta . ¡¡¡Comencemos!!!\n\n"
    x = 0
    emit('chatResponse', msg , to=request.sid)  

    initial_prompt = interview_prompt_2(name, skills, xp_years)
    messages = []
    message = MessageGPT("system", initial_prompt)
    messages.append(message.__dict__())
    response = send_to_GPT(messages)
    save_interview(messages, response)


def start_english(level:str) -> None:
    rules = "Cuando verifiques la respuesta por favor NO repitas la pregunta, NO la repitas; Y cuando digas las opciones por favor añade un salto de línea entre las mismas, especialmente cuando preguntas si quiere continuar al siguiente nivel. Cuando te den la respuesta de una pregunta automáticamente tienes que dar la siguiente pregunta"
    message0 = MessageGPT("system", rules)
    message1 = MessageGPT("user", "Hazme un test de inglés")
    prompt = """Inicio de la Sesión de Aprendizaje de Inglés con ChatGPT:

¡Saludos! Mi nombre es ChatGPT y seré tu profesor virtual de inglés. Estoy programado con el propósito principal de ayudarte a aprender y mejorar tus habilidades en inglés a través de un método interactivo basado en preguntas tipo test.

A continuación, detallo el proceso que seguiremos:

Niveles de Competencia: El aprendizaje se divide en seis niveles de competencia lingüística, que van desde el A1 (principiante) hasta el C2 (maestría). Cada nivel se ha diseñado cuidadosamente para abordar vocabulario, gramática y estructuras específicas del inglés.

Formato de las Preguntas: En cada nivel, te enfrentarás a una serie de preguntas. Cada una de estas preguntas vendrá acompañada de cuatro opciones de respuesta: a, b, c y d. Tu tarea será seleccionar la respuesta que consideres correcta.

Interacción y Retroalimentación: solo me felicitaras si la respuesta es correcta . Si respuesta no es la correcta, explicaras el por qué y mostraras la respuesta adecuada, asegurando así un aprendizaje efectivo. cada vez que una pregunta sea contestada procederás a dar la siguiente pregunta

Progresión y Evaluación: Al concluir las 10 preguntas de un nivel, recibirás una felicitación por haber terminado el nivel y una puntuación de 1 al 10 sobre las respuestas acertadas . Luego, te ofreceré la opción de avanzar al siguiente nivel con la opción a que sera un si o finalizar la sesión que sera la opción b. Si eliges avanzar, la dinámica será la misma, pero con un nivel de complejidad mayor.

Ventajas de este Método:

Retroalimentación Inmediata: Te permite corregir y aprender de tus errores en tiempo real.
Aprendizaje Modular: Puedes aprender y evaluar tu conocimiento nivel por nivel.
Flexibilidad: Puedes decidir el ritmo y cuándo avanzar.
Con toda esta información en mente, ¿estás listo para embarcarte en esta aventura lingüística? Si es así, por favor, especifica el nivel con el que deseas iniciar (A1, A2, B1, B2, C1, C2) y comenzaremos con la primera pregunta. ¡Espero que disfrutes este viaje hacia el dominio del inglés!"""
    message2 = MessageGPT("assistant", prompt)
    message3 = MessageGPT("user", level)
    messages = [message0.__dict__(), message1.__dict__(), message2.__dict__(), message3.__dict__()]
    response = send_to_GPT(messages)
    save_interview(messages, response)


def start_business(category):
    prompt = business_prompt(category)
    msg = MessageGPT("user", prompt)
    messages = [msg.__dict__()]
    response = send_to_GPT(messages)
    save_interview(messages, response)
    

def start_burnout():
    prompt = burnout_prompt()
    msg = MessageGPT("user", prompt)
    messages = [msg.__dict__()]
    response = send_to_GPT(messages)
    save_interview(messages, response)


def start_pray():
    prompt = pray_prompt()
    msg = MessageGPT("user", prompt)
    messages = [msg.__dict__()]
    response = send_to_GPT(messages)
    save_interview(messages, response)
    

def send_to_GPT(messages:list, model:str = "gpt-3.5-turbo") -> str:
    """
    Send message to chatGPT, emit stream to client with socketio, and return full text when finish
    
    ### Parameters
    1. messages: list with MessageGPT items
    2. model: "gpt-3.5-turbo" or "gpt-3.5-turbo-16k"
    """
    
    final_response = ""
    print("prompt send")
    try:
        completion = openai.ChatCompletion.create(
            model = model,
            messages = messages,
            stream = True
        )
        for obj in completion:
            chunk = obj["choices"][0]
            if chunk["finish_reason"] != "stop":
                msg = chunk["delta"]["content"]
                final_response += msg
                emit('chatResponse', msg, to=request.sid)  
    except Exception as e:
        print(e)
        emit('chatResponse', "Ha ocurrido un error, espere unos segundos e intente de nuevo", to=request.sid)
        emit('chatError', to=request.sid)
        error_log(session['user'], f"resume: {e}") 
    print("prompt received")
    emit('chatEnd', to=request.sid)
    return final_response
    

def interview_prompt(position:str, xp_years:str, skills:str) -> str:
    return f"Soy un {position} , tengo {xp_years} años de experiencia y mis habilidades principales son \
{skills} . En estos momentos estoy sin trabajo y necesito prepararme para las entrevista que tendré la \
semana que viene. Quiero que te conviertas en un entrevistador profesional y que me pongas a prueba realizándome \
tu la entrevista. Ten en cuanta los años de experiencia a la hora de la dificultad de las preguntas que me vas a \
realizar. La entrevista sera de 10 preguntas en formato test con 3 posibles respuestas, de las \
cuales solo 1 será la respuesta correcta . Las preguntas me las harás de una en una y yo te diré la respuesta poniéndote \
un comentario si es a, b o c. Si me equivoco con la respuesta me dirás cual es la correcta y porque. \
En caso contrario, si acierto la respuesta me felicitaras sin darme explicación. Una vez acierte y me felicites \
o falle y me digas cual es la correcta y porque , pasaremos a la siguiente pregunta. Así será el proceso hasta realizar \
las 10 preguntas y cuando se finalicen esas 10 preguntas me darás un feedback de como he echo la entrevista y me darás \
consejos para que tenga mas éxito en futuras entrevista de trabajo. Cuando este terminado todo lo que hemos dicho con \
anterioridad y me hayas dado el feedback, necesito que me preguntes si quiero realizar otra entrevista con una mayor \
dificultad en las preguntas y respuestas. En caso que que te diga que no, das por terminada la entrevista; Pero si te \
digo que si, volvemos a empezar con el proceso de entrevista, pero esta vez las preguntas serán mas mucho mas complejas\
ya que serán mas largas y el entrevistado se tendrá que poner en  contexto a la pregunta para dar la respuesta correcta. \
Tienes que hablar como un entrevistador profesional, me tienes que dar la primera pregunta en el siguiente mensaje \
y simula que estás empezando la conversación tú. Cuando yo te de la respuesta me das el feedback y en el mismo mensaje \
me das la siguiente pregunta"


def pray_prompt():
    prompt = """Quiero jugar 'Guía Diaria del Versículo'. Guíame a través de 3 preguntas para encontrar un versículo bíblico para hoy.

*las preguntas serán tipo test (tienes que mencionar el numero de pregunta) y el usuario tendrá que elegir a, b , c ,d o e . Hasta que no responda la primera pregunta , no se le hará la segunda pregunta. Basado en las respuestas, ChatGPT proporcionará un versículo bíblico relevante. Inicial el juego ahora !!"""
    return prompt

def burnout_prompt():
    prompt = "Teniendo en cuenta estos dos cuestionarios validados, como el Maslach Burnout Inventory (MBI) o el Copenhagen Burnout Inventory (CBI), que han sido desarrollados específicamente para evaluar el burnout. quiero que me haga un juego tipo test para evaluar el burnout y que funcione de la siguiente manera : la evaluación sera de 10 preguntas en formato test con 4 posibles respuestas, de las cuales solo 1 será la respuesta correcta . las preguntas me las harás de una en una y te daré la respuesta dando click en a, b , c o d . hasta que no conteste la pregunta no me harás la siguiente pregunta . así será el proceso hasta realizar 10 preguntas y cuando se finalicen continuaremos con la primera pregunta del nivel 2 que tendrá otras 10 preguntas. cuando se hayan respondido las preguntas del nivel 2 volverás a felicitar por haber terminado la evaluación. Tendrás que dar una valoración profesional del nivel de burnout, teniendo en cuenta la puntuación total que sera la suma de todas las respuestas y me darás el resultado total cuando se termine el nivel 2. Empieza de una vez con la primera pregunta"
    return prompt


def business_prompt(category):
    prompt = f"""Me vas a hacer un test sobre {category}. La evaluación será de 10 preguntas en formato test con 4 posibles respuestas, de las cuales solo 1 será la respuesta correcta. Las preguntas me las harás de una en una y te daré la respuesta haciendo clic en las opciones a, b o c. Hasta que no conteste la pregunta no me harás la siguiente pregunta, si me equivoco con la respuesta me dirás cuál es la correcta y por qué. En caso contrario, si acierto la respuesta, me felicitarás. Una vez acierte y me felicites o falle y me digas cuál es la correcta y porque, pasaremos a la siguiente pregunta. Así será el proceso hasta realizar 10 preguntas y cuando se finalicen esas 10 preguntas felicitarás por haber terminado el nivel 1 y continuaremos con la primera pregunta del nivel 2 que tendrá otras 10 preguntas. Cuando se hayan respondido las preguntas del nivel 2 volverás a felicitar por haber terminado la evaluación y tendrás que dar una puntuación profesional con base en las preguntas acertadas o no acertadas, Empieza de una vez diciendo la primera pregunta"""
    return prompt


def interview_prompt_2(name:str, skills:str, xp_years:str):
    prompt =  f"""Tu nombre es Kari, eres un trabajador de recursos humanos. Tu trabajo es entrevistar a las personas evaluando sus habilidades en formato test de 10 preguntas con 3 posibles respuestas (solo 1 es correcta), le dirás al entrevistado que cliquee en la respuesta que crea correcta (a, b, o c). Vas a comenzar haciéndole la pregunta 1, recibirás la respuesta del entrevistado y a eso le dirás si su respuesta es correcta o no e inmediatamente le dirás la siguiente pregunta. Al finalizar las 10 preguntas preguntarás si quiere hacer el test nivel 2. Hoy examinaras a {name} tienes que hacerle un test en base a sus habilidades que son {skills} {xp_years}. Di la primera pregunta de una vez sin presentarte ni nada"""
    return prompt


def load_prompts(filepath) -> list:
    with open(filepath, encoding="utf-8") as file:
        data = file.read()
        messages:list = json.loads(data)
        return messages


def answer_interview(answer:str) -> str:
    filepath = f"./prompts/{request.sid}.json"
    if not os.path.isfile(filepath):
        with open(filepath, "w") as file:
            file.write(json.dumps([]))
    messages = load_prompts(filepath)
    message = MessageGPT("user", answer)
    messages.append(message.__dict__())
    response = send_to_GPT(messages)
    save_interview(messages, response)


def resend_msg():
    filepath = f"./prompts/{request.sid}.json"
    messages = load_prompts(filepath)
    response = send_to_GPT(messages)
    save_interview(messages, response)


def save_interview(messages:list, response:str) -> str:
    messages.append({"role": "assistant", "content": response})
    with open(f"./prompts/{request.sid}.json", "w", encoding="utf-8") as file:
        file.write(json.dumps(messages))
