// Mobile Temperature Monitor Logic

// State
let state = {
    running: false,
    videoStream: null,
    worker: null,
    lastTemp: null,
    alertTriggered: false,
    roi: { x: 25, y: 35, w: 50, h: 30 }, // percentages
    config: {
        threshold: 50.0,
        direction: 'above',
        cooldown: 5000 // ms
    },
    alertResetTimer: null,
    isOcrBusy: false
};

// DOM Elements
const video = document.getElementById('videoFeed');
const canvas = document.getElementById('overlayCanvas');
const ctx = canvas.getContext('2d');
const roiBox = document.getElementById('roiBox');
const statusBadge = document.getElementById('statusBadge');
const currentTempEl = document.getElementById('currentTemp');
const rawOcrEl = document.getElementById('rawOcr');
const logList = document.getElementById('logList');
const btnToggle = document.getElementById('btnToggle');
const cameraSelect = document.getElementById('cameraSelect');

// Audio Context for alerts
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

async function playAlertSound() {
    if (audioCtx.state === 'suspended') await audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.type = 'square';
    osc.frequency.setValueAtTime(880, audioCtx.currentTime);
    osc.frequency.setValueAtTime(440, audioCtx.currentTime + 0.1);
    gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.00001, audioCtx.currentTime + 0.5);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.5);
}

function log(msg, type = 'normal') {
    const li = document.createElement('li');
    li.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
    if (type === 'alert') li.className = 'alert';
    logList.insertBefore(li, logList.firstChild);
    if (logList.children.length > 50) logList.removeChild(logList.lastChild);
}

// Camera Handling
async function getCameras() {
    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(d => d.kind === 'videoinput');
        
        cameraSelect.innerHTML = '';
        videoDevices.forEach((device, index) => {
            const option = document.createElement('option');
            option.value = device.deviceId;
            option.text = device.label || `Camera ${index + 1}`;
            cameraSelect.appendChild(option);
        });

        // Add 'environment' option as default generic fallback
        const envOption = document.createElement('option');
        envOption.value = 'environment';
        envOption.text = 'Back Camera (Default)';
        if (videoDevices.length === 0) cameraSelect.appendChild(envOption);
        
    } catch (e) {
        console.error("Camera enumeration failed", e);
        log("Could not list cameras. Permission denied?", "alert");
    }
}

async function startCamera(deviceId = null) {
    if (state.videoStream) {
        state.videoStream.getTracks().forEach(track => track.stop());
    }

    const constraints = {
        video: {
            deviceId: deviceId ? { exact: deviceId } : undefined,
            facingMode: deviceId === 'environment' ? 'environment' : undefined,
            width: { ideal: 1280 },
            height: { ideal: 720 }
        }
    };

    try {
        state.videoStream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = state.videoStream;
        roiBox.style.display = 'block';
        log("Camera started");
    } catch (e) {
        log("Camera failed: " + e.message, "alert");
    }
}

// Tesseract Initialization
async function initOCR() {
    document.getElementById('loadingOverlay').style.display = 'flex';
    try {
        state.worker = await Tesseract.createWorker('eng');
        await state.worker.setParameters({
            tessedit_char_whitelist: '0123456789.-°CF',
            tessjs_create_hocr: '0',
            tessjs_create_tsv: '0',
        });
        log("OCR Engine Ready");
    } catch (e) {
        log("OCR Init Failed: " + e.message, "alert");
    } finally {
        document.getElementById('loadingOverlay').style.display = 'none';
    }
}

