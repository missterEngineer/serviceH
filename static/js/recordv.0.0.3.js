let stream_data = {}
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
    stream_data[socket_endpoint] = []
    const stream_d = stream_data[socket_endpoint]
    let tmp_data = []
    mediaRecorder.ondataavailable = async function (e) {
        if (e.data.size > 0) {
            if(tmp_data.length == -100){
                let new_data = tmp_data.slice()
                tmp_data = []
                let blob
                if(socket_endpoint === "record"){
                    let tmp_blob = new Blob(new_data, {type: 'video/webm'})
                    let file = new File([tmp_blob], "recorder.webm")
                    blob = await convert2audio(file)
                }else{
                    blob = new Blob(new_data, {type: 'audio/mp3'});
                }
                socket.emit(socket_endpoint, blob)
            }
            socket.emit(socket_endpoint, e.data)
            stream_d.push(e.data)
        }
    };
    mediaRecorder.addEventListener("stop",($e)=> {
        stopStream(stream);
        if(!mediaRecorder.fromBtn){
            stopBtn.click();
        }
    } );
    mediaRecorder.start(100); // For every 100 mili-second the stream data will be stored in a separate chunk.
    mediaRecorder.stopped = false
    return mediaRecorder;
}


async function saveFiles(name){
    let file = new File(stream_data["record"], "recorder.webm")
    stream_data["record"] = await convert2audio(file)
    delete file
    stream_data["audio_file"] = new File([stream_data["record"]], name + ".computer.mp3")      
    delete stream_data["record"];
    stream_data["mic_file"] = new File( stream_data["recordMic"],  name + ".mic.webm")
    delete stream_data["recordMic"];
}


function retryMedia(){
    document.getElementById("wait_text").innerText = "Subiendo archivo..."
    let form =  new FormData()
    form.append("audio_file", stream_data["audio_file"])
    form.append("mic_file", stream_data["mic_file"])
    form.append("sid", socket.id)
    const ajax = new XMLHttpRequest();
    ajax.upload.addEventListener("progress", (progressHandler), false);
    ajax.addEventListener("loadend", completeHandler, false);
    ajax.addEventListener("error", errorHandler, false);
    ajax.addEventListener("abort", errorHandler, false);
    ajax.open("POST", "/recover_audio"); 
    ajax.send(form);
}

async function downloadMedia(filename){
    downloadBlob(filename + ".computer.mp3",stream_data["audio_file"])
    downloadBlob(filename + ".microphone.webm", stream_data["mic_file"])
}

function downloadBlob(filename, blob){
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    // the filename you want
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
}

function progressHandler(event) {
    const percent = (event.loaded / event.total) * 100;
    const span = document.getElementById("upload_time");
    span.innerText = Math.round(percent) + "%"
}
  
function completeHandler(event) {
try{
    console.log(event)
    const response = JSON.parse(event.target.response) 
    if ('success' in response){
        const text_element = document.getElementById("wait_text")
        text_element.innerText = "Archivo subido correctamente, procesando audio..."
        text_element.style.color = "rgb(144 99 9)"
    }
}catch(error){
    console.error(error)
    errorHandler(event)
}

}

function errorHandler(event) {
    const text_element = document.getElementById("wait_text")
    text_element.style.color = "#9b0909"
    text_element.innerHTML = "Error al subir archivo";
}
  



function stopStream(stream) {
    stream.getTracks().forEach((track) => {
        track.stop();
    });
}

async function send_data(endpoint){
    const data = stream_data[endpoint].slice();
    let file = new File(data, "recorder.webm")
    let audio = await convert2audio(file)
}

