const fs = require('fs')
const path = require('path')
const zlib = require('zlib')

const SIZE = 256
const OUT_DIR = path.resolve(__dirname, '..', 'build')
const PNG_PATH = path.join(OUT_DIR, 'icon.png')
const ICO_PATH = path.join(OUT_DIR, 'icon.ico')
const SVG_PATH = path.join(OUT_DIR, 'icon.svg')
const ELECTRON_ICON_PATH = path.resolve(__dirname, '..', 'electron', 'icon.png')
const FAVICON_PATH = path.resolve(__dirname, '..', 'public', 'favicon.png')

function clamp01(v) {
  if (v < 0) return 0
  if (v > 1) return 1
  return v
}

function lerp(a, b, t) {
  return a + (b - a) * t
}

function smoothstep(edge0, edge1, x) {
  const t = clamp01((x - edge0) / (edge1 - edge0))
  return t * t * (3 - 2 * t)
}

function createImage(width, height) {
  return { width, height, data: Buffer.alloc(width * height * 4) }
}

function blendPixel(img, x, y, r, g, b, a) {
  if (x < 0 || y < 0 || x >= img.width || y >= img.height) return
  if (a <= 0) return
  const i = (y * img.width + x) * 4
  const dstA = img.data[i + 3] / 255
  const outA = a + dstA * (1 - a)
  if (outA <= 0) return

  const dstR = img.data[i]
  const dstG = img.data[i + 1]
  const dstB = img.data[i + 2]

  const outR = (r * a + dstR * dstA * (1 - a)) / outA
  const outG = (g * a + dstG * dstA * (1 - a)) / outA
  const outB = (b * a + dstB * dstA * (1 - a)) / outA

  img.data[i] = Math.round(outR)
  img.data[i + 1] = Math.round(outG)
  img.data[i + 2] = Math.round(outB)
  img.data[i + 3] = Math.round(outA * 255)
}

function roundedRectSdf(px, py, cx, cy, hw, hh, r) {
  const qx = Math.abs(px - cx) - hw + r
  const qy = Math.abs(py - cy) - hh + r
  const ox = Math.max(qx, 0)
  const oy = Math.max(qy, 0)
  return Math.hypot(ox, oy) + Math.min(Math.max(qx, qy), 0) - r
}

function drawSoftCircle(img, cx, cy, radius, color, alpha = 1) {
  const minX = Math.floor(cx - radius - 1)
  const maxX = Math.ceil(cx + radius + 1)
  const minY = Math.floor(cy - radius - 1)
  const maxY = Math.ceil(cy + radius + 1)

  for (let y = minY; y <= maxY; y += 1) {
    for (let x = minX; x <= maxX; x += 1) {
      const dx = x + 0.5 - cx
      const dy = y + 0.5 - cy
      const d = Math.hypot(dx, dy)
      const t = clamp01(1 - d / radius)
      if (t <= 0) continue
      const a = alpha * t * t
      blendPixel(img, x, y, color[0], color[1], color[2], a)
    }
  }
}

function drawSoftRect(img, x0, y0, x1, y1, blur, color, alpha = 1) {
  const minX = Math.floor(x0 - blur - 1)
  const maxX = Math.ceil(x1 + blur + 1)
  const minY = Math.floor(y0 - blur - 1)
  const maxY = Math.ceil(y1 + blur + 1)

  for (let y = minY; y <= maxY; y += 1) {
    for (let x = minX; x <= maxX; x += 1) {
      const px = x + 0.5
      const py = y + 0.5
      const dx = Math.max(x0 - px, 0, px - x1)
      const dy = Math.max(y0 - py, 0, py - y1)
      const dist = Math.hypot(dx, dy)
      const t = clamp01(1 - dist / Math.max(blur, 1e-6))
      const a = alpha * (blur > 0 ? t : dist === 0 ? 1 : 0)
      if (a <= 0) continue
      blendPixel(img, x, y, color[0], color[1], color[2], a)
    }
  }
}

