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
    mediaRecorder.addEventListener("stop",($e, fromBtn=false)=> {
        stopStream(stream);
        if(!mediaRecorder.fromBtn){
            stopBtn.click();
        }
    } );
    mediaRecorder.start(100); // For every second the stream data will be stored in a separate chunk.
    mediaRecorder.stopped = false
    return mediaRecorder;
}

function stopStream(stream) {
    stream.getTracks().forEach((track) => {
        track.stop();
    });
}