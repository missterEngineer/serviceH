const startBtn = document.getElementById("startBtn"),
    startSpeakerBtn = document.getElementById("startSpeakerBtn"),
    transcript_content = document.getElementById("transcript-content"),
    audio = document.getElementById("audio-link").innerText,
    questionTxt = document.getElementById("questionTxt"),
    sendGPT = document.getElementById("sendGPT");


let gptResponse,
    with_speakers = false;

/** @param {string} id */
function close_modal(id){
    document.querySelector(`dialog#${id}`).close();
}

/** @param {string} id */
function open_modal(id){
    document.querySelector(`dialog#${id}`).showModal();
}

/** @param {HTMLButtonElement} button */
function show_prompt(button){
    let prompt = button.parentElement.nextElementSibling.innerText;
    prompt = prompt.replace("Prompt: ", "");
    questionTxt.value = prompt;
    close_modal("modal-prompts")
}

//{% if session.user == 'prueba' %} 
/** @param {HTMLElement} editBtn */
function edit_prompt(editBtn){
    let element = editBtn.previousElementSibling;
    let title = element.firstElementChild
    let input = document.createElement("input");
    input.value = title.textContent
    title.hidden = true;
    element.insertBefore(input, element.firstChild);
    element.onclick = ()=> void(0);
    editBtn.firstElementChild.src = "/static/images/saving.svg" //img tag
    editBtn.onclick = () => save_edit_prompt(editBtn);
}


/** @param {HTMLElement} saveBtn */
function save_edit_prompt(saveBtn){
    let element = saveBtn.previousElementSibling;
    const body = new FormData();
    const prompt_id = saveBtn.parentElement.dataset.id;
    const new_name = element.firstElementChild.value;
    body.append("id", prompt_id)
    body.append("name", new_name)
    fetch("/edit_prompt",{
        method:"POST",
        body:body
    }).then(response=>{
        if (!response.ok) alert("Error al editar")
    })
    ;
    element.firstElementChild.remove();
    let title = element.firstElementChild;
    title.hidden = false;
    title.textContent = new_name;
    saveBtn.firstElementChild.src = "/static/images/edit.svg" //img tag
    saveBtn.onclick = () => edit_prompt(saveBtn);
}


/** @param {HTMLElement} delBtn */
function del_prompt(delBtn){
    const body = new FormData();
    const prompt_id = delBtn.parentElement.parentElement.parentElement.dataset.id;
    body.append("id", prompt_id)
    fetch("/del_prompt",{
        method: "POST",
        body:body
    });
    delBtn.parentElement.parentElement.parentElement.remove();
}
//{% endif %}


function start_chat() {
    socket.emit('startChat', {
        conversation: transcript_content.innerText,
        question: questionTxt.value,
        audio_name: audio
    });
    writeSpeaker("Tú", questionTxt.value, "gpt-content");
    gptResponse = writeSpeaker("ChatGPT", "", "gpt-content");
    document.querySelector(".gpt-send").classList.add("hide");
    document.querySelector(".gpt-spinner").classList.remove("hide");
    sendGPT.onclick = () => {
        return void(0)
    };
}


socket.on('chatResponse', msg => {
    gptResponse.innerText += msg;
})


socket.on('chatEnd', () => {
    document.querySelector(".gpt-spinner").classList.add("hide");
    document.querySelector(".gpt-send").classList.remove("hide");
    sendGPT.onclick = start_chat;
})


function start_transcript(speaker = false) {
    socket.connect();
    with_speakers = speaker;
    transcript_content.innerText = "";
    let model;
    if (speaker === true) {
        model = "speaker"
        startSpeakerBtn.innerText = "Cargando..."
    } else {
        model = "normal"
        startBtn.innerText = "Cargando..."
    }
    document.getElementById("modal-loader").showModal();
    socket.emit('startTranscript', {
        model: model,
        audio: audio
    });
    startBtn.disabled = true;
    startSpeakerBtn.disabled = true;
}


startBtn.addEventListener("click", () => start_transcript(false))
startSpeakerBtn.addEventListener("click", () => start_transcript(true))


socket.on('response', msg => {
    if (with_speakers) {
        processTxtSpeaker(msg)
    } else {
        transcript_content.innerText += msg + "\n"
    }
    unlockGPT();
});


function processTxtSpeaker(msg) {
    let messages = msg.split("\n\n")
    for (message of messages) {
        extractTxtSpeaker(message)
    }
}


function extractTxtSpeaker(txt = "") {
    let txt_splitted = txt.split("[");
    console.log(txt_splitted)
    if (txt_splitted.length === 1) return;
    txt = txt_splitted[1];
    txt_splitted = txt.split("]");
    let speaker = txt_splitted[0];
    let message = txt_splitted[1];
    writeSpeaker(speaker, message, "transcript-content");
}

