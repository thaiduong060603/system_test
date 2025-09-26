
let pushupCount = 0;
let squatCount = 0;
let detector = null;
let flag_pushup = 'up';
let flag_squat = 'up';
let pushupState = { max_angle: 0, min_angle: 180, farthest_distance: null, closest_distance: null };
let squatState = { max_angle: 0, min_angle: 180, farthest_distance: null, closest_distance: null };

// Khai báo biến nhưng chưa gán giá trị ngay
let video, canvas, ctx, statusDiv;

// Mock inputs for thresholds (set dynamically)
const pushupThresholdInput = { value: 100 };
const squatThresholdInput = { value: 80 };
const distanceThresholdInput = { value: 30 };

// Hàm khởi tạo DOM elements
function initializeDOMElements() {
    video = document.getElementById('video');
    canvas = document.getElementById('output');
    statusDiv = document.getElementById('status');
    
    if (canvas) {
        ctx = canvas.getContext('2d');
    } else {
        console.error('Canvas element not found');
    }
}

async function setupDetector() {
    if (detector) return;
    
    // Đảm bảo DOM elements đã được khởi tạo
    if (!statusDiv) {
        initializeDOMElements();
    }
    
    try {
        statusDiv.innerText = 'Đang khởi tạo mô hình...';
        const detectorConfig = {
            modelType: poseDetection.movenet.modelType.SINGLEPOSE_LIGHTNING
        };
        detector = await poseDetection.createDetector(poseDetection.SupportedModels.MoveNet, detectorConfig);
        statusDiv.innerText = 'Mô hình đã sẵn sàng.';
        
        if (video && video.srcObject) {
            renderPrediction();
        }
    } catch (error) {
        statusDiv.innerText = `Lỗi khởi tạo mô hình: ${error.message}`;
    }
}

async function openCamera() {
    // Đảm bảo DOM elements đã được khởi tạo
    if (!video || !statusDiv) {
        initializeDOMElements();
    }
    
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        video.play();
        
        // Đợi video load xong
        video.addEventListener('loadeddata', () => {
            if (canvas) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
            }
            if (detector) {
                renderPrediction();
            }
        });
        
    } catch (err) {
        statusDiv.innerText = 'Lỗi truy cập camera: ' + err.message;
    }
}

function resetCounts() {
    pushupCount = 0;
    squatCount = 0;
    flag_pushup = 'up';
    flag_squat = 'up';
    pushupState.max_angle = 0;
    pushupState.min_angle = 180;
    pushupState.farthest_distance = null;
    pushupState.closest_distance = null;
    squatState.max_angle = 0;
    squatState.min_angle = 180;
    squatState.farthest_distance = null;
    squatState.closest_distance = null;
}

async function renderPrediction() {
    if (!video || !ctx || !statusDiv) {
        initializeDOMElements();
        return;
    }
    
    if (video.readyState === 4 && detector && !window.inRest) {
        const poses = await detector.estimatePoses(video);
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (poses && poses.length > 0) {
            const keypoints = poses[0].keypoints;
            const ex = window.exercises[window.currentExerciseIndex];
            const angleThres = parseFloat(ex.thresholds.angle_threshold);
            const distThres = parseFloat(ex.thresholds.distance_threshold);
            
            const { elbowSide, kneeSide } = selectBestSide(keypoints);
            const elbowKeypointIndices = elbowSide === 'left' ? [5, 7, 9] : [6, 8, 10];
            const kneeKeypointIndices = kneeSide === 'left' ? [11, 13, 15] : [12, 14, 16];
            
            const elbowAngle = getAngle(keypoints[elbowKeypointIndices[0]], keypoints[elbowKeypointIndices[1]], keypoints[elbowKeypointIndices[2]]);
            const kneeAngle = getAngle(keypoints[kneeKeypointIndices[0]], keypoints[kneeKeypointIndices[1]], keypoints[kneeKeypointIndices[2]]);
            
            const shoulderKeypoint = keypoints[elbowKeypointIndices[0]];
            const kneeKeypoint = keypoints[kneeKeypointIndices[1]];
            const shoulderToKneeDistance = getEuclideanDistance(shoulderKeypoint, kneeKeypoint);
            
            if (ex.name === 'pushup') {
                processPushup(elbowAngle, shoulderToKneeDistance, angleThres, distThres);
            } else if (ex.name === 'squat') {
                processSquat(kneeAngle, shoulderToKneeDistance, angleThres, distThres);
            }
            
            drawKeypoints(keypoints, ctx);
            drawSkeleton(keypoints, ctx);
            
            if (elbowAngle) drawAngle(keypoints[elbowKeypointIndices[0]], keypoints[elbowKeypointIndices[1]], keypoints[elbowKeypointIndices[2]], ctx, `Elbow: ${elbowAngle.toFixed(1)}°`);
            if (kneeAngle) drawAngle(keypoints[kneeKeypointIndices[0]], keypoints[kneeKeypointIndices[1]], keypoints[kneeKeypointIndices[2]], ctx, `Knee: ${kneeAngle.toFixed(1)}°`);
        }
    }
    requestAnimationFrame(renderPrediction);
}

