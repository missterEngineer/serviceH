import uuid
import openai
import json
from flask import request, session
from flask_socketio import emit
from utils import error_log
from dataclasses import dataclass


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


def answer_interview(answer:str) -> str:
    with open(f"./prompts/{request.sid}.json", encoding="utf-8") as file:
        data = file.read()
        messages:list = json.loads(data)
    message = MessageGPT("user", answer)
    messages.append(message.__dict__())
    model = "gpt-3.5-turbo"
    response = send_to_GPT(messages, model)
    save_interview(messages, response)


def save_interview(messages:list, response:str) -> str:
    messages.append({"role": "assistant", "content": response})
    with open(f"./prompts/{request.sid}.json", "w", encoding="utf-8") as file:
        file.write(json.dumps(messages))
