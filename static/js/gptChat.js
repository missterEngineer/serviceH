/** @type {HTMLDivElement} */
const historyContent = document.getElementById("historyContent");
/** @type {HTMLElement} */
let current_msg; 
/** @type {number}*/
let timer;


/** Create div and span for message and put inside historyContent div
 * @param {string} msg_num sender number (1 is user, 2 is GPT)
 * @param {string} msg message to put inside span
 * @returns {HTMLSpanElement}
 */
function createMsg(msg_num, msg=""){
    const div = document.createElement("div");
    div.classList.add(`msg${msg_num}`);
    const span = document.createElement("span");
    span.classList.add("msg");
    span.innerText = msg;
    div.appendChild(span);
    historyContent.appendChild(div);
    return span
}


function scroll2Bottom(){
    document.body.scrollTo(0, document.body.scrollHeight);
}


function add_loader(){
    const p = document.createElement("p");
    p.id = "generando";
    p.textContent = "Generando...";
    historyContent.appendChild(p);
}


function answerGPT(){
    const textarea = document.querySelector("textarea");
    let msg = textarea.value;
    createMsg("1", msg);
    current_msg = createMsg(2);
    add_loader();
    scroll2Bottom();
    socket.emit("answer_interview", msg);
    setTimeout(()=> textarea.value = "", 100);
}


function convert2hyperlink(){
    let textList = current_msg.innerText.split("\n");
    let loop_times = 0;
    let pass_number = false;
    for(let f=0; f < textList.length; f++){
        if(has_number(textList[f])  && !pass_number){
            pass_number =  true;
            continue
        }
        if(!pass_number) {
            continue
        }
        if(is_item_list(textList[f], loop_times)){
            if(loop_times < 4){
                loop_times++;
            }else{
                break
            }
            textList[f] = "<a href='#' onclick='choose(this)'>" + textList[f] + "</a><br>";
        }
    }
    current_msg.innerHTML = textList.join('<br>');
}


/** @param {HTMLAnchorElement} anchor */
function choose(anchor){
    document.getElementById("questionGPT").value = anchor.innerText;
    current_msg.querySelectorAll("a").forEach(inner_anchor=>{
        inner_anchor.removeAttribute("href");
        inner_anchor.onclick = void(0);
    })
    answerGPT();
}


/** @param {string} str */
function has_number(str){
    return /\d/.test(str)
}


/** 
 * @param {string} text
 * @param {number} loop_time
 */
function is_item_list(text, loop_time){
    if(text.toLowerCase().includes("a, b, c")) return false;
    if(text.toLowerCase().includes("a)") && loop_time === 0)  return true;
    if(text.toLowerCase().includes("b)") && loop_time === 1) return true;
    if(text.toLowerCase().includes("c)") && loop_time === 2) return true;
    if(text.toLowerCase().includes("d)") && loop_time === 3) return true;
    return false;
}


function check_hyperlink_final(){
    if(current_msg.querySelectorAll("a").length < 2){
        end_questions();
    }
}


function end_questions(){
    current_msg.innerText += "\n\n a) ¡Si! Quiero avanzar al siguiente nivel \n\n b)¡No! Quiero finalizar el test"
    convert2hyperlink();
}


function tryAgain(){
    current_msg.innerText = "";
    socket.emit("chatTryAgain");
}


function startTimer(){
    timer = 25;
    updateTimer();
    let interval = setInterval(()=>{
        if(timer > 0){
            timer--;
            updateTimer();
        }else{
            stopTimer(interval)
        }
    }, 1000)
}


function updateTimer(){
    document.getElementById("timer").innerText = timer;
}


function stopTimer(interval){
    clearInterval(interval);
    let timeout_text = "Se me ha acabado el tiempo, vamos con la siguiente pregunta"
    document.getElementById("questionGPT").value = timeout_text;
    answerGPT();
}

socket.on('chatResponse', msg => {
    current_msg.innerText += msg;
    scroll2Bottom();
})


socket.on('chatError',()=>{
    let txt_to_transform = "intente de nuevo";
    let anchor = "<a href='javascript:void(0)' onclick='tryAgain()'>intente de nuevo</a>";
    let newHtml = current_msg.innerHTML.replace(txt_to_transform, anchor);
    current_msg.innerHTML = newHtml;
})

