// 状態管理
const state = {
    isRecording: false,
    mediaRecorder: null,
    websocket: null,
    chunks: [],
    audioContext: null,
    analyser: null,
    stream: null
};

// 言語設定の取得
function getLanguageSettings() {
    const currentLang = window.TRAVEL_GUIDE.currentLang;
    let sourceLang, targetLang;

    switch (currentLang) {
        case 'en':
            // 英語モード: 英語⇔日本語
            sourceLang = 'en';
            targetLang = 'ja';
            break;
        case 'zh':
            // 中国語モード: 中国語⇔日本語
            sourceLang = 'zh';
            targetLang = 'ja';
            break;
        case 'ja':
            // 日本語モード: 相手の言語に応じて変換
            const urlParams = new URLSearchParams(window.location.search);
            const partnerLang = urlParams.get('partner_lang') || 'en';
            sourceLang = 'ja';
            targetLang = partnerLang;
            break;
        default:
            sourceLang = 'en';
            targetLang = 'ja';
    }

    return { sourceLang, targetLang };
}

// AudioContextの初期化
async function initAudioContext() {
    if (!state.audioContext) {
        state.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        await state.audioContext.resume();
    }
    return state.audioContext;
}

// 音声の再生
async function playAudio(audioUrl) {
    try {
        if (!state.audioContext) {
            await initAudioContext();
        }

        // 音声データの取得
        const response = await fetch(audioUrl);
        const arrayBuffer = await response.arrayBuffer();
        
        // デコード
        const audioBuffer = await state.audioContext.decodeAudioData(arrayBuffer);
        
        // ソース作成
        const source = state.audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(state.audioContext.destination);
        
        source.start(0);
        console.log('Started playing audio');

    } catch (error) {
        console.error('Audio playback error:', error);
    }
}

// WebSocket接続
function connectWebSocket() {
    if (state.websocket?.readyState === WebSocket.OPEN) return;
    
    const wsUrl = `ws://${window.location.host}/ws/interpreter`;
    state.websocket = new WebSocket(wsUrl);
    
    state.websocket.onopen = () => {
        console.log('WebSocket connected');
        // 言語モードを送信
        const currentLang = window.TRAVEL_GUIDE.currentLang;
        console.log('Setting language mode:', currentLang);
        state.websocket.send(JSON.stringify({
            type: 'mode',
            mode: currentLang
        }));
    };
    
    state.websocket.onmessage = async (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('Received message:', data);
            
            if (data.type === 'translation' && data.audioUrl) {
                await playAudio(data.audioUrl);
            }
        } catch (error) {
            console.error('Translation error:', error);
        }
    };

    state.websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    state.websocket.onclose = () => {
        console.log('WebSocket connection closed');
        state.websocket = null;
    };
}

// 録音データの処理と送信
function processAndSendRecording() {
    console.log('Processing recording, chunks:', state.chunks.length);
    
    if (state.chunks.length === 0) {
        console.log('No audio data to process');
        return;
    }
    
    const audioBlob = new Blob(state.chunks, { type: 'audio/wav' });
    const reader = new FileReader();
    
    reader.onload = () => {
        if (state.websocket?.readyState === WebSocket.OPEN) {
            const currentLang = window.TRAVEL_GUIDE.currentLang;
            const { sourceLang, targetLang } = getLanguageSettings();
            console.log(`Sending audio data (${sourceLang} -> ${targetLang}) in ${currentLang} mode`);
            
            state.websocket.send(JSON.stringify({
                type: 'audio',
                data: reader.result.split(',')[1],
                lang: targetLang,
                source_lang: sourceLang,
                mode: currentLang
            }));
        } else {
            console.log('WebSocket not ready');
        }
    };
    
    reader.readAsDataURL(audioBlob);
}

// 録音開始
async function startRecording() {
    try {
        // マイク使用の許可を要求
        state.stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                sampleRate: 16000
            }
        });
        
        // AudioContextの設定
        state.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const source = state.audioContext.createMediaStreamSource(state.stream);
        state.analyser = state.audioContext.createAnalyser();
        state.analyser.fftSize = 2048;
        source.connect(state.analyser);
        
        // WebSocket接続
        connectWebSocket();
        
        // MediaRecorderの設定
        state.mediaRecorder = new MediaRecorder(state.stream);
        state.chunks = [];
        
        state.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                state.chunks.push(event.data);
                console.log('Audio chunk received:', event.data.size, 'bytes');
            }
        };
        
        state.mediaRecorder.onstop = () => {
            console.log('MediaRecorder stopped');
            processAndSendRecording();
        };
        
        // 録音開始
        state.isRecording = true;
        state.mediaRecorder.start(100);  // 100msごとにデータを取得
        updateUI();
        
    } catch (error) {
        console.error('Recording error:', error);
        if (error.name === 'NotAllowedError') {
            alert('マイクへのアクセスが拒否されました。ブラウザの設定を確認してください。');
        } else {
            alert('録音の開始に失敗しました: ' + error.message);
        }
        await stopRecording();
    }
}

// 録音停止
async function stopRecording() {
    state.isRecording = false;
    
    if (state.mediaRecorder?.state === 'recording') {
        state.mediaRecorder.stop();
    }
    
    if (state.stream) {
        state.stream.getTracks().forEach(track => track.stop());
        state.stream = null;
    }
    
    state.mediaRecorder = null;
    updateUI();
}

// UI更新
function updateUI() {
    const button = document.getElementById('interpreterBtn');
    const status = document.getElementById('interpreterStatus');
    const indicator = document.querySelector('.recording-indicator');
    
    if (button && status) {
        // 日本語モードの場合はボタンを完全に非表示
        if (window.TRAVEL_GUIDE.currentLang === 'ja') {
            button.style.display = 'none';
            if (indicator) indicator.style.display = 'none';
            return;
        }

        // 日本語以外のモードではボタンを表示
        button.style.display = 'block';
        button.classList.remove('disabled');
        button.disabled = false;

        if (state.isRecording) {
            button.classList.remove('btn-outline-success');
            button.classList.add('btn-danger');
            status.textContent = '録音停止';
            if (indicator) indicator.style.display = 'block';
        } else {
            button.classList.remove('btn-danger');
            button.classList.add('btn-outline-success');
            status.textContent = '録音開始';
            if (indicator) indicator.style.display = 'none';
        }
    }
}

// イベントリスナーの設定
document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('interpreterBtn');
    if (button) {
        button.addEventListener('click', async () => {
            // クリック時にAudioContextを初期化
            await initAudioContext();
            
            if (!state.isRecording) {
                startRecording();
            } else {
                stopRecording();
            }
        });
    }
    updateUI();
});