// Image Processing & OCR
function processFrame() {
    if (!state.running || state.isOcrBusy) return;

    // Get ROI coordinates relative to video
    const rect = roiBox.getBoundingClientRect();
    const vidRect = video.getBoundingClientRect();

    if (rect.width === 0 || rect.height === 0) return;

    // Calculate ratio
    const scaleX = video.videoWidth / vidRect.width;
    const scaleY = video.videoHeight / vidRect.height;

    const roiX = (rect.left - vidRect.left) * scaleX;
    const roiY = (rect.top - vidRect.top) * scaleY;
    const roiW = rect.width * scaleX;
    const roiH = rect.height * scaleY;

    // Draw frame to off-screen canvas for cropping
    canvas.width = roiW;
    canvas.height = roiH;
    ctx.drawImage(video, roiX, roiY, roiW, roiH, 0, 0, roiW, roiH);

    // Image Pre-processing (Enhance contrast for OCR)
    let imageData = ctx.getImageData(0, 0, roiW, roiH);
    let data = imageData.data;
    
    // Simple binarization
    for (let i = 0; i < data.length; i += 4) {
        let avg = (data[i] + data[i + 1] + data[i + 2]) / 3;
        let color = avg > 128 ? 255 : 0;
        data[i] = data[i + 1] = data[i + 2] = color;
    }
    ctx.putImageData(imageData, 0, 0);

    state.isOcrBusy = true;

    state.worker.recognize(canvas)
        .then(({ data: { text } }) => {
            const cleanText = text.trim();
            rawOcrEl.textContent = cleanText || "--";
            
            // Extract number
            const matches = cleanText.match(/-?\d+\.?\d*/);
            if (matches) {
                const temp = parseFloat(matches[0]);
                updateTemp(temp);
            }
        })
        .catch(err => console.error(err))
        .finally(() => {
            state.isOcrBusy = false;
            if (state.running) setTimeout(processFrame, 500); // 2fps limit
        });
}

function updateTemp(temp) {
    state.lastTemp = temp;
    currentTempEl.textContent = temp.toFixed(1);

    const { threshold, direction } = state.config;
    let trigger = false;

    if (direction === 'above' && temp >= threshold) trigger = true;
    if (direction === 'below' && temp <= threshold) trigger = true;

    if (trigger) {
        if (!state.alertTriggered) {
            triggerAlert(temp);
        }
    } else {
        // Reset alert status immediately if back to normal? 
        // No, keep cooldown logic or manual reset? 
        // Let's allow auto-reset if safe for a while, but simple logic for now:
        // Python script used a cooldown timer.
    }
}

function triggerAlert(temp) {
    state.alertTriggered = true;
    statusBadge.textContent = "ALERT";
    statusBadge.className = "status-badge alert";
    log(`Threshold reached: ${temp}°C`, "alert");
    playAlertSound();

    if (state.alertResetTimer) clearTimeout(state.alertResetTimer);
    
    // Auto reset after cooldown
    state.alertResetTimer = setTimeout(() => {
        state.alertTriggered = false;
        statusBadge.textContent = "Monitoring";
        statusBadge.className = "status-badge active";
        log("Alert cooldown finished");
    }, state.config.cooldown);
}

// Logic for ROI Dragging
let dragItem = null;
let active = false;
let currentX, currentY, initialX, initialY;
let xOffset = 0, yOffset = 0;

// Need to implement drag logic for ROI box...
// For simplicity in this v1, we will use a library or simple CSS resize
// Actually, standard touch events are needed.

function initDrag(el) {
    let isDragging = false;
    let startX, startY, startLeft, startTop;

    el.addEventListener('touchstart', dragStart, {passive: false});
    el.addEventListener('mousedown', dragStart);

    function dragStart(e) {
        if (e.target.classList.contains('roi-handle')) return; // Let resize handle it
        e.preventDefault();
        isDragging = true;
        
        const clientX = e.type === 'touchstart' ? e.touches[0].clientX : e.clientX;
        const clientY = e.type === 'touchstart' ? e.touches[0].clientY : e.clientY;
        
        startX = clientX;
        startY = clientY;
        startLeft = el.offsetLeft;
        startTop = el.offsetTop;

        document.addEventListener('touchmove', drag, {passive: false});
        document.addEventListener('touchend', dragEnd);
        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', dragEnd);
    }

    function drag(e) {
        if (!isDragging) return;
        e.preventDefault();
        
        const clientX = e.type === 'touchmove' ? e.touches[0].clientX : e.clientX;
        const clientY = e.type === 'touchmove' ? e.touches[0].clientY : e.clientY;

        const dx = clientX - startX;
        const dy = clientY - startY;

        el.style.left = `${startLeft + dx}px`;
        el.style.top = `${startTop + dy}px`;
    }

    function dragEnd() {
        isDragging = false;
        document.removeEventListener('touchmove', drag);
        document.removeEventListener('touchend', dragEnd);
        document.removeEventListener('mousemove', drag);
        document.removeEventListener('mouseup', dragEnd);
    }
}

