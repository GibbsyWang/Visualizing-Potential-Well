const fs = require('fs')
const path = require('path')

const releaseDir = path.resolve(__dirname, '..', 'release')

if (!fs.existsSync(releaseDir)) {
  console.log('[post-build] release directory not found, skip cleanup.')
  process.exit(0)
}

const entries = fs.readdirSync(releaseDir, { withFileTypes: true })
for (const entry of entries) {
  const fullPath = path.join(releaseDir, entry.name)
  if (entry.isDirectory()) {
    fs.rmSync(fullPath, { recursive: true, force: true })
    continue
  }
  if (!entry.name.toLowerCase().endsWith('.exe')) {
    fs.rmSync(fullPath, { force: true })
  }
}

const remaining = fs
  .readdirSync(releaseDir, { withFileTypes: true })
  .filter((entry) => entry.isFile() && entry.name.toLowerCase().endsWith('.exe'))
  .map((entry) => entry.name)

if (remaining.length === 0) {
  console.warn('[post-build] cleanup complete, but no exe found in release.')
} else if (remaining.length === 1) {
  console.log(`[post-build] cleanup complete, kept: ${remaining[0]}`)
} else {
  console.warn(`[post-build] multiple exe files found: ${remaining.join(', ')}`)
}
