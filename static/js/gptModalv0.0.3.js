// Modal config
const gptModal = document.getElementById("gptModal"),
askBtn = document.getElementById("askBtn"),
closeModalBtn = document.getElementById("closeModalBtn"),
questionTxt = document.getElementById("questionTxt"),
gptResponse = document.getElementById("gptResponse");

askBtn.addEventListener('click',()=> gptModal.showModal())
closeModalBtn.addEventListener('click',()=> gptModal.close())

// Using ChatGPT
askBtn.addEventListener('click', ()=>{
    socket.connect();
    gptResponse.innerHTML = '<p id="generando">Generando...</p>';
    if (!audio){
        audio = ""
    }
    socket.emit('startChat', {
        conversation: transcriptTxt.value,
        question: questionTxt.value,
        audio_name: audio
    });
    if(loadMsg !== undefined){
        loadMsg(1, questionTxt.value)
    }
})
socket.on('chatResponse', msg => {
    gptResponse.innerHTML += msg
})
socket.on('chatEnd', () => {
    document.getElementById("generando").remove()
    if(loadMsg !== undefined){
        loadMsg(2,  gptResponse.innerHTML)
    }
})