// Resize logic
function initResize(box) {
    const handles = box.querySelectorAll('.roi-handle');
    
    handles.forEach(handle => {
        handle.addEventListener('touchstart', resizeStart, {passive: false});
        handle.addEventListener('mousedown', resizeStart);
    });

    function resizeStart(e) {
        e.stopPropagation();
        e.preventDefault();
        
        const handle = e.target;
        const clientX = e.type === 'touchstart' ? e.touches[0].clientX : e.clientX;
        const clientY = e.type === 'touchstart' ? e.touches[0].clientY : e.clientY;
        
        const startX = clientX;
        const startY = clientY;
        const startW = box.offsetWidth;
        const startH = box.offsetHeight;
        const startL = box.offsetLeft;
        const startT = box.offsetTop;

        const isTL = handle.classList.contains('roi-handle-tl');
        const isTR = handle.classList.contains('roi-handle-tr');
        const isBL = handle.classList.contains('roi-handle-bl');
        
        function resize(e) {
            e.preventDefault();
            const cx = e.type === 'touchmove' ? e.touches[0].clientX : e.clientX;
            const cy = e.type === 'touchmove' ? e.touches[0].clientY : e.clientY;
            
            const dx = cx - startX;
            const dy = cy - startY;

            if (isTR) {
                box.style.width = `${startW + dx}px`;
                box.style.height = `${startH - dy}px`;
                box.style.top = `${startT + dy}px`;
            } else if (isTL) {
                box.style.width = `${startW - dx}px`;
                box.style.height = `${startH - dy}px`;
                box.style.top = `${startT + dy}px`;
                box.style.left = `${startL + dx}px`;
            } else if (isBL) {
                box.style.width = `${startW - dx}px`;
                box.style.height = `${startH + dy}px`;
                box.style.left = `${startL + dx}px`;
            } else { // BR
                box.style.width = `${startW + dx}px`;
                box.style.height = `${startH + dy}px`;
            }
        }

        function stopResize() {
            document.removeEventListener('touchmove', resize);
            document.removeEventListener('touchend', stopResize);
            document.removeEventListener('mousemove', resize);
            document.removeEventListener('mouseup', stopResize);
        }

        document.addEventListener('touchmove', resize, {passive: false});
        document.addEventListener('touchend', stopResize);
        document.addEventListener('mousemove', resize);
        document.addEventListener('mouseup', stopResize);
    }
}


// Event Listeners
btnToggle.addEventListener('click', () => {
    state.running = !state.running;
    if (state.running) {
        if (!state.videoStream) startCamera(cameraSelect.value);
        btnToggle.textContent = "Stop Monitoring";
        btnToggle.className = "btn-danger";
        statusBadge.textContent = "Monitoring";
        statusBadge.className = "status-badge active";
        processFrame();
    } else {
        btnToggle.textContent = "Start Monitoring";
        btnToggle.className = "btn-primary";
        statusBadge.textContent = "Idle";
        statusBadge.className = "status-badge";
    }
});

document.getElementById('btnInc').addEventListener('click', () => {
    const el = document.getElementById('thresholdInput');
    el.value = parseFloat(el.value) + 0.5;
    state.config.threshold = parseFloat(el.value);
});

document.getElementById('btnDec').addEventListener('click', () => {
    const el = document.getElementById('thresholdInput');
    el.value = parseFloat(el.value) - 0.5;
    state.config.threshold = parseFloat(el.value);
});

document.getElementById('thresholdInput').addEventListener('change', (e) => {
    state.config.threshold = parseFloat(e.target.value);
});

document.getElementById('directionSelect').addEventListener('change', (e) => {
    state.config.direction = e.target.value;
});

cameraSelect.addEventListener('change', () => {
    if (state.running) {
        startCamera(cameraSelect.value);
    }
});

// Initialization
window.addEventListener('load', async () => {
    await getCameras();
    await initOCR();
    initDrag(roiBox);
    initResize(roiBox);
});
