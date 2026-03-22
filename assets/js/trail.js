// Oregon Trail pixel-art animated header scene
(function () {
  var canvas = document.getElementById('trail-canvas');
  if (!canvas) return;
  var ctx = canvas.getContext('2d');

  // Pixel scale for chunky retro look
  var PIXEL = 4;
  var wagonX = -60;
  var frameCount = 0;
  var raf;

  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function resize() {
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
  }

  function drawPixelRect(x, y, w, h, color) {
    ctx.fillStyle = color;
    // Snap to pixel grid
    var sx = Math.round(x / PIXEL) * PIXEL;
    var sy = Math.round(y / PIXEL) * PIXEL;
    var sw = Math.round(w / PIXEL) * PIXEL;
    var sh = Math.round(h / PIXEL) * PIXEL;
    ctx.fillRect(sx, sy, sw, sh);
  }

  function drawMountain(cx, baseY, height, width, color) {
    var steps = Math.floor(width / PIXEL / 2);
    for (var i = 0; i <= steps; i++) {
      var ratio = i / steps;
      var h = height * (1 - ratio);
      drawPixelRect(cx - i * PIXEL, baseY - h, PIXEL, h, color);
      drawPixelRect(cx + i * PIXEL, baseY - h, PIXEL, h, color);
    }
  }

  function drawTree(x, baseY, h, color) {
    // Trunk
    drawPixelRect(x, baseY - h * 0.3, PIXEL, h * 0.3, '#5a4a2a');
    // Canopy triangle
    for (var row = 0; row < 4; row++) {
      var w = (row + 1) * PIXEL;
      drawPixelRect(x - row * PIXEL, baseY - h * 0.3 - (4 - row) * PIXEL, w * 2, PIXEL, color);
    }
  }

  function drawCloud(x, y, w) {
    var color = cssVar('--canvas-cloud');
    drawPixelRect(x, y, w, PIXEL * 2, color);
    drawPixelRect(x + PIXEL, y - PIXEL, w - PIXEL * 2, PIXEL, color);
    drawPixelRect(x + PIXEL * 2, y + PIXEL * 2, w - PIXEL * 4, PIXEL, color);
  }

  function drawSun(x, y, r) {
    var color = cssVar('--canvas-sun');
    // Simple pixel circle approximation
    for (var dy = -r; dy <= r; dy += PIXEL) {
      for (var dx = -r; dx <= r; dx += PIXEL) {
        if (dx * dx + dy * dy <= r * r) {
          drawPixelRect(x + dx, y + dy, PIXEL, PIXEL, color);
        }
      }
    }
    // Rays
    var rayLen = r + PIXEL * 3;
    for (var a = 0; a < 8; a++) {
      var angle = a * Math.PI / 4 + frameCount * 0.005;
      var rx = x + Math.cos(angle) * rayLen;
      var ry = y + Math.sin(angle) * rayLen;
      drawPixelRect(rx, ry, PIXEL, PIXEL, color);
    }
  }

  function drawWagon(x, y, bobFrame) {
    var color = cssVar('--canvas-wagon');
    var bob = (bobFrame % 2 === 0) ? 0 : PIXEL;
    var woodColor = '#5a4a2a';
    var coverColor = '#e8dcc0';

    // --- Wheels (larger with spoke cross) ---
    var wheelR = PIXEL * 3;
    // Rear wheel
    var rwx = x + PIXEL * 3, rwy = y + PIXEL * 3 - bob;
    drawPixelRect(rwx, rwy, PIXEL, PIXEL, woodColor);
    drawPixelRect(rwx - PIXEL, rwy - PIXEL, PIXEL * 3, PIXEL, woodColor);
    drawPixelRect(rwx - PIXEL, rwy + PIXEL, PIXEL * 3, PIXEL, woodColor);
    drawPixelRect(rwx, rwy - PIXEL * 2, PIXEL, PIXEL, woodColor);
    drawPixelRect(rwx, rwy + PIXEL * 2, PIXEL, PIXEL, woodColor);
    drawPixelRect(rwx - PIXEL * 2, rwy, PIXEL, PIXEL, woodColor);
    drawPixelRect(rwx + PIXEL * 2, rwy, PIXEL, PIXEL, woodColor);
    // Front wheel
    var fwx = x + PIXEL * 11, fwy = y + PIXEL * 3 - bob;
    drawPixelRect(fwx, fwy, PIXEL, PIXEL, woodColor);
    drawPixelRect(fwx - PIXEL, fwy - PIXEL, PIXEL * 3, PIXEL, woodColor);
    drawPixelRect(fwx - PIXEL, fwy + PIXEL, PIXEL * 3, PIXEL, woodColor);
    drawPixelRect(fwx, fwy - PIXEL * 2, PIXEL, PIXEL, woodColor);
    drawPixelRect(fwx, fwy + PIXEL * 2, PIXEL, PIXEL, woodColor);
    drawPixelRect(fwx - PIXEL * 2, fwy, PIXEL, PIXEL, woodColor);
    drawPixelRect(fwx + PIXEL * 2, fwy, PIXEL, PIXEL, woodColor);

    // --- Wagon bed (flat base between wheels) ---
    drawPixelRect(x + PIXEL, y + PIXEL - bob, PIXEL * 13, PIXEL, woodColor);
    // Side walls
    drawPixelRect(x + PIXEL, y - bob, PIXEL * 13, PIXEL, color);
    drawPixelRect(x + PIXEL, y - PIXEL - bob, PIXEL, PIXEL * 2, woodColor);
    drawPixelRect(x + PIXEL * 13, y - PIXEL - bob, PIXEL, PIXEL * 2, woodColor);

    // --- Canopy hoops (the distinctive covered wagon arches) ---
    // Three hoops
    drawPixelRect(x + PIXEL * 2, y - PIXEL * 2 - bob, PIXEL, PIXEL * 2, woodColor);
    drawPixelRect(x + PIXEL * 7, y - PIXEL * 2 - bob, PIXEL, PIXEL * 2, woodColor);
    drawPixelRect(x + PIXEL * 12, y - PIXEL * 2 - bob, PIXEL, PIXEL * 2, woodColor);
    // Hoop tops
    drawPixelRect(x + PIXEL * 2, y - PIXEL * 5 - bob, PIXEL, PIXEL, woodColor);
    drawPixelRect(x + PIXEL * 7, y - PIXEL * 6 - bob, PIXEL, PIXEL, woodColor);
    drawPixelRect(x + PIXEL * 12, y - PIXEL * 5 - bob, PIXEL, PIXEL, woodColor);

    // --- Canvas cover (white bonnet shape) ---
    // Bottom edge
    drawPixelRect(x + PIXEL * 2, y - PIXEL * 2 - bob, PIXEL * 11, PIXEL, coverColor);
    // Middle
    drawPixelRect(x + PIXEL * 2, y - PIXEL * 3 - bob, PIXEL * 11, PIXEL, coverColor);
    drawPixelRect(x + PIXEL * 3, y - PIXEL * 4 - bob, PIXEL * 9, PIXEL, coverColor);
    // Top (arched)
    drawPixelRect(x + PIXEL * 3, y - PIXEL * 5 - bob, PIXEL * 9, PIXEL, coverColor);
    drawPixelRect(x + PIXEL * 4, y - PIXEL * 6 - bob, PIXEL * 7, PIXEL, coverColor);

    // --- Yoke / tongue (connects wagon to oxen) ---
    drawPixelRect(x + PIXEL * 14, y + PIXEL * 2 - bob, PIXEL * 4, PIXEL, woodColor);

    // --- Oxen (ahead, to the right of wagon) ---
    var oxColor = '#6b5030';
    var oxDark = '#4a3820';
    // Ox 1 body
    drawPixelRect(x + PIXEL * 18, y - bob, PIXEL * 4, PIXEL * 3, oxColor);
    // Ox 1 head (extends forward and up)
    drawPixelRect(x + PIXEL * 22, y - PIXEL - bob, PIXEL * 2, PIXEL * 2, oxColor);
    // Ox 1 horns
    drawPixelRect(x + PIXEL * 22, y - PIXEL * 2 - bob, PIXEL, PIXEL, oxDark);
    drawPixelRect(x + PIXEL * 24, y - PIXEL * 2 - bob, PIXEL, PIXEL, oxDark);
    // Ox 1 legs (alternate for walking)
    var legOff = (bobFrame % 2 === 0) ? 0 : PIXEL;
    drawPixelRect(x + PIXEL * 18 + legOff, y + PIXEL * 3 - bob, PIXEL, PIXEL * 2, oxColor);
    drawPixelRect(x + PIXEL * 21 - legOff, y + PIXEL * 3 - bob, PIXEL, PIXEL * 2, oxColor);
    // Ox 1 tail
    drawPixelRect(x + PIXEL * 17, y - bob, PIXEL, PIXEL * 2, oxDark);
  }

  function drawCactus(x, baseY, h) {
    var color = '#5b7828';
    // Trunk
    drawPixelRect(x, baseY - h, PIXEL, h, color);
    // Left arm
    drawPixelRect(x - PIXEL, baseY - h * 0.6, PIXEL, PIXEL * 2, color);
    drawPixelRect(x - PIXEL, baseY - h * 0.6 - PIXEL, PIXEL, PIXEL, color);
    // Right arm
    drawPixelRect(x + PIXEL, baseY - h * 0.4, PIXEL, PIXEL * 2, color);
    drawPixelRect(x + PIXEL, baseY - h * 0.4 - PIXEL, PIXEL, PIXEL, color);
  }

  function draw() {
    resize();
    var W = canvas.width;
    var H = canvas.height;
    var skyColor = cssVar('--canvas-sky');
    var groundColor = cssVar('--canvas-ground');
    var trailColor = cssVar('--canvas-trail');
    var mountainColor = cssVar('--canvas-mountain');
    var treeColor = cssVar('--canvas-tree');

    var groundY = H * 0.65;

    // Sky
    ctx.fillStyle = skyColor;
    ctx.fillRect(0, 0, W, groundY);

    // Sun
    drawSun(W - 60, 36, 16);

    // Clouds (drift slowly)
    var cloudOff = (frameCount * 0.15) % (W + 200);
    drawCloud((cloudOff + 50) % (W + 200) - 100, 24, PIXEL * 10);
    drawCloud((cloudOff + W * 0.4 + 120) % (W + 200) - 100, 40, PIXEL * 8);
    drawCloud((cloudOff + W * 0.7 + 200) % (W + 200) - 100, 16, PIXEL * 12);

    // Mountains
    drawMountain(W * 0.15, groundY, H * 0.35, W * 0.18, mountainColor);
    drawMountain(W * 0.4, groundY, H * 0.28, W * 0.15, mountainColor);
    drawMountain(W * 0.65, groundY, H * 0.32, W * 0.2, mountainColor);
    drawMountain(W * 0.85, groundY, H * 0.25, W * 0.12, mountainColor);

    // Snow caps
    var snowColor = '#d8d8c8';
    drawPixelRect(W * 0.15 - PIXEL, groundY - H * 0.35, PIXEL * 3, PIXEL, snowColor);
    drawPixelRect(W * 0.65 - PIXEL, groundY - H * 0.32, PIXEL * 3, PIXEL, snowColor);

    // Ground
    ctx.fillStyle = groundColor;
    ctx.fillRect(0, groundY, W, H - groundY);

    // Trail path (a lighter strip)
    var trailY = groundY + (H - groundY) * 0.4;
    drawPixelRect(0, trailY, W, PIXEL * 3, trailColor);

    // Trail dashes
    for (var dx = 0; dx < W; dx += PIXEL * 8) {
      var dashOff = (frameCount * 0.5) % (PIXEL * 8);
      drawPixelRect(dx - dashOff, trailY + PIXEL, PIXEL * 4, PIXEL, groundColor);
    }

    // Trees along horizon
    var treeSpacing = W / 7;
    for (var t = 0; t < 7; t++) {
      var tx = treeSpacing * t + treeSpacing * 0.3;
      var th = 16 + (t % 3) * 6;
      drawTree(tx, groundY, th, treeColor);
    }

    // Cacti
    drawCactus(W * 0.25, trailY - PIXEL, 20);
    drawCactus(W * 0.72, trailY - PIXEL, 16);

    // Wagon (animated, crossing the screen)
    var bobFrame = Math.floor(frameCount / 8);
    drawWagon(wagonX, trailY - PIXEL * 3, bobFrame);

    // Advance wagon
    wagonX += 0.6;
    if (wagonX > W + 80) wagonX = -80;

    frameCount++;
    raf = requestAnimationFrame(draw);
  }

  window.drawTrail = function () {
    cancelAnimationFrame(raf);
    frameCount = 0;
    draw();
  };

  draw();

  // Redraw on resize
  var resizeTimer;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      cancelAnimationFrame(raf);
      draw();
    }, 100);
  });
})();