function drawIcon() {
  const img = createImage(SIZE, SIZE)

  const cx = SIZE / 2
  const cy = SIZE / 2
  const hw = 110
  const hh = 110
  const corner = 34

  // Rounded-square background with blue-purple gradient.
  for (let y = 0; y < SIZE; y += 1) {
    for (let x = 0; x < SIZE; x += 1) {
      const px = x + 0.5
      const py = y + 0.5
      const sdf = roundedRectSdf(px, py, cx, cy, hw, hh, corner)
      const mask = smoothstep(1.0, -1.0, sdf)
      if (mask <= 0) continue

      const tx = px / SIZE
      const ty = py / SIZE
      const g = clamp01((tx * 0.6 + ty * 0.9) / 1.5)
      const vignette = clamp01(1 - Math.hypot(tx - 0.5, ty - 0.5) * 1.3)

      const r = Math.round(lerp(20, 132, g) * (0.75 + vignette * 0.25))
      const gg = Math.round(lerp(72, 43, g) * (0.75 + vignette * 0.25))
      const b = Math.round(lerp(196, 220, g) * (0.75 + vignette * 0.25))
      blendPixel(img, x, y, r, gg, b, mask)

      // Subtle inner border.
      const border = clamp01(1 - Math.abs(sdf + 2.5) / 2.0) * 0.16
      if (border > 0) {
        blendPixel(img, x, y, 245, 246, 255, border)
      }
    }
  }

  const wallLeft = 70
  const wallRight = 186
  const wallTop = 60
  const wallBottom = 196

  // Potential well walls.
  drawSoftRect(img, wallLeft - 5, wallTop, wallLeft + 5, wallBottom, 1.5, [244, 246, 255], 0.95)
  drawSoftRect(img, wallRight - 5, wallTop, wallRight + 5, wallBottom, 1.5, [244, 246, 255], 0.95)

  // Energy levels inside the well.
  const levels = [84, 112, 140, 168]
  for (const y of levels) {
    drawSoftRect(img, wallLeft + 8, y - 1, wallRight - 8, y + 1, 2, [185, 205, 255], 0.33)
  }

  // Wavefunction curve.
  const waveColor = [255, 104, 104]
  for (let x = wallLeft + 6; x <= wallRight - 6; x += 0.9) {
    const t = (x - (wallLeft + 6)) / ((wallRight - 6) - (wallLeft + 6))
    const y = 128 + Math.sin(t * Math.PI * 3.0) * 30
    drawSoftCircle(img, x, y, 2.8, waveColor, 0.92)
    drawSoftCircle(img, x, y, 6.5, waveColor, 0.12)
  }

  // Small "particle" marker on the wave.
  const px = 156
  const pt = (px - (wallLeft + 6)) / ((wallRight - 6) - (wallLeft + 6))
  const py = 128 + Math.sin(pt * Math.PI * 3.0) * 30
  drawSoftCircle(img, px, py, 7, [255, 240, 120], 0.85)
  drawSoftCircle(img, px, py, 13, [255, 240, 120], 0.20)

  // Bottom accent.
  drawSoftRect(img, 52, 205, 204, 212, 6, [140, 198, 255], 0.35)

  return img
}

function makeCrcTable() {
  const table = new Uint32Array(256)
  for (let n = 0; n < 256; n += 1) {
    let c = n
    for (let k = 0; k < 8; k += 1) {
      c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1)
    }
    table[n] = c >>> 0
  }
  return table
}

const CRC_TABLE = makeCrcTable()

function crc32(buf) {
  let c = 0xffffffff
  for (let i = 0; i < buf.length; i += 1) {
    c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8)
  }
  return (c ^ 0xffffffff) >>> 0
}

function pngChunk(type, data) {
  const typeBuf = Buffer.from(type, 'ascii')
  const len = Buffer.alloc(4)
  len.writeUInt32BE(data.length, 0)

  const crcBuf = Buffer.alloc(4)
  const crc = crc32(Buffer.concat([typeBuf, data]))
  crcBuf.writeUInt32BE(crc, 0)

  return Buffer.concat([len, typeBuf, data, crcBuf])
}

