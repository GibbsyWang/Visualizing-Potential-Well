<template>
  <!-- 3D 页面：左侧参数面板，右侧显示波函数与概率密度点云。 -->
  <AppLayout>
    <template #sidebar>
      <div class="sidebar">
        <div class="formulas">
          <h3 class="formulas-title">Formulas</h3>
          <div class="formulas-item">
            <KatexRenderer :expression="waveFunction3DExpression" :displayMode="true" />
          </div>
          <div class="formulas-item">
            <KatexRenderer :expression="energy3DExpression" :displayMode="true" />
          </div>
        </div>

        <div class="parameters">
          <h3 class="parameters-title">Set parameters</h3>

          <div class="parameters-item">
            <div class="parameters-item-label">
              <label for="quantum-number-x">Quantum number x (n<sub>x</sub>):</label>
              <div class="parameters-item-value">{{ n_x }}</div>
            </div>
            <Slider v-model:value="n_x" :min="1" :max="5" :marks="marks" :step="1" @change="handleChangePlotNX" @afterChange="handleAfterChange">
            </Slider>
          </div>

          <div class="parameters-item">
            <div class="parameters-item-label">
              <label for="quantum-number-y">Quantum number y (n<sub>y</sub>):</label>
              <div class="parameters-item-value">{{ n_y }}</div>
            </div>
            <Slider v-model:value="n_y" :min="1" :max="5" :marks="marks" :step="1" @change="handleChangePlotNY" @afterChange="handleAfterChange">
            </Slider>
          </div>

          <div class="parameters-item">
            <div class="parameters-item-label">
              <label for="quantum-number-z">Quantum number z (n<sub>z</sub>):</label>
              <div class="parameters-item-value">{{ n_z }}</div>
            </div>
            <Slider v-model:value="n_z" :min="1" :max="5" :marks="marks" :step="1" @change="handleChangePlotNZ" @afterChange="handleAfterChange">
            </Slider>
          </div>

          <div class="parameters-item">
            <div class="parameters-item-label">
              <label for="length-x">Length x (L<sub>x</sub>):</label>
              <div class="parameters-item-value">{{ L_x.toFixed(2) }}</div>
            </div>
            <Slider v-model:value="L_x" :min="1.0" :max="5.0" :marks="marksL" :step="0.05" @change="handleChangePlotLX" @afterChange="handleAfterChange">
            </Slider>
          </div>

          <div class="parameters-item">
            <div class="parameters-item-label">
              <label for="length-y">Length y (L<sub>y</sub>):</label>
              <div class="parameters-item-value">{{ L_y.toFixed(2) }}</div>
            </div>
            <Slider v-model:value="L_y" :min="1.0" :max="5.0" :marks="marksL" :step="0.05" @change="handleChangePlotLY" @afterChange="handleAfterChange">
            </Slider>
          </div>

          <div class="parameters-item">
            <div class="parameters-item-label">
              <label for="length-z">Length z (L<sub>z</sub>):</label>
              <div class="parameters-item-value">{{ L_z.toFixed(2) }}</div>
            </div>
            <Slider v-model:value="L_z" :min="1.0" :max="5.0" :marks="marksL" :step="0.05" @change="handleChangePlotLZ" @afterChange="handleAfterChange">
            </Slider>
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
                <span>Total</span>
                <span class="performance-value">{{ perfStats.total.toFixed(2) }} ms</span>
              </div>
            </div>
            <BackToHomeButton />
          </div>
        </div>
      </div>
    </template>

    <template #content>
      <div class="plot-container">
        <h1 class="plot-container-title"><span class="plot-mark">3D</span> Infinite Square Well
        </h1>

        <div class="plot-row">
          <div class="plot-col">
            <div id="wavefunction-volume" class="plot-box"></div>
          </div>
          <div class="plot-col">
            <div id="probability-density-volume" class="plot-box"></div>
          </div>
        </div>
      </div>
    </template>
  </AppLayout>
