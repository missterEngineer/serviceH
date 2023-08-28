
function convert2audio(video_file) {
    let audioContext = new(window.AudioContext || window.webkitAudioContext)();
    let reader = new FileReader();
    let myBuffer;

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
        let new_file = bufferToWave(renderedBuffer,offlineAudioContext.length)
        return new_file
         //make_download(renderedBuffer, offlineAudioContext.length);
    };

    return reader.readAsArrayBuffer(video_file); // video file
}

function make_download(buffer, total_samples) {

    // get duration and sample rate
    let duration = buffer.duration,
        rate = buffer.sampleRate,
        offset = 0;

    let new_file = URL.createObjectURL(bufferToWave(buffer, total_samples));

    let download_link = document.getElementById("download_link");
    download_link.href = new_file;
    let name = generateFileName();
    download_link.download = name;
}

function generateFileName() {
    let origin_name = document.querySelector("input").files[0].name;
    let pos = origin_name.lastIndexOf('.');
    let no_ext = origin_name.slice(0, pos);

    return no_ext + ".compressed.wav";
}
// Convert an AudioBuffer to a Blob using WAVE representation
function bufferToWave(abuffer, len) {
    let numOfChan = abuffer.numberOfChannels,
        length = len * numOfChan * 2 + 44,
        buffer = new ArrayBuffer(length),
        view = new DataView(buffer),
        channels = [],
        i, sample,
        offset = 0,
        pos = 0;
    console.log("channels", numOfChan)
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
    console.log("??")
    // create Blob
    return new Blob([buffer], {
        type: "audio/wav"
    });

    function setUint16(data) {
        view.setUint16(pos, data, true);
        pos += 2;
    }

    function setUint32(data) {
        view.setUint32(pos, data, true);
        pos += 4;
    }
}