function processPushup(elbowAngle, shoulderToKneeDistance, angleThres, distThres) {
    if (shoulderToKneeDistance === null || elbowAngle === null) return;
    
    if (flag_pushup === 'up') {
        if (elbowAngle > pushupState.max_angle) {
            pushupState.max_angle = elbowAngle;
            pushupState.farthest_distance = shoulderToKneeDistance;
        }
        if (elbowAngle < angleThres && pushupState.max_angle > 0) {
            flag_pushup = 'down';
        }
    } else if (flag_pushup === 'down') {
        if (elbowAngle < pushupState.min_angle) {
            pushupState.min_angle = elbowAngle;
            pushupState.closest_distance = shoulderToKneeDistance;
        }
        if (elbowAngle > angleThres + 20) {
            flag_pushup = 'up';
            const distanceChange = Math.abs(pushupState.farthest_distance - pushupState.closest_distance);
            if (distanceChange < distThres) {
                pushupCount++;
                if (window.onRepComplete) {
                    window.onRepComplete('pushup');
                }
            }
            pushupState.max_angle = 0;
            pushupState.min_angle = 180;
            pushupState.farthest_distance = null;
            pushupState.closest_distance = null;
        }
    }
}

function processSquat(kneeAngle, shoulderToKneeDistance, angleThres, distThres) {
    if (shoulderToKneeDistance === null || kneeAngle === null) return;
    
    if (flag_squat === 'up') {
        if (kneeAngle > squatState.max_angle) {
            squatState.max_angle = kneeAngle;
            squatState.farthest_distance = shoulderToKneeDistance;
        }
        if (kneeAngle < angleThres && squatState.max_angle > 0) {
            flag_squat = 'down';
        }
    } else if (flag_squat === 'down') {
        if (kneeAngle < squatState.min_angle) {
            squatState.min_angle = kneeAngle;
            squatState.closest_distance = shoulderToKneeDistance;
        }
        if (kneeAngle > angleThres + 20) {
            flag_squat = 'up';
            const distanceChange = Math.abs(squatState.farthest_distance - squatState.closest_distance);
            if (distanceChange > distThres) {
                squatCount++;
                if (window.onRepComplete) {
                    window.onRepComplete('squat');
                }
            }
            squatState.max_angle = 0;
            squatState.min_angle = 180;
            squatState.farthest_distance = null;
            squatState.closest_distance = null;
        }
    }
}

// Export các biến cần thiết ra global scope
window.pushupThresholdInput = pushupThresholdInput;
window.squatThresholdInput = squatThresholdInput;
window.distanceThresholdInput = distanceThresholdInput;
window.setupDetector = setupDetector;
window.openCamera = openCamera;
window.resetCounts = resetCounts;

// Khởi tạo DOM elements khi script load
document.addEventListener('DOMContentLoaded', function() {
    initializeDOMElements();
});