</template>
<script setup>
  // 依赖导入：包含响应式状态、数学工具与通用组件。
  import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
  import AppLayout from '@/components/layout/AppLayout.vue'
  import BackToHomeButton from '@/components/backToHome/BackToHomeButton.vue'
  import KatexRenderer from '@/components/katex/KatexRenderer.vue'
  import { Slider } from 'ant-design-vue'
  import { marks, marksL } from './constants'
  import { debounce } from '@/utils/debounce'
  import { loadPlotly } from '@/utils/loadPlotly'

  // 响应式状态：量子数、边长、拖拽状态与性能指标。
  const n_x = ref(1)
  const n_y = ref(1)
  const n_z = ref(1)
  const L_x = ref(1.0)
  const L_y = ref(1.0)
  const L_z = ref(1.0)
  const isDragging = ref(false)
  const fps = ref(0)
  const perfStats = ref({
    build: 0,
    psi: 0,
    psi2: 0,
    total: 0
  })
  // 绘制策略：拖动时合并同一帧内的更新，避免重复渲染。
  const NUM_POINTS_HIGH = 18
  const WAVE_PLOT_TITLE = 'Wavefunction Point Cloud (ψ)'
  const DENSITY_PLOT_TITLE = 'Probability Density Point Cloud (ψ²)'

  const updateQuantumNumber = (target, val) => {
    isDragging.value = true
    target.value = val
    scheduleDraw()
  }
  const updateLength = (target, val) => {
    isDragging.value = true
    target.value = val
    scheduleDraw()
  }
  const handleChangePlotNX = (val) => updateQuantumNumber(n_x, val)
  const handleChangePlotNY = (val) => updateQuantumNumber(n_y, val)
  const handleChangePlotNZ = (val) => updateQuantumNumber(n_z, val)
  const handleChangePlotLX = (val) => updateLength(L_x, val)
  const handleChangePlotLY = (val) => updateLength(L_y, val)
  const handleChangePlotLZ = (val) => updateLength(L_z, val)
  const handleAfterChange = () => {
    if (!isDragging.value) return
    isDragging.value = false
    scheduleDraw()
  }

  // 公式展示：KaTeX 使用计算属性以便随参数实时更新。
  const waveFunction3DExpression = computed(() => `\\psi_{n_x,n_y,n_z}(x, y, z) = \\sqrt{\\frac{8}{L_x L_y L_z}} \\sin(\\frac{n_x \\pi x}{L_x}) \\sin(\\frac{n_y \\pi y}{L_y}) \\sin(\\frac{n_z \\pi z}{L_z})`)
  const energy3DExpression = computed(() => `E_{n_x,n_y,n_z} = \\frac{\\pi^2 \\hbar^2}{2m_e} \\left(\\frac{n_x^2}{L_x^2} + \\frac{n_y^2}{L_y^2} + \\frac{n_z^2}{L_z^2}\\right)`)

  // 绘图配色与默认相机配置。
  const PSI_COLORSCALE = [
    [0, '#0000ff'],
    [0.5, '#ffffff'],
    [1, '#ff0000']
  ]
  const PSI2_COLORSCALE = 'Viridis'
  const SURFACE_COLORBAR_BASE = {
    thickness: 16,
    thicknessmode: 'pixels',
    len: 0.82,
    lenmode: 'fraction',
    xpad: 6
  }
  const DEFAULT_CAMERA = {
    eye: { x: 1.35, y: 1.35, z: 1.1 },
    center: { x: 0, y: 0, z: 0 },
    up: { x: 0, y: 0, z: 1 }
  }
  let isActive = false
  let fpsRaf = 0
  let fpsFrames = 0
  let fpsLast = 0
  let Plotly = null
  // 标题字体随内容区宽度变化，避免窄屏时标题挤压。
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
    font: {
      size: getPlotTitleFontSize(),
      color: '#000000'
    }
  })
  const PSI_VISIBILITY_THRESHOLD = 0.1
  const PSI2_VISIBILITY_THRESHOLD = 0.01
  // 点云缓存：同一组量子数下复用归一化网格计算结果。
  let basePointCloudCache = {
    nx: null,
    ny: null,
    nz: null,
    points: null,
    xNorm: [],
    yNorm: [],
    zNorm: [],
    value: [],
    valueSquared: [],
    maxAbs: 0,
    waveVisibleIndices: [],
    waveVisibleStrengths: [],
    densityVisibleIndices: [],
    densityVisibleStrengths: []
  }
  const buildBasePointCloud = (nx, ny, nz, points) => {
    if (
      basePointCloudCache.nx === nx &&
      basePointCloudCache.ny === ny &&
      basePointCloudCache.nz === nz &&
      basePointCloudCache.points === points
    ) {
      return basePointCloudCache
    }

    const xNorm = []
    const yNorm = []
    const zNorm = []
    const value = []
    const valueSquared = []
    const step = 1 / (points - 1)
    let maxAbs = 0

    for (let i = 0; i < points; i += 1) {
      const u = i * step
      const sinX = Math.sin(nx * Math.PI * u)
      for (let j = 0; j < points; j += 1) {
        const v = j * step
        const sinY = Math.sin(ny * Math.PI * v)
        for (let k = 0; k < points; k += 1) {
          const w = k * step
          const baseValue = sinX * sinY * Math.sin(nz * Math.PI * w)
          xNorm.push(u)
          yNorm.push(v)
          zNorm.push(w)
          value.push(baseValue)
          valueSquared.push(baseValue * baseValue)
          const absValue = Math.abs(baseValue)
          if (absValue > maxAbs) maxAbs = absValue
        }
      }
    }

    const waveVisibleIndices = []
    const waveVisibleStrengths = []
    const densityVisibleIndices = []
    const densityVisibleStrengths = []
    const safeMaxAbs = Math.max(maxAbs, 1e-6)
    for (let index = 0; index < value.length; index += 1) {
      const normalizedAbs = Math.abs(value[index]) / safeMaxAbs
      if (normalizedAbs > PSI_VISIBILITY_THRESHOLD) {
        waveVisibleIndices.push(index)
        waveVisibleStrengths.push((normalizedAbs - PSI_VISIBILITY_THRESHOLD) / (1 - PSI_VISIBILITY_THRESHOLD))
      }
      const normalizedDensity = valueSquared[index] / (safeMaxAbs * safeMaxAbs)
      if (normalizedDensity > PSI2_VISIBILITY_THRESHOLD) {
        densityVisibleIndices.push(index)
        densityVisibleStrengths.push((normalizedDensity - PSI2_VISIBILITY_THRESHOLD) / (1 - PSI2_VISIBILITY_THRESHOLD))
      }
    }

    basePointCloudCache = {
      nx,
      ny,
      nz,
      points,
      xNorm,
      yNorm,
      zNorm,
      value,
      valueSquared,
      maxAbs: safeMaxAbs,
      waveVisibleIndices,
      waveVisibleStrengths,
      densityVisibleIndices,
      densityVisibleStrengths
    }
    return basePointCloudCache
  }
  const buildPointCloudData = (nx, ny, nz, points, lx, ly, lz) => {
    const base = buildBasePointCloud(nx, ny, nz, points)
    const amplitude = Math.sqrt(8 / (lx * ly * lz))
    const amplitude2 = amplitude * amplitude
    const value = base.value.map((v) => v * amplitude)
    const density = base.valueSquared.map((v2) => v2 * amplitude2)
    const maxAbs = base.maxAbs * amplitude
    return {
      base,
      x: base.xNorm,
      y: base.yNorm,
      z: base.zNorm,
      value,
      density,
      maxAbs,
      maxDensity: maxAbs * maxAbs
    }
  }
  // 将通过阈值筛选的点展开为 Plotly 所需数组。
  const buildVisiblePointCloud = (indices, strengths, x, y, z, values, minMarkerSize, maxMarkerSize) => {
    const visibleX = []
    const visibleY = []
    const visibleZ = []
    const visibleValue = []
    const pointSizes = []
    for (let i = 0; i < indices.length; i += 1) {
      const index = indices[i]
      visibleX.push(x[index])
      visibleY.push(y[index])
      visibleZ.push(z[index])
      visibleValue.push(values[index])
      pointSizes.push(minMarkerSize + strengths[i] * (maxMarkerSize - minMarkerSize))
    }
    return { visibleX, visibleY, visibleZ, visibleValue, pointSizes }
  }
  const createColorbarTrace = (cmin, cmax, colorscale, title, tickvals) => ({
    type: 'scatter3d',
    mode: 'markers',
    x: [0, 0],
    y: [0, 0],
    z: [0, 0],
    hoverinfo: 'skip',
    marker: {
      size: 0.01,
      opacity: 0,
      color: [cmin, cmax],
      colorscale,
      cmin,
      cmax,
      showscale: true,
      colorbar: {
        ...SURFACE_COLORBAR_BASE,
        title,
        tickmode: 'array',
        tickvals,
        tickformat: '.2f'
      }
    },
    showlegend: false
  })
  const createNormalizedAxis = (title, length) => {
    const integerTicks = []
    const maxInteger = Math.floor(length + 1e-9)
    for (let tick = 0; tick <= maxInteger; tick += 1) {
      integerTicks.push(tick)
    }
    return {
      title,
      range: [0, 1],
      autorange: false,
      tickmode: 'array',
      tickvals: integerTicks.map((tick) => tick / Math.max(length, 1e-6)),
      ticktext: integerTicks.map((tick) => `${tick}`)
    }
  }
  const createPointCloudLayout = (title, camera) => ({
    autosize: true,
    uirevision: title,
    title: buildPlotTitle(title),
    scene: {
      camera,
      xaxis: createNormalizedAxis('x', L_x.value),
      yaxis: createNormalizedAxis('y', L_y.value),
      zaxis: createNormalizedAxis('z', L_z.value),
      aspectmode: 'cube'
    },
    margin: { l: 10, r: 10, b: 10, t: 40 }
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

  // 主绘制流程：渲染波函数与概率密度点云。
  const drawWavefunctionPointCloud = () => {
    if (!isActive || !Plotly) return
    const perfStart = performance.now()
    const perf = {
      build: 0,
      psi: 0,
      psi2: 0,
      total: 0
    }
    const waveTarget = document.getElementById('wavefunction-volume')
    const densityTarget = document.getElementById('probability-density-volume')
    if (!waveTarget && !densityTarget) return
    const waveCamera = waveTarget?._fullLayout?.scene?.camera || DEFAULT_CAMERA
    const densityCamera = densityTarget?._fullLayout?.scene?.camera || DEFAULT_CAMERA

    const buildStart = performance.now()
    const numPoints = NUM_POINTS_HIGH
    const { base, x, y, z, value, density, maxAbs, maxDensity } = buildPointCloudData(
      n_x.value,
      n_y.value,
      n_z.value,
      numPoints,
      L_x.value,
      L_y.value,
      L_z.value
    )
    perf.build = performance.now() - buildStart

    const midAbs = maxAbs / 2
    const isNarrowScreen = window.innerWidth <= 1080
    const minMarkerSize = isNarrowScreen ? 2 : 3
    const maxMarkerSize = isNarrowScreen ? 5 : 7.5
    const waveVisible = buildVisiblePointCloud(
      base.waveVisibleIndices,
      base.waveVisibleStrengths,
      x,
      y,
      z,
      value,
      minMarkerSize,
      maxMarkerSize
    )
    const densityVisible = buildVisiblePointCloud(
      base.densityVisibleIndices,
      base.densityVisibleStrengths,
      x,
      y,
      z,
      density,
      minMarkerSize,
      maxMarkerSize
    )

    if (waveTarget) {
      const t0 = performance.now()
      const waveTrace = {
        type: 'scatter3d',
        mode: 'markers',
        x: waveVisible.visibleX,
        y: waveVisible.visibleY,
        z: waveVisible.visibleZ,
        customdata: waveVisible.visibleValue,
        hovertemplate: 'x: %{x:.2f}<br>y: %{y:.2f}<br>z: %{z:.2f}<br>ψ: %{customdata:.3f}<extra></extra>',
        marker: {
          size: waveVisible.pointSizes,
          color: waveVisible.visibleValue,
          colorscale: PSI_COLORSCALE,
          cmin: -maxAbs,
          cmax: maxAbs,
          opacity: 1,
          line: { width: 0 },
          showscale: false
        },
        showlegend: false
      }
      const waveColorbarTrace = createColorbarTrace(-maxAbs, maxAbs, PSI_COLORSCALE, 'Amplitude', [-maxAbs, -midAbs, 0, midAbs, maxAbs])
      Plotly.react(
        waveTarget,
        [waveTrace, waveColorbarTrace],
        createPointCloudLayout(WAVE_PLOT_TITLE, waveCamera),
        { responsive: true, displaylogo: false }
      )
      perf.psi = performance.now() - t0
    }

    if (densityTarget) {
      const t0 = performance.now()
      const densityTrace = {
        type: 'scatter3d',
        mode: 'markers',
        x: densityVisible.visibleX,
        y: densityVisible.visibleY,
        z: densityVisible.visibleZ,
        customdata: densityVisible.visibleValue,
        hovertemplate: 'x: %{x:.2f}<br>y: %{y:.2f}<br>z: %{z:.2f}<br>ψ²: %{customdata:.3f}<extra></extra>',
        marker: {
          size: densityVisible.pointSizes,
          color: densityVisible.visibleValue,
          colorscale: PSI2_COLORSCALE,
          cmin: 0,
          cmax: maxDensity,
          opacity: 1,
          line: { width: 0 },
          showscale: false
        },
        showlegend: false
      }
      const densityColorbarTrace = createColorbarTrace(0, maxDensity, PSI2_COLORSCALE, 'Probability density', [0, maxDensity * 0.25, maxDensity * 0.5, maxDensity * 0.75, maxDensity])
      Plotly.react(
        densityTarget,
        [densityTrace, densityColorbarTrace],
        createPointCloudLayout(DENSITY_PLOT_TITLE, densityCamera),
        { responsive: true, displaylogo: false }
      )
      perf.psi2 = performance.now() - t0
    }

    perf.total = performance.now() - perfStart
    perfStats.value = perf
  }

  let rafId = 0
  // 帧调度：合并同一帧内的多次更新请求，减少重复渲染。
  const scheduleDraw = () => {
    if (rafId) return
    rafId = window.requestAnimationFrame(() => {
      rafId = 0
      drawWavefunctionPointCloud()
    })
  }

  const handleResize = debounce(() => {
    scheduleDraw()
  }, 50)

  const scheduleDrawDebounced = debounce(() => {
    if (!isDragging.value) {
      scheduleDraw()
    }
  }, 120)

  watch([n_x, n_y, n_z], () => {
    scheduleDrawDebounced()
  })

  watch([L_x, L_y, L_z], () => {
    scheduleDrawDebounced()
  })

  // 生命周期：挂载时初始化 Plotly，卸载时清理事件与实例。
  onMounted(async () => {
    isActive = true
    startFpsMonitor()
    await ensurePlotly()
    if (!isActive) return
    scheduleDraw()
    window.addEventListener('resize', handleResize)
  })

  onUnmounted(() => {
    isActive = false
    window.removeEventListener('resize', handleResize)
    if (rafId) {
      window.cancelAnimationFrame(rafId)
      rafId = 0
    }
    if (fpsRaf) {
      window.cancelAnimationFrame(fpsRaf)
      fpsRaf = 0
    }
    const waveTarget = document.getElementById('wavefunction-volume')
    if (Plotly && waveTarget) Plotly.purge(waveTarget)
    const densityTarget = document.getElementById('probability-density-volume')
    if (Plotly && densityTarget) Plotly.purge(densityTarget)
  })
</script>
<style scoped>
  @import './style.css';
</style>