async function convert2audio(video_file) {
    return new Promise((resolve,reject) =>{
        let audioContext = new(window.AudioContext || window.webkitAudioContext)();
        let reader = new FileReader();
        let myBuffer;
        let new_file;
        const sampleRate = 16000;
        const numberOfChannels = 1;
        reader.onload = async function () {
            let videoFileAsBuffer = reader.result; // arraybuffer
            let decodedAudioData = await audioContext.decodeAudioData(videoFileAsBuffer)
            let duration = decodedAudioData.duration;
    
            let offlineAudioContext = new OfflineAudioContext(numberOfChannels, sampleRate *
                duration, sampleRate);
            let soundSource = offlineAudioContext.createBufferSource();
    
            myBuffer = decodedAudioData;
            soundSource.buffer = myBuffer;
            soundSource.connect(offlineAudioContext.destination);
            soundSource.start();
    
            compressor = offlineAudioContext.createDynamicsCompressor();
    
            compressor.threshold.setValueAtTime(-20, offlineAudioContext.currentTime);
            compressor.knee.setValueAtTime(30, offlineAudioContext.currentTime);
            compressor.ratio.setValueAtTime(5, offlineAudioContext.currentTime);
            compressor.attack.setValueAtTime(.05, offlineAudioContext.currentTime);
            compressor.release.setValueAtTime(.25, offlineAudioContext.currentTime);
            // Connect nodes to destination
            soundSource.connect(compressor);
            compressor.connect(offlineAudioContext.destination);
            let renderedBuffer = await offlineAudioContext.startRendering()
            new_file = bufferToWave(renderedBuffer,offlineAudioContext.length)
            resolve(new_file)
             //make_download(renderedBuffer, offlineAudioContext.length);
        };
        reader.readAsArrayBuffer(video_file); // video file
    })
}

function bufferToWave(abuffer, len) {
    let numOfChan = abuffer.numberOfChannels,
        length = len * numOfChan * 2 + 44,
        buffer = new ArrayBuffer(length),
        view = new DataView(buffer),
        channels = [],
        i, sample,
        offset = 0,
        pos = 0;

    // write WAVE header
    setUint32(0x46464952); // "RIFF"
    setUint32(length - 8); // file length - 8
    setUint32(0x45564157); // "WAVE"

    setUint32(0x20746d66); // "fmt " chunk
    setUint32(16); // length = 16
    setUint16(1); // PCM (uncompressed)
    setUint16(numOfChan);
    setUint32(abuffer.sampleRate);
    setUint32(abuffer.sampleRate * 2 * numOfChan); // avg. bytes/sec
    setUint16(numOfChan * 2); // block-align
    setUint16(16); // 16-bit (hardcoded in this demo)

    setUint32(0x61746164); // "data" - chunk
    setUint32(length - pos - 4); // chunk length

    // write interleaved data
    for (i = 0; i < abuffer.numberOfChannels; i++)
        channels.push(abuffer.getChannelData(i));

    while (pos < length) {
        for (i = 0; i < numOfChan; i++) { // interleave channels
            sample = Math.max(-1, Math.min(1, channels[i][offset])); // clamp
            sample = (0.5 + sample < 0 ? sample * 32768 : sample * 32767) | 0; // scale to 16-bit signed int
            view.setInt16(pos, sample, true); // write 16-bit sample
            pos += 2;
        }
        offset++ // next source sample
    }
    let wavHdr = lamejs.WavHeader.readHeader(new DataView(buffer));
    let wavSamples = new Int16Array(buffer, wavHdr.dataOffset, wavHdr.dataLen / 2);
    return wavToMp3(wavHdr.channels, wavHdr.sampleRate, wavSamples);
    // create Blob

    function setUint16(data) {
        view.setUint16(pos, data, true);
        pos += 2;
    }

    function setUint32(data) {
        view.setUint32(pos, data, true);
        pos += 4;
    }
}

function wavToMp3(channels, sampleRate, samples) {
    var buffer = [];
    var mp3enc = new lamejs.Mp3Encoder(channels, sampleRate, 128);
    var remaining = samples.length;
    var samplesPerFrame = 1152;
    for (var i = 0; remaining >= samplesPerFrame; i += samplesPerFrame) {
        var mono = samples.subarray(i, i + samplesPerFrame);
        var mp3buf = mp3enc.encodeBuffer(mono);
        if (mp3buf.length > 0) {
            buffer.push(new Int8Array(mp3buf));
        }
        remaining -= samplesPerFrame;
    }
    var d = mp3enc.flush();
    if(d.length > 0){
        buffer.push(new Int8Array(d));
    }

    var mp3Blob = new Blob(buffer, {type: 'audio/mp3'});
    return mp3Blob

}