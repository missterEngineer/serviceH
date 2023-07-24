async function recordScreen() {
    return await navigator.mediaDevices.getDisplayMedia({
        audio: true,
        video: {
            mediaSource: "screen"
        }
    });
}

async function recordMic() {
    return await navigator.mediaDevices.getUserMedia({
        audio: true, // constraints - only audio needed for this app
    })
}

function createRecorder(stream, socket_endpoint) {
    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = function (e) {
        if (e.data.size > 0) {
            socket.emit(socket_endpoint, e.data);
        }
    };
    mediaRecorder.addEventListener("stop",()=> stopBtn.click() );
    mediaRecorder.start(1000); // For every second the stream data will be stored in a separate chunk.
    return mediaRecorder;
}