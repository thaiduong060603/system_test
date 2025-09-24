function getAngle(p1, p2, p3) {
  if (!p1 || !p2 || !p3 || p1.score < 0.5 || p2.score < 0.5 || p3.score < 0.5) return null;
  const a = Math.hypot(p2.x - p1.x, p2.y - p1.y);
  const b = Math.hypot(p2.x - p3.x, p2.y - p3.y);
  const c = Math.hypot(p1.x - p3.x, p1.y - p3.y);
  if (a === 0 || b === 0) return null;
  return Math.acos((a * a + b * b - c * c) / (2 * a * b)) * 180 / Math.PI;
}

function drawKeypoints(keypoints, ctx) {
  keypoints.forEach(kp => {
    if (kp.score > 0.5) {
      ctx.beginPath();
      ctx.arc(kp.x, kp.y, 4, 0, 2 * Math.PI);
      ctx.fillStyle = 'red';
      ctx.fill();
    }
  });
}

const skeletonConnections = [
  [0, 1], [0, 2], [1, 3], [2, 4],
  [5, 6], [5, 7], [7, 9], [6, 8], [8, 10],
  [5, 11], [6, 12], [11, 12], [11, 13], [13, 15], [12, 14], [14, 16]
];

function drawSkeleton(keypoints, ctx) {
  ctx.strokeStyle = 'green';
  ctx.lineWidth = 2;
  skeletonConnections.forEach(([i, j]) => {
    const p1 = keypoints[i], p2 = keypoints[j];
    if (p1 && p2 && p1.score > 0.5 && p2.score > 0.5) {
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
    }
  });
}

function drawAngle(p1, p2, p3, ctx, text) {
  if (!p1 || !p2 || !p3 || p1.score < 0.5 || p2.score < 0.5 || p3.score < 0.5) return;
  ctx.beginPath();
  ctx.moveTo(p1.x, p1.y);
  ctx.lineTo(p2.x, p2.y);
  ctx.lineTo(p3.x, p3.y);
  ctx.strokeStyle = 'purple';
  ctx.stroke();
  ctx.fillStyle = 'black';
  ctx.fillText(text, p2.x + 10, p2.y - 10);
}

function selectBestSide(keypoints) {
  const leftElbow = [keypoints[5], keypoints[7], keypoints[9]];
  const rightElbow = [keypoints[6], keypoints[8], keypoints[10]];
  const leftKnee = [keypoints[11], keypoints[13], keypoints[15]];
  const rightKnee = [keypoints[12], keypoints[14], keypoints[16]];

  const leftElbowScore = leftElbow.reduce((s, p) => s + (p ? p.score : 0), 0) / 3;
  const rightElbowScore = rightElbow.reduce((s, p) => s + (p ? p.score : 0), 0) / 3;
  const leftKneeScore = leftKnee.reduce((s, p) => s + (p ? p.score : 0), 0) / 3;
  const rightKneeScore = rightKnee.reduce((s, p) => s + (p ? p.score : 0), 0) / 3;

  return {
    elbowSide: leftElbowScore >= rightElbowScore ? "left" : "right",
    kneeSide: leftKneeScore >= rightKneeScore ? "left" : "right"
  };
}

function getEuclideanDistance(p1, p2) {
  if (!p1 || !p2 || p1.score < 0.5 || p2.score < 0.5) return null;
  return Math.hypot(p2.x - p1.x, p2.y - p1.y);
}