/**
@param {string} speaker speaker's name
@param {string} msg speaker's message
@param {string} node_id HTML Element ID
*/
function writeSpeaker(speaker, msg, node_id) {
    let img = document.createElement("img");
    img.innerText = speaker;
    if (speaker === "Tú"){
        img.src = "/static/images/book_green.svg";
    }else{
        img.src = "/static/images/robot.svg";
    }
    let p = document.createElement("p");
    p.innerText = msg;
    let div = document.createElement("div");
    div.appendChild(img);
    div.appendChild(p);
    div.classList.add("txt-speaker");
    document.getElementById(node_id).appendChild(div);
    // {% if session.user == 'prueba' %}
    if (speaker !== "Tú") return p;
    let svg = `
        <svg width="20px" height="20px" viewBox="0 0 32 32" version="1.1" xmlns="http://www.w3.org/2000/svg" class="save-prompt" onclick="save_dialog_prompt(this)">
            <g id="Page-1" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd" sketch:type="MSPage">
                <g id="Icon-Set" sketch:type="MSLayerGroup" transform="translate(-152.000000, -515.000000)" fill="currentColor">
                    <path d="M171,525 C171.552,525 172,524.553 172,524 L172,520 C172,519.447 171.552,519 171,519 C170.448,519 170,519.447 170,520 L170,524 C170,524.553 170.448,525 171,525 L171,525 Z M182,543 C182,544.104 181.104,545 180,545 L156,545 C154.896,545 154,544.104 154,543 L154,519 C154,517.896 154.896,517 156,517 L158,517 L158,527 C158,528.104 158.896,529 160,529 L176,529 C177.104,529 178,528.104 178,527 L178,517 L180,517 C181.104,517 182,517.896 182,519 L182,543 L182,543 Z M160,517 L176,517 L176,526 C176,526.553 175.552,527 175,527 L161,527 C160.448,527 160,526.553 160,526 L160,517 L160,517 Z M180,515 L156,515 C153.791,515 152,516.791 152,519 L152,543 C152,545.209 153.791,547 156,547 L180,547 C182.209,547 184,545.209 184,543 L184,519 C184,516.791 182.209,515 180,515 L180,515 Z" id="save-floppy" sketch:type="MSShapeGroup">
                    </path>
                </g>
            </g>
        </svg>
    `
    p.insertAdjacentHTML("beforeend", svg)
    // {% endif %}
    return p
}


/** @param {HTMLElement} svg */
function save_dialog_prompt(svg) {
    document.querySelector("dialog textarea").value = svg.parentNode.innerText;
    open_modal("modal-save");
}


function save_prompt(){
    const data = new FormData(document.querySelector("dialog form"));
    fetch("/save_prompt", {
        method:"POST",
        body:data
    }).then(response=>{
        if(response.ok){
            close_modal("modal-save")
        }else{
            alert("Ha ocurrido un error, intente de nuevo")
        }
    })
}


async function loadData() {
    const response = await fetch(`/get_prompts?filename=${audio}`)
    if (!response.ok) return
    const audio_txt = await response.json()
    const audio_data = JSON.parse(audio_txt)
    if (has_speakers(audio_data.conversation)) {
        processTxtSpeaker(audio_data.conversation)
    } else {
        transcript_content.innerText = audio_data.conversation
    }
    let msg_speaker = "Tú"
    if ('messages' in audio_data){
        for (let msg of audio_data.messages) {
            writeSpeaker(msg_speaker, msg, "gpt-content")
            msg_speaker = msg_speaker == "Tú" ? "ChatGPT" : "Tú"
        }
    }
    unlockGPT();
}

function unlockGPT(){
    sendGPT.onclick = start_chat;
    document.querySelector("#questionTxt").disabled = false;
    document.querySelector(".blocked").classList.remove("blocked");
    document.querySelector(".saved-prompts").onclick = () => open_modal('modal-prompts');
    document.querySelector(".gpt-divider").hidden = false;
    document.getElementById("startSpeakerBtn").hidden = false;
    document.getElementById("startBtn").hidden = false;
    document.getElementById("empty").style.display = "none";
    document.getElementById("transcript-title").hidden = false;
}


function has_speakers(text = '') {
    if (text.includes("SPEAKER_00") || text.includes("Speaker_0")) return true
    return false
}

socket.on('end', () => {
    document.getElementById("modal-loader").close();
    startBtn.disabled = false
    startBtn.innerText = "Transcribir"
    startSpeakerBtn.disabled = false
    startSpeakerBtn.innerText = "Transcribir(P)"
})

function del_file() {
    fetch(`/del_file?filename=${audio}`).then(() => {
        location.href = "/"
    }).catch(() => {
        alert("No existe el archivo")
    })
}
loadData()

/** @param {HTMLElement} parent */
function set_spinner(parent) {
    const span = document.createElement("span"),
        img = document.createElement("img");
    span.classList.add("spinner");
    img.src = "/static/images/spinner.svg"
    img.alt = "Cargando..."
    span.appendChild(img)
    parent.appendChild(span)
}
