<template>
  <!-- 2D 页面：左侧参数面板，右侧显示四个 Plotly / Canvas 图形区域。 -->
  <AppLayout>
    <template #sidebar>
      <div class="sidebar">
        <div class="formulas">
          <h3 class="formulas-title">Formulas</h3>
          <div class="formulas-item">
            <KatexRenderer :expression="waveFunction2DExpression" :displayMode="true" />
          </div>
          <div class="formulas-item">
            <KatexRenderer :expression="energy2DExpression" :displayMode="true" />
          </div>
        </div>

        <div class="parameter">
          <h3 class="parameter-title">Set parameters</h3>

          <div class="parameter-item">
            <div class="parameter-item-label">
              <label for="quantum-number-x">Quantum number x (n<sub>x</sub>):</label>
              <div class="parameter-item-value">{{ n_x }}</div>
            </div>
            <Slider v-model:value="n_x" :min="1" :max="5" :marks="marks" :step="1" @change="handleChangePlotNX" @afterChange="handleAfterChange" />
          </div>

          <div class="parameter-item">
            <div class="parameter-item-label">
              <label for="quantum-number-y">Quantum number y (n<sub>y</sub>):</label>
              <div class="parameter-item-value">{{ n_y }}</div>
            </div>
            <Slider v-model:value="n_y" :min="1" :max="5" :marks="marks" :step="1" @change="handleChangePlotNY" @afterChange="handleAfterChange" />
          </div>

          <div class="parameter-item">
            <div class="parameter-item-label">
              <label for="length-x">Length x (L<sub>x</sub>):</label>
              <div class="parameter-item-value">{{ L_x.toFixed(2) }}</div>
            </div>
            <Slider v-model:value="L_x" :min="1.0" :max="5.0" :marks="marksL" :step="0.05" @change="handleChangePlotLX" @afterChange="handleAfterChange" />
          </div>

        <div class="parameter-item">
          <div class="parameter-item-label">
            <label for="length-y">Length y (L<sub>y</sub>):</label>
            <div class="parameter-item-value">{{ L_y.toFixed(2) }}</div>
          </div>
          <Slider v-model:value="L_y" :min="1.0" :max="5.0" :marks="marksL" :step="0.05" :disabled="lockLxLy" @change="handleChangePlotLY" @afterChange="handleAfterChange" />
        </div>

        <div class="parameter-item parameter-item--compact">
          <label class="lock-toggle">
            <input v-model="lockLxLy" type="checkbox" />
            <span>Lock L<sub>x</sub> = L<sub>y</sub></span>
          </label>
        </div>

        <div class="parameter-item">
          <div class="parameter-item-label">
            <span>Has degenerate orbital?</span>
            <div class="parameter-item-value">{{ hasDegeneracy ? 'Yes' : 'No' }}</div>
          </div>
        </div>

          <div class="operator">
              <div class="operator-item">
                <div class="performance">
                  <div class="performance-metric">
                    <span>FPS</span>
                    <span class="performance-value">{{ fps }}</span>
                  </div>
                  <div class="performance-metric">
                    <span>Compute grid</span>
                    <span class="performance-value">{{ perfStats.build.toFixed(2) }} ms</span>
                  </div>
                  <div class="performance-metric">
                    <span>Plot ψ</span>
                    <span class="performance-value">{{ perfStats.psi.toFixed(2) }} ms</span>
                  </div>
                  <div class="performance-metric">
                    <span>Plot ψ<sup>2</sup></span>
                    <span class="performance-value">{{ perfStats.psi2.toFixed(2) }} ms</span>
                  </div>
                  <div class="performance-metric">
                    <span>Plot energy</span>
                    <span class="performance-value">{{ perfStats.energy.toFixed(2) }} ms</span>
                  </div>
                  <div class="performance-metric">
                    <span>Heatmap</span>
                    <span class="performance-value">{{ perfStats.heatmap.toFixed(2) }} ms</span>
                  </div>
                  <div class="performance-metric">
                    <span>Total</span>
                    <span class="performance-value">{{ perfStats.total.toFixed(2) }} ms</span>
                  </div>
                </div>
                <BackToHomeButton />
              </div>
            </div>
        </div>
      </div>
    </template>

    <template #content>
      <div class="plot-container">
        <h1 class="plot-container-title"><span class="plot-mark">2D</span> Infinite Square Well</h1>

        <div class="plot-row">
          <div class="plot-col">
            <div id="psi-3d" class="plot-box"></div>
          </div>
          <div class="plot-col">
            <div id="psi2-3d" class="plot-box"></div>
          </div>
        </div>
        <div class="plot-row">
          <div class="plot-col">
            <div id="energy-3d" class="plot-box"></div>
          </div>
          <div class="plot-col">
            <div id="energy-heatmap" class="plot-box"></div>
          </div>
        </div>
      </div>
    </template>
  </AppLayout>
</template>

