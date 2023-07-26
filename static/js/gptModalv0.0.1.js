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
    gptResponse.innerHTML = '<p>Generando...</p>';
    socket.emit('startChat', {
        conversation: transcriptTxt.value,
        question: questionTxt.value
    });
})
socket.on('chatResponse', msg => {
    gptResponse.innerHTML += msg
})