function encodePng(img) {
  const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])

  const ihdr = Buffer.alloc(13)
  ihdr.writeUInt32BE(img.width, 0)
  ihdr.writeUInt32BE(img.height, 4)
  ihdr[8] = 8 // bit depth
  ihdr[9] = 6 // RGBA
  ihdr[10] = 0 // compression
  ihdr[11] = 0 // filter
  ihdr[12] = 0 // interlace

  const stride = img.width * 4
  const raw = Buffer.alloc((stride + 1) * img.height)
  for (let y = 0; y < img.height; y += 1) {
    const rowStart = y * (stride + 1)
    raw[rowStart] = 0 // filter type 0
    img.data.copy(raw, rowStart + 1, y * stride, y * stride + stride)
  }

  const compressed = zlib.deflateSync(raw, { level: 9 })
  const chunks = [
    pngChunk('IHDR', ihdr),
    pngChunk('IDAT', compressed),
    pngChunk('IEND', Buffer.alloc(0))
  ]
  return Buffer.concat([sig, ...chunks])
}

function encodeIcoFromPng(pngBytes) {
  const header = Buffer.alloc(6)
  header.writeUInt16LE(0, 0) // reserved
  header.writeUInt16LE(1, 2) // type: icon
  header.writeUInt16LE(1, 4) // image count

  const dir = Buffer.alloc(16)
  dir[0] = 0 // 256 width
  dir[1] = 0 // 256 height
  dir[2] = 0 // color count
  dir[3] = 0 // reserved
  dir.writeUInt16LE(1, 4) // planes
  dir.writeUInt16LE(32, 6) // bit count
  dir.writeUInt32LE(pngBytes.length, 8) // image size
  dir.writeUInt32LE(6 + 16, 12) // image offset

  return Buffer.concat([header, dir, pngBytes])
}

function writeSvgReference() {
  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#164bc4"/>
      <stop offset="100%" stop-color="#7b2dbf"/>
    </linearGradient>
    <filter id="soft" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="1.8"/>
    </filter>
  </defs>
  <rect x="18" y="18" width="220" height="220" rx="34" fill="url(#bg)"/>
  <rect x="65" y="60" width="10" height="136" rx="3" fill="#f7f9ff"/>
  <rect x="181" y="60" width="10" height="136" rx="3" fill="#f7f9ff"/>
  <g stroke="#bed2ff" stroke-width="2" opacity="0.35">
    <line x1="78" y1="84" x2="178" y2="84"/>
    <line x1="78" y1="112" x2="178" y2="112"/>
    <line x1="78" y1="140" x2="178" y2="140"/>
    <line x1="78" y1="168" x2="178" y2="168"/>
  </g>
  <path d="M76,128 C94,84 110,172 128,128 C146,84 162,172 180,128" fill="none" stroke="#ff6969" stroke-width="6" stroke-linecap="round"/>
  <circle cx="156" cy="152" r="7" fill="#ffe878"/>
  <circle cx="156" cy="152" r="13" fill="#ffe878" opacity="0.25" filter="url(#soft)"/>
  <rect x="52" y="205" width="152" height="7" rx="3.5" fill="#8cc6ff" opacity="0.35" filter="url(#soft)"/>
</svg>
`
  fs.writeFileSync(SVG_PATH, svg, 'utf8')
}

function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true })
  fs.mkdirSync(path.dirname(ELECTRON_ICON_PATH), { recursive: true })
  fs.mkdirSync(path.dirname(FAVICON_PATH), { recursive: true })

  const icon = drawIcon()
  const png = encodePng(icon)
  const ico = encodeIcoFromPng(png)

  fs.writeFileSync(PNG_PATH, png)
  fs.writeFileSync(ICO_PATH, ico)
  fs.writeFileSync(ELECTRON_ICON_PATH, png)
  fs.writeFileSync(FAVICON_PATH, png)
  writeSvgReference()

  console.log(`Generated: ${PNG_PATH}`)
  console.log(`Generated: ${ICO_PATH}`)
  console.log(`Generated: ${SVG_PATH}`)
  console.log(`Generated: ${ELECTRON_ICON_PATH}`)
  console.log(`Generated: ${FAVICON_PATH}`)
}

main()