<script setup>
  // 依赖导入：包含状态管理、通用组件与绘图工具。
  import { ref, computed, onMounted, onBeforeUnmount, onUnmounted, watch } from 'vue'
  import AppLayout from '@/components/layout/AppLayout.vue'
  import BackToHomeButton from '@/components/backToHome/BackToHomeButton.vue'
  import KatexRenderer from '@/components/katex/KatexRenderer.vue'
  import { Slider } from 'ant-design-vue'
  import { marks, marksL } from './constants'
  import { debounce } from '@/utils/debounce'
  import { loadPlotly } from '@/utils/loadPlotly'

  // 响应式状态：量子数、边长、锁定选项、拖拽状态与性能指标。
  const n_x = ref(1)
  const n_y = ref(1)
  const L_x = ref(1.0)
  const L_y = ref(1.0)
  const lockLxLy = ref(false)
  const isDragging = ref(false)
  const fps = ref(0)
  const perfStats = ref({
    build: 0,
    psi: 0,
    psi2: 0,
    energy: 0,
    heatmap: 0,
    total: 0
  })

  // 公式展示：在侧边栏实时显示 2D 波函数和能量表达式。
  const waveFunction2DExpression = computed(() => `\\psi_{n_x,n_y}(x, y) = \\sqrt{\\frac{4}{L_x L_y}} \\sin(\\frac{n_x \\pi x}{L_x}) \\sin(\\frac{n_y \\pi y}{L_y})`)
  const energy2DExpression = computed(() => `E_{n_x,n_y} = \\frac{\\pi^2 \\hbar^2}{2m_e} \\left(\\frac{n_x^2}{L_x^2} + \\frac{n_y^2}{L_y^2}\\right)`)
  const hasDegeneracy = computed(() => {
    const sameLength = Math.abs(L_x.value - L_y.value) < 1e-6
    return sameLength && n_x.value !== n_y.value
  })

  // 交互处理：滑块拖拽时区分实时预览与拖拽结束后的稳定重绘。
  const handleChangePlotNX = (val) => {
    isDragging.value = true
    n_x.value = val
    scheduleDraw()
  }
  const handleChangePlotNY = (val) => {
    isDragging.value = true
    n_y.value = val
    scheduleDraw()
  }
  const handleChangePlotLX = (val) => {
    isDragging.value = true
    L_x.value = val
    if (lockLxLy.value) {
      L_y.value = val
    }
    scheduleDraw()
  }
  const handleChangePlotLY = (val) => {
    isDragging.value = true
    L_y.value = lockLxLy.value ? L_x.value : val
    scheduleDraw()
  }
  const handleAfterChange = () => {
    if (!isDragging.value) return
    isDragging.value = false
    scheduleDraw()
  }

  // 绘图基础配置：控制采样精度、颜色、布局与标题字号。
  const NUM_POINTS_HIGH = 60
  const NUM_POINTS_LOW = 30
  let isActive = false
  let fpsRaf = 0
  let fpsFrames = 0
  let fpsLast = 0
  let Plotly = null
  let psiInitialized = false
  let psi2Initialized = false
  let psiHeightCache = 0
  let psi2HeightCache = 0
  const BASE_CONFIG = { responsive: true, displaylogo: false }
  const PSI_COLORSCALE = [
    [0, '#0000ff'],
    [0.5, '#ffffff'],
    [1, '#ff0000']
  ]
  const PSI2_COLORSCALE = 'Viridis'
  const getPlotTitleFontSize = () => {
    const containerWidth = document.querySelector('.plot-container')?.getBoundingClientRect().width || window.innerWidth
    return Math.max(12, Math.min(24, Math.round(containerWidth / 52)))
  }
  const buildPlotTitle = (text) => ({
    text,
    x: 0.5,
    xanchor: 'center',
    y: 0.98,
    yanchor: 'top',
    font: { size: getPlotTitleFontSize(), color: '#000000' }
  })
  const PSI_LAYOUT_BASE = {
    autosize: true,
    uirevision: 'psi-2d',
    title: buildPlotTitle('Wavefunction (ψ)'),
    scene: {
      xaxis: {
        title: 'x',
        tickmode: 'linear',
        tick0: 0,
        dtick: 1,
        showline: false,
        linecolor: 'rgba(0,0,0,0)',
        showgrid: true,
        gridcolor: '#d9d9d9',
        zeroline: false
      },
      yaxis: {
        title: 'y',
        tickmode: 'linear',
        tick0: 0,
        dtick: 1,
        showline: false,
        linecolor: 'rgba(0,0,0,0)',
        showgrid: true,
        gridcolor: '#d9d9d9',
        zeroline: false
      },
      zaxis: {
        title: { text: 'ψ' },
        range: [-2.5, 2.5],
        autorange: false,
        tickmode: 'linear',
        tick0: 0,
        dtick: 1,
        showline: false,
        linecolor: 'rgba(0,0,0,0)',
        showgrid: true,
        gridcolor: '#d9d9d9'
      },
      aspectratio: { x: 1, y: 1, z: 1 }
    },
    margin: { l: 10, r: 10, t: 40, b: 10 }
  }
  const PSI2_LAYOUT_BASE = {
    autosize: true,
    uirevision: 'psi2-2d',
    title: buildPlotTitle('Probability density (ψ²)'),
    scene: {
      xaxis: {
        title: 'x',
        tickmode: 'linear',
        tick0: 0,
        dtick: 1,
        showline: false,
        linecolor: 'rgba(0,0,0,0)',
        showgrid: true,
        gridcolor: '#d9d9d9',
        zeroline: false
      },
      yaxis: {
        title: 'y',
        tickmode: 'linear',
        tick0: 0,
        dtick: 1,
        showline: false,
        linecolor: 'rgba(0,0,0,0)',
        showgrid: true,
        gridcolor: '#d9d9d9',
        zeroline: false
      },
      zaxis: {
        title: { text: 'ψ²' },
        range: [0, 4],
        autorange: false,
        tickmode: 'linear',
        tick0: 0,
        dtick: 1,
        showline: false,
        linecolor: 'rgba(0,0,0,0)',
        showgrid: true,
        gridcolor: '#d9d9d9',
        zeroline: false
      },
      aspectratio: { x: 1, y: 1, z: 1 }
    },
    margin: { l: 10, r: 10, t: 40, b: 10 }
  }
  const SURFACE_COLORBAR_BASE = {
    thickness: 16,
    thicknessmode: 'pixels',
    len: 0.82,
    lenmode: 'fraction',
    xpad: 6
  }
  const buildPsiLayout = (height, lx, ly) => ({
    ...PSI_LAYOUT_BASE,
    title: buildPlotTitle('Wavefunction (ψ)'),
    height,
    scene: {
      ...PSI_LAYOUT_BASE.scene,
      xaxis: { ...PSI_LAYOUT_BASE.scene.xaxis, range: [0, lx], autorange: false },
      yaxis: { ...PSI_LAYOUT_BASE.scene.yaxis, range: [0, ly], autorange: false },
      zaxis: { ...PSI_LAYOUT_BASE.scene.zaxis }
    }
  })
  const buildPsi2Layout = (height, lx, ly) => ({
    ...PSI2_LAYOUT_BASE,
    title: buildPlotTitle('Probability density (ψ²)'),
    height,
    scene: {
      ...PSI2_LAYOUT_BASE.scene,
      xaxis: { ...PSI2_LAYOUT_BASE.scene.xaxis, range: [0, lx], autorange: false },
      yaxis: { ...PSI2_LAYOUT_BASE.scene.yaxis, range: [0, ly], autorange: false },
      zaxis: { ...PSI2_LAYOUT_BASE.scene.zaxis }
    }
  })
  const startFpsMonitor = () => {
    fpsLast = performance.now()
    fpsFrames = 0
    const tick = (now) => {
      fpsFrames += 1
      const elapsed = now - fpsLast
      if (elapsed >= 500) {
        fps.value = Math.round((fpsFrames * 1000) / elapsed)
        fpsFrames = 0
        fpsLast = now
      }
      fpsRaf = window.requestAnimationFrame(tick)
    }
    fpsRaf = window.requestAnimationFrame(tick)
  }
  const ensurePlotly = async () => {
    if (Plotly) return Plotly
    Plotly = await loadPlotly()
    return Plotly
  }

  // 归一化网格缓存：L 改变时复用基础正弦值，减少重复计算。
  let baseSurfaceCache = { nx: null, ny: null, points: null, u: [], v: [], z: [], z2: [], maxAbs: 0 }
  const axisCache = { points: null, x: new Map(), y: new Map() }
  const getAxisKey = (val) => Number(val).toFixed(2)

  const buildNormalizedGrid = (points) => {
    const u = []
    const v = []
    const step = 1 / (points - 1)
    for (let i = 0; i < points; i += 1) {
      const val = i * step
      u.push(val)
      v.push(val)
    }
    return { u, v }
  }

  const buildBaseSurface = (nx, ny, points) => {
    if (baseSurfaceCache.nx === nx &&
      baseSurfaceCache.ny === ny &&
      baseSurfaceCache.points === points) {
      return baseSurfaceCache
    }

    const { u, v } = buildNormalizedGrid(points)
    const z = []
    const z2 = []
    let maxAbs = 0
    for (let j = 0; j < v.length; j += 1) {
      const row = []
      const row2 = []
      const vVal = v[j]
      const sinY = Math.sin(ny * Math.PI * vVal)
      for (let i = 0; i < u.length; i += 1) {
        const uVal = u[i]
        const val = Math.sin(nx * Math.PI * uVal) * sinY
        row.push(val)
        const val2 = val * val
        row2.push(val2)
        const abs = Math.abs(val)
        if (abs > maxAbs) maxAbs = abs
      }
      z.push(row)
      z2.push(row2)
    }

    baseSurfaceCache = { nx, ny, points, u, v, z, z2, maxAbs }
    return baseSurfaceCache
  }

  const buildSurfaceData = (lx, ly, nx, ny, points) => {
    const base = buildBaseSurface(nx, ny, points)
    if (axisCache.points !== base.points) {
      axisCache.points = base.points
      axisCache.x.clear()
      axisCache.y.clear()
    }
    const xKey = getAxisKey(lx)
    const yKey = getAxisKey(ly)
    let x = axisCache.x.get(xKey)
    if (!x) {
      x = base.u.map((val) => val * lx)
      axisCache.x.set(xKey, x)
    }
    let y = axisCache.y.get(yKey)
    if (!y) {
      y = base.v.map((val) => val * ly)
      axisCache.y.set(yKey, y)
    }
    const scale = Math.sqrt(4 / (lx * ly))
    const scale2 = scale * scale
    const zPsi = []
    const zPsi2 = []
    for (let j = 0; j < base.z.length; j += 1) {
      const row = base.z[j]
      const row2 = base.z2[j]
      const rowPsi = new Array(row.length)
      const rowPsi2 = new Array(row.length)
      for (let i = 0; i < row.length; i += 1) {
        rowPsi[i] = row[i] * scale
        rowPsi2[i] = row2[i] * scale2
      }
      zPsi.push(rowPsi)
      zPsi2.push(rowPsi2)
    }
    const maxAbs = base.maxAbs * scale
    return { x, y, zPsi, zPsi2, maxAbs }
  }

  const getContainerHeight = (el) => {
    if (!el) return 0
    const rect = el.getBoundingClientRect()
    return Math.max(1, Math.round(rect.height))
  }

  const ENERGY_N_MAX = 5
  const ENERGY_BAR_WIDTH = 0.9
  const buildBarMesh = (bars, width) => {
    const x = []
    const y = []
    const z = []
    const intensity = []
    const i = []
    const j = []
    const k = []
    let index = 0
    const half = width / 2
    bars.forEach((bar) => {
      const x0 = bar.x - half
      const x1 = bar.x + half
      const y0 = bar.y - half
      const y1 = bar.y + half
      const z0 = 0
      const z1 = bar.h
      const verts = [
        [x0, y0, z0],
        [x1, y0, z0],
        [x1, y1, z0],
        [x0, y1, z0],
        [x0, y0, z1],
        [x1, y0, z1],
        [x1, y1, z1],
        [x0, y1, z1]
      ]
      const intensities = [0, 0, 0, 0, 1, 1, 1, 1]
      verts.forEach((v) => {
        x.push(v[0])
        y.push(v[1])
        z.push(v[2])
      })
      intensities.forEach((val) => intensity.push(val))
      const faces = [
        [0, 1, 2], [0, 2, 3], // 底面
        [4, 6, 5], [4, 7, 6], // 顶面
        [0, 4, 5], [0, 5, 1], // 侧面
        [1, 5, 6], [1, 6, 2], // 侧面
        [2, 6, 7], [2, 7, 3], // 侧面
        [3, 7, 4], [3, 4, 0]  // 侧面
      ]
      faces.forEach((f) => {
        i.push(index + f[0])
        j.push(index + f[1])
        k.push(index + f[2])
      })
      index += 8
    })
    return { x, y, z, intensity, i, j, k }
  }

  const buildHoverPoints = (bars) => {
    const x = []
    const y = []
    const z = []
    const text = []
    bars.forEach((bar) => {
      x.push(bar.x)
      y.push(bar.y)
      z.push(bar.h)
      text.push(`E: ${bar.h.toFixed(1)}`)
    })
    return { x, y, z, text }
  }

  const buildBarEdgeLines = (bars, defaultWidth) => {
    const x = []
    const y = []
    const z = []
    bars.forEach((bar) => {
      const width = bar.width ?? defaultWidth
      const half = width / 2
      const x0 = bar.x - half
      const x1 = bar.x + half
      const y0 = bar.y - half
      const y1 = bar.y + half
      const z0 = 0
      const z1 = bar.h
      const verts = [
        [x0, y0, z0],
        [x1, y0, z0],
        [x1, y1, z0],
        [x0, y1, z0],
        [x0, y0, z1],
        [x1, y0, z1],
        [x1, y1, z1],
        [x0, y1, z1]
      ]
      const edges = [
        [0, 1], [1, 2], [2, 3], [3, 0],
        [4, 5], [5, 6], [6, 7], [7, 4],
        [0, 4], [1, 5], [2, 6], [3, 7]
      ]
      edges.forEach(([a, b]) => {
        x.push(verts[a][0], verts[b][0], null)
        y.push(verts[a][1], verts[b][1], null)
        z.push(verts[a][2], verts[b][2], null)
      })
    })
    return { x, y, z }
  }

  const computeEnergy = (nxVal, nyVal, lxVal, lyVal) => {
    const lxSafe = Math.max(lxVal, 1e-6)
    const lySafe = Math.max(lyVal, 1e-6)
    return (nxVal * nxVal) / (lxSafe * lxSafe) + (nyVal * nyVal) / (lySafe * lySafe)
  }


  const viridisStops = [
    [0, [227, 242, 255]],
    [0.25, [186, 220, 255]],
    [0.5, [126, 192, 255]],
    [0.75, [63, 154, 230]],
    [1, [0, 94, 200]]
  ]

  const getViridisColor = (t) => {
    const clamped = Math.min(1, Math.max(0, t))
    let idx = 0
    while (idx < viridisStops.length - 1 && clamped > viridisStops[idx + 1][0]) idx += 1
    const [t0, c0] = viridisStops[idx]
    const [t1, c1] = viridisStops[Math.min(idx + 1, viridisStops.length - 1)]
    const local = t1 === t0 ? 0 : (clamped - t0) / (t1 - t0)
    const r = Math.round(c0[0] + (c1[0] - c0[0]) * local)
    const g = Math.round(c0[1] + (c1[1] - c0[1]) * local)
    const b = Math.round(c0[2] + (c1[2] - c0[2]) * local)
    return `rgb(${r}, ${g}, ${b})`
  }

  const drawEnergyHeatmap = (container, lxVal, lyVal, nxVal, nyVal, hasDegenerate) => {
    if (!container) return
    let canvas = container.querySelector('canvas')
    if (!canvas) {
      canvas = document.createElement('canvas')
    }
    let tooltip = container.querySelector('.heatmap-tooltip')
    if (!tooltip) {
      tooltip = document.createElement('div')
      tooltip.className = 'heatmap-tooltip'
      tooltip.style.position = 'absolute'
      tooltip.style.pointerEvents = 'none'
      tooltip.style.padding = '4px 6px'
      tooltip.style.borderRadius = '4px'
      tooltip.style.background = 'rgba(34, 34, 34, 0.9)'
      tooltip.style.color = '#fff'
      tooltip.style.fontSize = '12px'
      tooltip.style.lineHeight = '1'
      tooltip.style.whiteSpace = 'nowrap'
      tooltip.style.display = 'none'
      tooltip.style.zIndex = '2'
    }
    if (container.firstChild !== canvas || container.childNodes.length < 1) {
      container.innerHTML = ''
      container.appendChild(canvas)
      container.appendChild(tooltip)
    } else if (!container.contains(tooltip)) {
      container.appendChild(tooltip)
    }
    const rect = container.getBoundingClientRect()
    const width = Math.max(1, Math.round(rect.width))
    const height = Math.max(1, Math.round(rect.height))
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    canvas.width = width * dpr
    canvas.height = height * dpr
    canvas.style.width = `${width}px`
    canvas.style.height = `${height}px`
    const ctx = canvas.getContext('2d')
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.clearRect(0, 0, width, height)
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, width, height)

    const margin = { left: 56, right: 70, top: 36, bottom: 48 }
    const availableW = Math.max(1, width - margin.left - margin.right)
    const availableH = Math.max(1, height - margin.top - margin.bottom)
    const squareSize = Math.max(1, Math.min(availableW, availableH))
    const plotW = squareSize
    const plotH = squareSize
    const plotX = margin.left + Math.max(0, (availableW - squareSize) / 2)
    const plotY = margin.top + Math.max(0, (availableH - squareSize) / 2)
    const xVals = Array.from({ length: ENERGY_N_MAX }, (_, i) => i + 1)
    const yVals = Array.from({ length: ENERGY_N_MAX }, (_, i) => i + 1)
    const zMatrix = []
    let maxEnergy = 0
    for (let yIndex = 0; yIndex < yVals.length; yIndex += 1) {
      const nyVal = yVals[yIndex]
      const row = []
      for (let xIndex = 0; xIndex < xVals.length; xIndex += 1) {
        const nxVal = xVals[xIndex]
        const energy = computeEnergy(nxVal, nyVal, lxVal, lyVal)
        if (energy > maxEnergy) maxEnergy = energy
        row.push(energy)
      }
      zMatrix.push(row)
    }
    const maxEnergySafe = Math.max(maxEnergy, 1e-6)
    const cellW = plotW / xVals.length
    const cellH = plotH / yVals.length

    canvas._heatmapState = {
      plotX,
      plotY,
      plotW,
      plotH,
      cellW,
      cellH,
      xVals,
      yVals,
      zMatrix,
      nxVal,
      nyVal,
      hasDegenerate
    }
    if (!canvas._heatmapListeners) {
      canvas._heatmapListeners = true
      const showTooltip = (evt) => {
        const state = canvas._heatmapState
        if (!state) return
        const rect = canvas.getBoundingClientRect()
        const x = evt.clientX - rect.left
        const y = evt.clientY - rect.top
        const inside = x >= state.plotX &&
          x <= state.plotX + state.plotW &&
          y >= state.plotY &&
          y <= state.plotY + state.plotH
        if (!inside) {
          tooltip.style.display = 'none'
          return
        }
        const xIndex = Math.min(
          state.xVals.length - 1,
          Math.max(0, Math.floor((x - state.plotX) / state.cellW))
        )
        const yIndexFromTop = Math.min(
          state.yVals.length - 1,
          Math.max(0, Math.floor((y - state.plotY) / state.cellH))
        )
        const yIndex = state.yVals.length - 1 - yIndexFromTop
        const energy = state.zMatrix[yIndex][xIndex]
        const cellNx = state.xVals[xIndex]
        const cellNy = state.yVals[yIndex]
        const isCurrent = cellNx === state.nxVal && cellNy === state.nyVal
        const isDegenerate = state.hasDegenerate &&
          cellNx === state.nyVal &&
          cellNy === state.nxVal &&
          state.nxVal !== state.nyVal
        if (isCurrent) {
          tooltip.style.background = '#f9d3d2'
          tooltip.style.color = '#1e2a36'
        } else if (isDegenerate) {
          tooltip.style.background = '#fde4c1'
          tooltip.style.color = '#1e2a36'
        } else {
          tooltip.style.background = '#e3f2ff'
          tooltip.style.color = '#1e2a36'
        }
        tooltip.textContent = `E: ${energy.toFixed(1)}`
        tooltip.style.left = `${x + 10}px`
        tooltip.style.top = `${y + 10}px`
        tooltip.style.display = 'block'
      }
      const hideTooltip = () => {
        tooltip.style.display = 'none'
      }
      canvas.addEventListener('mousemove', showTooltip)
      canvas.addEventListener('mouseleave', hideTooltip)
    }

    for (let yIndex = 0; yIndex < yVals.length; yIndex += 1) {
      for (let xIndex = 0; xIndex < xVals.length; xIndex += 1) {
        const val = zMatrix[yIndex][xIndex]
        ctx.fillStyle = getViridisColor(val / maxEnergySafe)
        const x = plotX + xIndex * cellW
        const y = plotY + (yVals.length - 1 - yIndex) * cellH
        ctx.fillRect(x, y, cellW + 1, cellH + 1)
      }
    }

    ctx.strokeStyle = '#444'
    ctx.lineWidth = 1
    ctx.strokeRect(plotX, plotY, plotW, plotH)

    const highlightCell = (hx, hy, color) => {
      if (!hx || !hy) return
      const xIndex = hx - 1
      const yIndex = hy - 1
      if (xIndex < 0 || xIndex >= xVals.length || yIndex < 0 || yIndex >= yVals.length) return
      const x = plotX + xIndex * cellW
      const y = plotY + (yVals.length - 1 - yIndex) * cellH
      const inset = Math.min(2, cellW * 0.1, cellH * 0.1)
      ctx.save()
      ctx.globalAlpha = 0.25
      ctx.fillStyle = color
      ctx.fillRect(x + inset, y + inset, cellW - inset * 2, cellH - inset * 2)
      ctx.restore()
      ctx.save()
      ctx.strokeStyle = color
      ctx.lineWidth = 2
      ctx.strokeRect(x + inset, y + inset, cellW - inset * 2, cellH - inset * 2)
      ctx.restore()
    }

    highlightCell(nxVal, nyVal, '#e53935')
    if (hasDegenerate && nxVal !== nyVal) {
      highlightCell(nyVal, nxVal, '#f39c12')
    }

    ctx.strokeStyle = '#444'
    ctx.lineWidth = 1
    const titleFontSize = getPlotTitleFontSize()
    ctx.fillStyle = '#000000'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'bottom'
    ctx.font = `${titleFontSize}px Arial, sans-serif`
    ctx.fillText('Energy Heatmap (E)', width / 2, Math.max(24, margin.top - 8))

    ctx.textAlign = 'center'
    ctx.textBaseline = 'top'
    ctx.font = '14px Arial, sans-serif'
    xVals.forEach((val, idx) => {
      const x = plotX + idx * cellW + cellW / 2
      ctx.beginPath()
      ctx.moveTo(x, plotY + plotH)
      ctx.lineTo(x, plotY + plotH + 5)
      ctx.stroke()
      ctx.fillText(`${val}`, x, plotY + plotH + 8)
    })

    ctx.textAlign = 'right'
    ctx.textBaseline = 'middle'
    yVals.forEach((val, idx) => {
      const y = plotY + (yVals.length - 1 - idx) * cellH + cellH / 2
      ctx.beginPath()
      ctx.moveTo(plotX - 5, y)
      ctx.lineTo(plotX, y)
      ctx.stroke()
      ctx.fillText(`${val}`, plotX - 10, y)
    })

    ctx.textAlign = 'center'
    ctx.textBaseline = 'top'
    ctx.font = '16px Arial, sans-serif'
    const xAxisLabelOffset = 28
    ctx.fillText('n\u2093', plotX + plotW / 2, plotY + plotH + xAxisLabelOffset)

    ctx.save()
    const yAxisLabelOffset = 40
    ctx.translate(plotX - yAxisLabelOffset, plotY + plotH / 2)
    ctx.rotate(-Math.PI / 2)
    ctx.textAlign = 'center'
    ctx.textBaseline = 'top'
    ctx.font = '16px Arial, sans-serif'
    ctx.fillText('n\u1D67', 0, 0)
    ctx.restore()

    const barX = plotX + plotW + 20
    const barY = plotY
    const barW = 16
    const barH = plotH
    const gradient = ctx.createLinearGradient(0, barY + barH, 0, barY)
    viridisStops.forEach(([stop, color]) => {
      gradient.addColorStop(stop, `rgb(${color[0]}, ${color[1]}, ${color[2]})`)
    })
    ctx.fillStyle = gradient
    ctx.fillRect(barX, barY, barW, barH)
    ctx.strokeStyle = '#444'
    ctx.strokeRect(barX, barY, barW, barH)

    ctx.fillStyle = '#222'
    ctx.textAlign = 'left'
    ctx.textBaseline = 'middle'
    ctx.font = '12px Arial, sans-serif'
    const ticks = 4
    for (let i = 0; i <= ticks; i += 1) {
      const t = i / ticks
      const y = barY + barH - t * barH
      const val = maxEnergySafe * t
      ctx.fillText(val.toFixed(0), barX + barW + 8, y)
    }
  }

  const drawWavefunction2D = () => {
    if (!isActive || !Plotly) return
    const perfStart = performance.now()
    const perf = {
      build: 0,
      psi: 0,
      psi2: 0,
      energy: 0,
      heatmap: 0,
      total: 0
    }
    const psiEl = document.getElementById('psi-3d')
    const psi2El = document.getElementById('psi2-3d')
    const energyEl = document.getElementById('energy-3d')
    const heatmapEl = document.getElementById('energy-heatmap')
    if (!psiEl && !psi2El && !energyEl && !heatmapEl) return

    const lx = L_x.value
    const ly = L_y.value
    const nx = n_x.value
    const ny = n_y.value
    const isNarrowScreen = window.innerWidth <= 1080

    const points = isDragging.value ? NUM_POINTS_LOW : NUM_POINTS_HIGH
    const buildStart = performance.now()
    const { x, y, zPsi, zPsi2, maxAbs: baseMaxAbs } = buildSurfaceData(lx, ly, nx, ny, points)
    perf.build = performance.now() - buildStart
    const maxAbs = baseMaxAbs === 0 ? 1 : baseMaxAbs
    const midAbs = maxAbs / 2
    const maxPsi2 = maxAbs * maxAbs
    const psi2Tick25 = maxPsi2 * 0.25
    const psi2Tick50 = maxPsi2 * 0.5
    const psi2Tick75 = maxPsi2 * 0.75

    const psiHeight = psiEl ? getContainerHeight(psiEl) : 0

    if (psiEl) {
      const t0 = performance.now()
      const psiTrace = {
        type: 'surface',
        x,
        y,
        z: zPsi,
        colorscale: PSI_COLORSCALE,
        cmin: -maxAbs,
        cmax: maxAbs,
        cmid: 0,
        cauto: false,
        reversescale: false,
        colorbar: {
          ...SURFACE_COLORBAR_BASE,
          title: 'Amplitude',
          tickmode: 'array',
          tickvals: [-maxAbs, -midAbs, 0, midAbs, maxAbs],
          tickformat: '.1f'
        },
        showscale: true
      }
      if (!psiInitialized) {
        const psiLayout = buildPsiLayout(psiHeight, lx, ly)
        Plotly.react(psiEl, [psiTrace], psiLayout, BASE_CONFIG)
        psiInitialized = true
        psiHeightCache = psiHeight
      } else {
        Plotly.restyle(psiEl, {
          x: [x],
          y: [y],
          z: [zPsi],
          cmin: [-maxAbs],
          cmax: [maxAbs],
          cmid: [0],
          'colorbar.tickvals': [[-maxAbs, -midAbs, 0, midAbs, maxAbs]]
        }, [0])
        Plotly.relayout(psiEl, {
          title: buildPlotTitle('Wavefunction (ψ)'),
          'scene.xaxis.range': [0, lx],
          'scene.yaxis.range': [0, ly]
        })
        if (psiHeight && Math.abs(psiHeight - psiHeightCache) > 0.5) {
          Plotly.relayout(psiEl, { height: psiHeight })
          psiHeightCache = psiHeight
        }
      }
      perf.psi = performance.now() - t0
    }

    const psi2Height = psi2El ? getContainerHeight(psi2El) : 0

    if (psi2El) {
      const t0 = performance.now()
      const psi2Trace = {
        type: 'surface',
        x,
        y,
        z: zPsi2,
        colorscale: PSI2_COLORSCALE,
        cmin: 0,
        cmax: maxPsi2,
        cauto: false,
        colorbar: {
          ...SURFACE_COLORBAR_BASE,
          tickmode: 'array',
          tickvals: [0, psi2Tick25, psi2Tick50, psi2Tick75, maxPsi2],
          tickformat: '.1f'
        },
        showscale: true
      }
      if (!psi2Initialized) {
        const psi2Layout = buildPsi2Layout(psi2Height, lx, ly)
        Plotly.react(psi2El, [psi2Trace], psi2Layout, BASE_CONFIG)
        psi2Initialized = true
        psi2HeightCache = psi2Height
      } else {
        Plotly.restyle(psi2El, {
          x: [x],
          y: [y],
          z: [zPsi2],
          cmin: [0],
          cmax: [maxPsi2],
          'colorbar.tickvals': [[0, psi2Tick25, psi2Tick50, psi2Tick75, maxPsi2]]
        }, [0])
        Plotly.relayout(psi2El, {
          title: buildPlotTitle('Probability density (ψ²)'),
          'scene.xaxis.range': [0, lx],
          'scene.yaxis.range': [0, ly]
        })
        if (psi2Height && Math.abs(psi2Height - psi2HeightCache) > 0.5) {
          Plotly.relayout(psi2El, { height: psi2Height })
          psi2HeightCache = psi2Height
        }
      }
      perf.psi2 = performance.now() - t0
    }

    if (energyEl) {
      const t0 = performance.now()
      const bars = []
      let maxEnergy = 0
      for (let nxVal = 1; nxVal <= ENERGY_N_MAX; nxVal += 1) {
        for (let nyVal = 1; nyVal <= ENERGY_N_MAX; nyVal += 1) {
          const energy = computeEnergy(nxVal, nyVal, lx, ly)
          if (energy > maxEnergy) maxEnergy = energy
          bars.push({ x: nxVal, y: nyVal, h: energy, width: ENERGY_BAR_WIDTH })
        }
      }
      const highlightBar = bars.find((bar) => bar.x === nx && bar.y === ny)
      const highlightBarScaled = highlightBar
        ? { ...highlightBar, width: ENERGY_BAR_WIDTH }
        : null
      const hasDegenerate = hasDegeneracy.value
      const degenerateBar = hasDegenerate
        ? bars.find((bar) => bar.x === ny && bar.y === nx)
        : null
      const degenerateBarScaled = degenerateBar
        ? { ...degenerateBar, width: ENERGY_BAR_WIDTH }
        : null
      const baseBars = bars.filter((bar) => bar !== highlightBar && bar !== degenerateBar)
      const plotData = []

      if (baseBars.length) {
        const baseMesh = buildBarMesh(baseBars, ENERGY_BAR_WIDTH)
        plotData.push({
          type: 'mesh3d',
          ...baseMesh,
          opacity: 1,
          intensity: baseMesh.intensity,
          colorscale: [
            [0, '#ffffff'],
            [1, '#4f9bd1']
          ],
          cmin: 0,
          cmax: 1,
          autocolorscale: false,
          intensitymode: 'vertex',
          showscale: false,
          flatshading: true,
          showlegend: false,
          hoverinfo: 'skip',
          hovertemplate: ''
        })
        const baseHover = buildHoverPoints(baseBars)
        plotData.push({
          type: 'scatter3d',
          mode: 'markers',
          x: baseHover.x,
          y: baseHover.y,
          z: baseHover.z,
          text: baseHover.text,
          hoverinfo: 'text',
          marker: { size: 12, color: 'rgba(0,0,0,0.01)' },
          hoverlabel: {
            bgcolor: '#dbeffd',
            bordercolor: '#4f9bd1',
            font: { color: '#1e2a36' }
          },
          showlegend: false
        })
      }

      if (highlightBar) {
        const highlightMesh = buildBarMesh([highlightBarScaled], highlightBarScaled.width)
        plotData.push({
          type: 'mesh3d',
          ...highlightMesh,
          opacity: 1,
          intensity: highlightMesh.intensity,
          colorscale: [
            [0, '#ffffff'],
            [1, '#e53935']
          ],
          cmin: 0,
          cmax: 1,
          autocolorscale: false,
          intensitymode: 'vertex',
          showscale: false,
          flatshading: true,
          showlegend: false,
          hoverinfo: 'skip',
          hovertemplate: ''
        })
        plotData.push({
          type: 'scatter3d',
          mode: 'markers',
          x: [ENERGY_N_MAX + 2],
          y: [ENERGY_N_MAX + 2],
          z: [0],
          marker: {
            size: 9,
            color: '#e53935',
            symbol: 'square',
            line: { color: '#1a1a1a', width: 1 }
          },
          name: 'Current<br>Orbital',
          showlegend: !isNarrowScreen,
          hoverinfo: 'skip'
        })
        const highlightHover = buildHoverPoints([highlightBarScaled])
        plotData.push({
          type: 'scatter3d',
          mode: 'markers',
          x: highlightHover.x,
          y: highlightHover.y,
          z: highlightHover.z,
          text: highlightHover.text,
          hoverinfo: 'text',
          marker: { size: 16, color: 'rgba(0,0,0,0.01)' },
          hoverlabel: {
            bgcolor: '#f9d3d2',
            bordercolor: '#e53935',
            font: { color: '#1e2a36' }
          },
          showlegend: false
        })
      }

      if (degenerateBarScaled) {
        const degenerateMesh = buildBarMesh([degenerateBarScaled], degenerateBarScaled.width)
        plotData.push({
          type: 'mesh3d',
          ...degenerateMesh,
          opacity: 1,
          intensity: degenerateMesh.intensity,
          colorscale: [
            [0, '#ffffff'],
            [1, '#f39c12']
          ],
          cmin: 0,
          cmax: 1,
          autocolorscale: false,
          intensitymode: 'vertex',
          showscale: false,
          flatshading: true,
          showlegend: false,
          hoverinfo: 'skip',
          hovertemplate: ''
        })
        const degenerateHover = buildHoverPoints([degenerateBarScaled])
        plotData.push({
          type: 'scatter3d',
          mode: 'markers',
          x: degenerateHover.x,
          y: degenerateHover.y,
          z: degenerateHover.z,
          text: degenerateHover.text,
          hoverinfo: 'text',
          marker: { size: 12, color: 'rgba(0,0,0,0.01)' },
          hoverlabel: {
            bgcolor: '#fde4c1',
            bordercolor: '#f39c12',
            font: { color: '#1e2a36' }
          },
          showlegend: false
        })
      }

      const degenerateLegendOpacity = hasDegenerate ? 1 : 0.35
      plotData.push({
        type: 'scatter3d',
        mode: 'markers',
        x: [ENERGY_N_MAX + 3],
        y: [ENERGY_N_MAX + 3],
        z: [0],
        marker: {
          size: 9,
          color: `rgba(243,156,18,${degenerateLegendOpacity})`,
          symbol: 'square',
          line: { color: `rgba(26,26,26,${degenerateLegendOpacity})`, width: 1 }
        },
        name: 'Degenerate<br>Orbital',
        showlegend: !isNarrowScreen,
        hoverinfo: 'skip'
      })

      const edgeBars = bars
      const edgeLines = buildBarEdgeLines(edgeBars, ENERGY_BAR_WIDTH)
      plotData.push({
        type: 'scatter3d',
        mode: 'lines',
        x: edgeLines.x,
        y: edgeLines.y,
        z: edgeLines.z,
        line: { color: '#2a2a2a', width: 2 },
        hoverinfo: 'skip',
        hovertemplate: '',
        showlegend: false
      })

      const energyLayout = {
        autosize: true,
        uirevision: 'energy-2d',
        title: buildPlotTitle('Energy Levels (E)'),
        showlegend: !isNarrowScreen,
        legend: !isNarrowScreen ? {
          font: { size: 16 },
          itemclick: false,
          itemdoubleclick: false
        } : undefined,
        hovermode: 'closest',
        scene: {
          domain: { x: [0, 1], y: [0, 1] },
          xaxis: {
            title: { text: 'n<sub>x</sub>' },
            tickmode: 'array',
            tickvals: Array.from({ length: ENERGY_N_MAX }, (_, i) => i + 1),
            ticktext: Array.from({ length: ENERGY_N_MAX }, (_, i) => `${i + 1}`),
            dtick: 1,
            range: [0.5, ENERGY_N_MAX + 0.5]
          },
          yaxis: {
            title: { text: 'n<sub>y</sub>' },
            tickmode: 'array',
            tickvals: Array.from({ length: ENERGY_N_MAX }, (_, i) => i + 1),
            ticktext: Array.from({ length: ENERGY_N_MAX }, (_, i) => `${i + 1}`),
            dtick: 1,
            range: [0.5, ENERGY_N_MAX + 0.5]
          },
          zaxis: {
            title: { text: 'E' },
            range: [0, Math.max(maxEnergy * 1.1, 1)],
            autorange: false
          },
          aspectratio: { x: 1, y: 1, z: 0.7 },
          camera: {
            eye: { x: -1.2, y: -1.2, z: 0.7 },
            center: { x: 0, y: 0, z: -0.2 }
          }
        },
        margin: { l: 10, r: 10, t: 40, b: 10 },
        height: psiHeight || getContainerHeight(energyEl)
      }

      Plotly.react(energyEl, plotData, energyLayout, BASE_CONFIG)
      perf.energy = performance.now() - t0
    }
    if (heatmapEl) {
      const t0 = performance.now()
      drawEnergyHeatmap(heatmapEl, lx, ly, nx, ny, hasDegeneracy.value)
      perf.heatmap = performance.now() - t0
    }

    perf.total = performance.now() - perfStart
    perfStats.value = perf
  }
  let rafId = 0
  const scheduleDraw = () => {
    if (rafId) return
    rafId = window.requestAnimationFrame(() => {
      rafId = 0
      drawWavefunction2D()
    })
  }
  const debouncedDraw = debounce(scheduleDraw, 50)
  let resizeObserver = null
  const observePlotSize = () => {
    if (typeof ResizeObserver === 'undefined') return
    const targets = [
      document.getElementById('psi-3d'),
      document.getElementById('psi2-3d'),
      document.getElementById('energy-3d'),
      document.getElementById('energy-heatmap'),
      document.querySelector('.layout-content')
    ].filter(Boolean)
    if (!targets.length) return
    resizeObserver = new ResizeObserver(() => {
      window.requestAnimationFrame(() => {
        window.requestAnimationFrame(() => {
          const plotTargets = [
            document.getElementById('psi-3d'),
            document.getElementById('psi2-3d'),
            document.getElementById('energy-3d')
          ]
          plotTargets.forEach((el) => {
            if (!Plotly || !el || !el._fullLayout) return
            const rect = el.getBoundingClientRect()
            const width = Math.max(1, Math.round(rect.width))
            const height = Math.max(1, Math.round(rect.height))
            Plotly.relayout(el, { width, height })
            Plotly.Plots.resize(el)
          })
          psiHeightCache = 0
          psi2HeightCache = 0
          debouncedDraw()
        })
      })
    })
    targets.forEach((el) => resizeObserver.observe(el))
  }

  watch([n_x, n_y], () => {
    if (isDragging.value) return
    scheduleDraw()
  })

  watch([L_x, L_y], () => {
    if (isDragging.value) return
    scheduleDraw()
  })

  watch([L_x, lockLxLy], ([lx, locked]) => {
    if (!locked) return
    if (Math.abs(L_y.value - lx) < 1e-6) return
    L_y.value = lx
  })

  onMounted(async () => {
    isActive = true
    startFpsMonitor()
    await ensurePlotly()
    if (!isActive) return
    scheduleDraw()
    observePlotSize()
  })

  onBeforeUnmount(() => {
    isActive = false
    const psiEl = document.getElementById('psi-3d')
    const psi2El = document.getElementById('psi2-3d')
    const energyEl = document.getElementById('energy-3d')
    if (Plotly && psiEl) Plotly.purge(psiEl)
    if (Plotly && psi2El) Plotly.purge(psi2El)
    if (Plotly && energyEl) Plotly.purge(energyEl)
  })

  onUnmounted(() => {
    if (resizeObserver) {
      resizeObserver.disconnect()
      resizeObserver = null
    }
    if (fpsRaf) {
      window.cancelAnimationFrame(fpsRaf)
      fpsRaf = 0
    }
    if (rafId) {
      window.cancelAnimationFrame(rafId)
      rafId = 0
    }
  })
</script>

<style scoped>
  @import './style.css';
</style>
