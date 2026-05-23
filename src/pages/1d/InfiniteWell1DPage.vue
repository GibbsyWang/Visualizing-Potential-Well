<template>
  <!-- 1D 椤甸潰锛氬乏渚у弬鏁伴潰鏉匡紝鍙充晶浣跨敤 Canvas 缁樺埗涓変釜鑱斿姩鍥俱€?-->
  <AppLayout>
    <template #sidebar>
      <div class="sidebar">
        <div class="formulas">
          <h3 class="formulas-title">Formulas</h3>
          <div class="formulas-item">
            <KatexRenderer :expression="waveFunctionExpression" :displayMode="true" />
          </div>
          <div class="formulas-item">
            <KatexRenderer :expression="energyExpression" :displayMode="true" />
          </div>
        </div>

        <div class="parameters">
          <h3 class="parameters-title">Set parameters</h3>

          <div v-if="!isInfiniteL" class="parameter-item">
            <div class="parameter-item-label"> <label for="quantum-number">Quantum Number (n):</label>
              <div class="parameter-item-value">{{ n }}</div>
            </div>
            <Slider v-model:value="n" :min="1" :max="7" :marks="marks" :step="1">
            </Slider>
          </div>

          <div v-if="isInfiniteL" class="parameter-item">
            <div class="parameter-item-label">
              <label for="amplitude-a">A:</label>
              <div class="parameter-item-value">{{ A.toFixed(2) }}</div>
            </div>
            <Slider v-model:value="A" :min="-1.0" :max="1.0" :step="0.05" :marks="marksAB" />
          </div>

          <div v-if="isInfiniteL" class="parameter-item">
            <div class="parameter-item-label">
              <label for="amplitude-b">B:</label>
              <div class="parameter-item-value">{{ B.toFixed(2) }}</div>
            </div>
            <Slider v-model:value="B" :min="-1.0" :max="1.0" :step="0.05" :marks="marksAB" />
          </div>

          <div v-if="isInfiniteL" class="parameter-item">
            <div class="parameter-item-label">
              <label for="wave-number">Wave Number (k):</label>
              <div class="parameter-item-value">{{ k.toFixed(2) }}</div>
            </div>
            <Slider v-model:value="k" :min="-3.0" :max="3.0" :step="0.05" :marks="marksK" />
          </div>

          <div class="parameter-item">
            <div class="parameter-item-label"> <label for="length">Length (L):</label>
            <div class="parameter-item-value">{{ displayLValue }}</div>
            </div>
            <Slider v-model:value="L" :min="1.0" :max="5.0" :marks="marksL" :step="0.05" :disabled="isInfiniteL" @change="handleChangePlotL">
              </Slider>
          </div>

          <div class="parameter-item parameter-item--compact">
            <div class="mode-toggle">
              <span class="mode-toggle-label" :class="{ 'mode-toggle-label--active': !isInfiniteL }">Finite L</span>
              <Switch v-model:checked="isInfiniteL" size="small" />
              <span class="mode-toggle-label" :class="{ 'mode-toggle-label--active': isInfiniteL }">Infinite L</span>
            </div>
          </div>
        </div>

        <div class="operator">
          <div class="operator-item">
            <div class="performance">
              <div class="performance-metric">
                <span>FPS</span>
                <span class="performance-value">{{ fps }}</span>
              </div>
            </div>
            <BackToHomeButton />
          </div>
          <div class="operator-item">
            <AppButton @click="handleSaveImages">save image</AppButton>
          </div>
        </div>
      </div>
    </template>

    <template #content>
      <div class="plot-container">
        <h1 class="plot-container-title"><span class="plot-mark">1D</span> {{ pageTitle }}
        </h1>
        <div id="infinite-well-1d" class="plot-stage"></div>
      </div>
    </template>
  </AppLayout>
</template>

<script setup>
  import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
  import AppLayout from '@/components/layout/AppLayout.vue'
  import BackToHomeButton from '@/components/backToHome/BackToHomeButton.vue'
  import AppButton from '@/components/btn/AppButton.vue'
  import { Slider, Switch } from 'ant-design-vue'
  import { marks, marksL } from './constants'
  import KatexRenderer from '@/components/katex/KatexRenderer.vue'
  import html2canvas from 'html2canvas'
  import { debounce } from "@/utils/debounce"

  const L_MIN = 1.0
  const L_MAX = 5.0
  const L_STEP = 0.05
  const PLOT_ASPECT_RATIO = 3 / 2
  const FREE_X_MIN = -5
  const FREE_X_MAX = 5
  const FREE_X_STEP = 0.05
  const K_MIN = -3
  const K_MAX = 3
  const normalizeL = (val) => Number((Math.round(val / L_STEP) * L_STEP).toFixed(2))
  const getLKey = (val) => Number(val).toFixed(2)
  const marksAB = {
    '-1': '-1.0',
    '1': '1.0'
  }
  const marksK = {
    '-3': '-3.0',
    '3': '3.0'
  }

  const n = ref(1)
  const L = ref(1.0)
  const lastFiniteL = ref(1.0)
  const isInfiniteL = ref(false)
  const A = ref(1.0)
  const B = ref(0.0)
  const k = ref(2.0)
  const fps = ref(0)
  const displayLValue = computed(() => (isInfiniteL.value ? '\u221E' : L.value.toFixed(2)))
  const pageTitle = computed(() => (isInfiniteL.value ? 'Free Particle' : 'Infinite Square Well'))
  const waveFunctionExpression = computed(() => (
    isInfiniteL.value
      ? `\\psi(x) = A \\cos(kx) + B \\sin(kx)`
      : `\\psi_n(x) = \\sqrt{\\frac{2}{L}} \\sin(\\frac{n \\pi x}{L})`
  ))
  const energyExpression = computed(() => (
    isInfiniteL.value
      ? `E = \\frac{\\hbar^2 k^2}{2m_e}`
      : `E_n = \\frac{n^2 \\pi^2 \\hbar^2}{2 m_e L^2}`
  ))

  let fpsRaf = 0
  let fpsFrames = 0
  let fpsLast = 0
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

  const handleChangePlotL = (val) => {
    L.value = normalizeL(val)
  }

  const colors = ['#311b92', '#283593', '#1976d2', '#039be5', '#00bcd4', '#26a69a', '#81c784']

  let data1D = null
  let energyTraces = []
  let plot1StaticReady = false
  let plot1StaticSize = { width: 0, height: 0 }
  let plot1StaticL = ''
  let plot2StaticReady = false
  let plot2StaticSize = { width: 0, height: 0 }
  let plot3StaticReady = false
  let plot3StaticSize = { width: 0, height: 0 }
  let plot3StaticL = ''
  let freeEnergyStaticReady = false
  let freeEnergyStaticSize = { width: 0, height: 0 }
  let currentLayoutMode = ''
  const lIndexMap = new Map()

  const loadData1D = async () => {
    const dataUrl = `${import.meta.env.BASE_URL}data/1d-data.json`
    const res = await fetch(dataUrl)
    data1D = await res.json()
    energyTraces = data1D.energy_traces || []
    plot1StaticReady = false
    plot1StaticSize = { width: 0, height: 0 }
    plot1StaticL = ''
    plot2StaticReady = false
    plot2StaticSize = { width: 0, height: 0 }
    plot3StaticReady = false
    plot3StaticSize = { width: 0, height: 0 }
    plot3StaticL = ''
    freeEnergyStaticReady = false
    freeEnergyStaticSize = { width: 0, height: 0 }
    lIndexMap.clear()
    data1D.L_values.forEach((val, idx) => {
      lIndexMap.set(Number(val).toFixed(2), idx)
    })
  }

  const buildWaveData = (lVal) => {
    if (!data1D) return null
    const idx = lIndexMap.get(Number(lVal).toFixed(2))
    if (idx === undefined) return null
    return data1D.L_data[idx]
  }

  const getLegendLineSegments = (line) => {
    if (Array.isArray(line)) return line
    return [{ text: String(line) }]
  }

  const getLegendSegmentFont = (fontSize, script) => {
    const size = script ? Math.max(9, Math.round(fontSize * 0.72)) : fontSize
    return `${size}px Arial, sans-serif`
  }

  const measureLegendLine = (ctx, fontSize, line) => {
    const segments = getLegendLineSegments(line)
    return segments.reduce((width, segment) => {
      ctx.font = getLegendSegmentFont(fontSize, segment.script)
      return width + ctx.measureText(segment.text).width
    }, 0)
  }

  const drawLegendLine = (ctx, x, y, fontSize, line) => {
    const segments = getLegendLineSegments(line)
    let cursorX = x
    segments.forEach((segment) => {
      ctx.font = getLegendSegmentFont(fontSize, segment.script)
      const offsetY = segment.script === 'sub'
        ? fontSize * 0.32
        : segment.script === 'sup'
          ? -fontSize * 0.32
          : 0
      ctx.fillText(segment.text, cursorX, y + offsetY)
      cursorX += ctx.measureText(segment.text).width
    })
  }

  const getLegendMetrics = (plotWidth) => {
    const fontSize = Math.max(11, Math.min(15, Math.round(plotWidth / 28)))
    return {
      fontSize,
      lineHeight: Math.round(fontSize * 1.35),
      paddingX: Math.max(8, Math.min(12, Math.round(fontSize * 0.7))),
      paddingY: Math.max(6, Math.min(10, Math.round(fontSize * 0.6))),
      itemGap: Math.max(4, Math.min(7, Math.round(fontSize * 0.35))),
      columnGap: Math.max(14, Math.min(22, Math.round(fontSize * 1.4))),
      symbolGap: Math.max(8, Math.min(12, Math.round(fontSize * 0.7))),
      lineWidth: Math.max(18, Math.min(28, Math.round(plotWidth / 15))),
      markerRadius: Math.max(3, Math.min(5, Math.round(fontSize / 3.2)))
    }
  }

  const drawRoundedRectPath = (ctx, x, y, width, height, radius) => {
    const r = Math.min(radius, width / 2, height / 2)
    ctx.beginPath()
    ctx.moveTo(x + r, y)
    ctx.lineTo(x + width - r, y)
    ctx.arcTo(x + width, y, x + width, y + r, r)
    ctx.lineTo(x + width, y + height - r)
    ctx.arcTo(x + width, y + height, x + width - r, y + height, r)
    ctx.lineTo(x + r, y + height)
    ctx.arcTo(x, y + height, x, y + height - r, r)
    ctx.lineTo(x, y + r)
    ctx.arcTo(x, y, x + r, y, r)
    ctx.closePath()
  }

  const drawInlineLegend = (ctx, area, items, options = {}) => {
    if (!items.length) return
    const metrics = getLegendMetrics(area.width)
    const maxHeightRatio = options.maxHeightRatio || 1
    const preferredColumns = Math.max(1, options.columns || 1)
    const maxColumns = Math.max(preferredColumns, options.maxColumns || preferredColumns)
    const normalizedItems = items.map((item) => ({
      ...item,
      lines: Array.isArray(item.label)
        ? item.label
        : String(item.label).split('\n')
    }))
    ctx.save()
    ctx.font = `${metrics.fontSize}px Arial, sans-serif`
    ctx.textBaseline = 'top'

    let layout = null
    for (let columns = preferredColumns; columns <= maxColumns; columns += 1) {
      const rows = Math.ceil(normalizedItems.length / columns)
      const rowHeights = Array.from({ length: rows }, () => 0)
      const columnWidths = Array.from({ length: columns }, () => 0)

      normalizedItems.forEach((item, index) => {
        const column = Math.floor(index / rows)
        const row = index % rows
        const labelWidth = item.lines.reduce((maxWidth, line) => Math.max(maxWidth, measureLegendLine(ctx, metrics.fontSize, line)), 0)
        const itemHeight = item.lines.length * metrics.lineHeight
        rowHeights[row] = Math.max(rowHeights[row], itemHeight)
        columnWidths[column] = Math.max(columnWidths[column], metrics.lineWidth + metrics.symbolGap + labelWidth)
      })

      const contentHeight = rowHeights.reduce((sum, rowHeight) => sum + rowHeight, 0) + Math.max(0, rows - 1) * metrics.itemGap
      const boxHeight = metrics.paddingY * 2 + contentHeight
      layout = {
        columns,
        rows,
        rowHeights,
        columnWidths,
        boxHeight,
        boxWidth: metrics.paddingX * 2 + columnWidths.reduce((sum, columnWidth) => sum + columnWidth, 0) + Math.max(0, columns - 1) * metrics.columnGap
      }
      if (boxHeight <= area.height * maxHeightRatio) break
    }

    if (!layout) {
      ctx.restore()
      return
    }

    const boxX = area.left + area.width - layout.boxWidth - 10
    const boxY = area.top + 10

    ctx.fillStyle = 'rgba(255, 255, 255, 0.82)'
    ctx.strokeStyle = 'rgba(70, 70, 70, 0.18)'
    ctx.lineWidth = 1
    drawRoundedRectPath(ctx, boxX, boxY, layout.boxWidth, layout.boxHeight, 6)
    ctx.fill()
    ctx.stroke()

    const rowOffsets = []
    let currentRowOffset = boxY + metrics.paddingY
    layout.rowHeights.forEach((rowHeight, index) => {
      rowOffsets[index] = currentRowOffset
      currentRowOffset += rowHeight
      if (index < layout.rowHeights.length - 1) currentRowOffset += metrics.itemGap
    })

    const columnOffsets = []
    let currentColumnOffset = boxX + metrics.paddingX
    layout.columnWidths.forEach((columnWidth, index) => {
      columnOffsets[index] = currentColumnOffset
      currentColumnOffset += columnWidth
      if (index < layout.columnWidths.length - 1) currentColumnOffset += metrics.columnGap
    })

    const rowsPerColumn = layout.rows
    normalizedItems.forEach((item, index) => {
      const column = Math.floor(index / rowsPerColumn)
      const row = index % rowsPerColumn
      const cellTop = rowOffsets[row]
      const cellHeight = layout.rowHeights[row]
      const symbolLeft = columnOffsets[column]
      const textX = symbolLeft + metrics.lineWidth + metrics.symbolGap
      const labelHeight = item.lines.length * metrics.lineHeight
      const textTop = cellTop + (cellHeight - labelHeight) / 2
      const symbolCenterY = cellTop + cellHeight / 2

      if (item.type === 'marker') {
        ctx.save()
        ctx.fillStyle = item.color
        ctx.beginPath()
        ctx.arc(symbolLeft + metrics.lineWidth / 2, symbolCenterY, metrics.markerRadius, 0, Math.PI * 2)
        ctx.fill()
        ctx.restore()
      } else {
        ctx.save()
        ctx.strokeStyle = item.color
        ctx.lineWidth = item.width || 2
        ctx.beginPath()
        ctx.moveTo(symbolLeft, symbolCenterY)
        ctx.lineTo(symbolLeft + metrics.lineWidth, symbolCenterY)
        ctx.stroke()
        ctx.restore()
      }

      ctx.fillStyle = '#222'
      item.lines.forEach((line, lineIndex) => {
        drawLegendLine(ctx, textX, textTop + lineIndex * metrics.lineHeight, metrics.fontSize, line)
      })
    })

    ctx.restore()
  }

  const renderPlot3PsiLabels = (area, mapY, yTicks) => {
    const labelContainer = document.getElementById('plot3-psi-labels')
    if (!labelContainer) return
    const labelFontSize = Math.max(11, Math.min(18, Math.round(area.width / 28)))
    const labels = yTicks.map((val, i) => {
      const top = mapY(val)
      const left = area.left + area.width + 6
      return `
        <div style="position: absolute; top: ${top}px; left: ${left}px; transform: translateY(-50%); font-size: ${labelFontSize}px; font-family: Arial, sans-serif; white-space: nowrap;">
          &#x03C8;<sub>${i + 1}</sub>
        </div>
      `
    }).join('')
    labelContainer.innerHTML = labels
  }

  const renderAxisLabels = (mode) => {
    const finiteLabels = [
      { id: 'plot1-xlabel', text: 'x' },
      { id: 'plot1-ylabel', text: '\u03C8 and |\u03C8|\u00B2' },
      { id: 'plot2-xlabel', text: 'L' },
      { id: 'plot2-ylabel', text: 'E (a.u.)' },
      { id: 'plot3-xlabel', text: 'x' },
      { id: 'plot3-ylabel', text: 'E (a.u.)' }
    ]
    const freeLabels = [
      { id: 'plot1-xlabel', text: 'x' },
      { id: 'plot1-ylabel', text: '\u03C8 and |\u03C8|\u00B2' },
      { id: 'plot2-xlabel', text: 'k' },
      { id: 'plot2-ylabel', text: 'E (a.u.)' }
    ]
    const labels = mode === 'free' ? freeLabels : finiteLabels
    labels.forEach(({ id, text }) => {
      const el = document.getElementById(id)
      if (!el) return
      el.textContent = text
      el.style.fontFamily = 'Arial, sans-serif'
    })
  }
  const setupCanvas = (canvasId) => {
    const canvas = document.getElementById(canvasId)
    if (!canvas) return null
    const rect = canvas.getBoundingClientRect()
    const width = Math.max(1, rect.width)
    const height = Math.max(1, rect.height)
    const ratio = window.devicePixelRatio || 1
    const targetWidth = Math.round(width * ratio)
    const targetHeight = Math.round(height * ratio)
    if (canvas.width !== targetWidth || canvas.height !== targetHeight) {
      canvas.width = targetWidth
      canvas.height = targetHeight
    }
    const ctx = canvas.getContext('2d')
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
    ctx.clearRect(0, 0, width, height)
    return { ctx, width, height }
  }

  const PLOT_MARGIN = {
    left: 68,
    right: 32,
    top: 38,
    bottom: 48
  }

  const getPlotArea = (width, height) => {
    const { left, right, top, bottom } = PLOT_MARGIN
    return {
      left,
      top,
      width: Math.max(1, width - left - right),
      height: Math.max(1, height - top - bottom)
    }
  }

  const createMapper = (area, xRange, yRange) => {
    const [xMin, xMax] = xRange
    const [yMin, yMax] = yRange
    const xScale = area.width / (xMax - xMin)
    const yScale = area.height / (yMax - yMin)
    return {
      mapX: (x) => area.left + (x - xMin) * xScale,
      mapY: (y) => area.top + area.height - (y - yMin) * yScale
    }
  }
  const drawAxes = (ctx, area, xRange, yRange, opts = {}) => {
    const {
      title,
      xLabel,
      yLabel,
      xTicks,
      yTicks,
      xTickLabels,
      yTickLabels,
      xDecimals = 1,
      yDecimals = 1,
      yLabelOffset = 0,
      drawAxisLabels = true,
      drawGrid = false
    } = opts

    const [xMin, xMax] = xRange
    const [yMin, yMax] = yRange
    const xTickVals = xTicks || Array.from({ length: 6 }, (_, i) => xMin + ((xMax - xMin) * i) / 5)
    const yTickVals = yTicks || Array.from({ length: 6 }, (_, i) => yMin + ((yMax - yMin) * i) / 5)

    if (drawGrid) {
      ctx.save()
      ctx.strokeStyle = '#d6d6d6'
      ctx.lineWidth = 1
      ctx.setLineDash([])

      xTickVals.forEach((val) => {
        const x = area.left + ((val - xMin) / (xMax - xMin)) * area.width
        ctx.beginPath()
        ctx.moveTo(x, area.top)
        ctx.lineTo(x, area.top + area.height)
        ctx.stroke()
      })

      yTickVals.forEach((val) => {
        const y = area.top + area.height - ((val - yMin) / (yMax - yMin)) * area.height
        ctx.beginPath()
        ctx.moveTo(area.left, y)
        ctx.lineTo(area.left + area.width, y)
        ctx.stroke()
      })
      ctx.restore()
    }

    ctx.save()
    ctx.strokeStyle = '#444'
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.rect(area.left, area.top, area.width, area.height)
    ctx.stroke()

    ctx.fillStyle = '#222'
    ctx.font = '14px Arial, sans-serif'

    if (title) {
      const containerWidth = document.getElementById('infinite-well-1d')?.getBoundingClientRect().width || window.innerWidth
      const titleFontSize = Math.max(12, Math.min(24, Math.round(containerWidth / 52)))
      ctx.textAlign = 'center'
      ctx.textBaseline = 'bottom'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'bottom'
      ctx.font = `${titleFontSize}px Arial, sans-serif`
      ctx.fillText(title, area.left + area.width / 2, area.top - 6)
    }

    ctx.textAlign = 'center'
    ctx.textBaseline = 'top'
    ctx.font = '14px Arial, sans-serif'
    xTickVals.forEach((val, i) => {
      const x = area.left + ((val - xMin) / (xMax - xMin)) * area.width
      ctx.beginPath()
      ctx.moveTo(x, area.top + area.height)
      ctx.lineTo(x, area.top + area.height + 5)
      ctx.stroke()
      const label = xTickLabels ? xTickLabels[i] : val.toFixed(xDecimals)
      ctx.fillText(label, x, area.top + area.height + 8)
    })

    ctx.textAlign = 'right'
    ctx.textBaseline = 'middle'
    ctx.font = '14px Arial, sans-serif'
    yTickVals.forEach((val, i) => {
      const y = area.top + area.height - ((val - yMin) / (yMax - yMin)) * area.height
      ctx.beginPath()
      ctx.moveTo(area.left - 5, y)
      ctx.lineTo(area.left, y)
      ctx.stroke()
      const label = yTickLabels ? yTickLabels[i] : val.toFixed(yDecimals)
      ctx.fillText(label, area.left - 10, y)
    })

    if (xLabel && drawAxisLabels) {
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      ctx.font = '18px Arial, sans-serif'
      ctx.fillText(xLabel, area.left + area.width / 2, area.top + area.height + 24)
    }

    if (yLabel && drawAxisLabels) {
      ctx.save()
      ctx.translate(Math.max(6, area.left / 2 - 20) + yLabelOffset, area.top + area.height / 2)
      ctx.rotate(-Math.PI / 2)
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      ctx.font = '18px Arial, sans-serif'
      ctx.fillText(yLabel, 0, 0)
      ctx.restore()
    }

    ctx.restore()
  }

  const clipToPlotArea = (ctx, area, drawFn) => {
    ctx.save()
    ctx.beginPath()
    ctx.rect(area.left, area.top, area.width, area.height)
    ctx.clip()
    drawFn()
    ctx.restore()
  }
  const drawLine = (ctx, xArr, yArr, mapX, mapY, color, width = 1, dash = []) => {
    if (!xArr.length) return
    ctx.save()
    ctx.strokeStyle = color
    ctx.lineWidth = width
    ctx.setLineDash(dash)
    ctx.beginPath()
    ctx.moveTo(mapX(xArr[0]), mapY(yArr[0]))
    for (let i = 1; i < xArr.length; i += 1) {
      ctx.lineTo(mapX(xArr[i]), mapY(yArr[i]))
    }
    ctx.stroke()
    ctx.restore()
  }
  const fillArea = (ctx, xArr, yArr, mapX, mapY, baseValue, fillStyle) => {
    if (!xArr.length) return
    ctx.save()
    ctx.fillStyle = fillStyle
    ctx.beginPath()
    ctx.moveTo(mapX(xArr[0]), mapY(baseValue))
    for (let i = 0; i < xArr.length; i += 1) {
      ctx.lineTo(mapX(xArr[i]), mapY(yArr[i]))
    }
    ctx.lineTo(mapX(xArr[xArr.length - 1]), mapY(baseValue))
    ctx.closePath()
    ctx.fill()
    ctx.restore()
  }
  const buildXTicks = (lVal) => {
    const xTicks = []
    for (let val = 0; val <= lVal + 1e-9; val += 0.5) {
      xTicks.push(Number(val.toFixed(1)))
    }
    return xTicks
  }
  const exportAllPlotsBitmap = async () => {
    const container = document.getElementById('infinite-well-1d')
    if (!container) return
    const canvas = await html2canvas(container, {
      backgroundColor: '#ffffff',
      scale: window.devicePixelRatio || 1,
      useCORS: true,
      logging: false
    })
    canvas.toBlob((blob) => {
      if (!blob) return
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = '1d-plots.png'
      link.click()
      URL.revokeObjectURL(link.href)
    }, 'image/png')
  }

  const handleSaveImages = async () => {
    drawInfiniteWell1D()
    await exportAllPlotsBitmap()
  }
  const drawPlot1Static = (lVal) => {
    const canvasInfo = setupCanvas('plot1-bg')
    if (!canvasInfo) return
    const { ctx, width, height } = canvasInfo
    plot1StaticSize = { width, height }
    plot1StaticL = getLKey(lVal)
    const area = getPlotArea(width, height)
    const xRange = [0, lVal]
    const yRange = [-2.5, 2.5]
    const xTicks = buildXTicks(lVal)

    drawAxes(ctx, area, xRange, yRange, {
      title: 'Wavefunction and Probability Density',
      xLabel: 'x',
      yLabel: 'psi and psi^2',
      xDecimals: 1,
      yDecimals: 1,
      xTicks,
      drawGrid: true,
      drawAxisLabels: false
    })
    plot1StaticReady = true
  }

  const ensurePlot1Static = (lVal) => {
    const bg = document.getElementById('plot1-bg')
    if (!bg) return
    const rect = bg.getBoundingClientRect()
    const width = Math.max(1, Math.round(rect.width))
    const height = Math.max(1, Math.round(rect.height))
    const lKey = getLKey(lVal)
    if (!plot1StaticReady || width !== plot1StaticSize.width || height !== plot1StaticSize.height || plot1StaticL !== lKey) {
      drawPlot1Static(lVal)
    }
  }
  const drawPlot1 = (waveData, nIndex, lVal) => {
    ensurePlot1Static(lVal)
    const canvasInfo = setupCanvas('plot1-canvas')
    if (!canvasInfo) return
    const { ctx, width, height } = canvasInfo
    const area = getPlotArea(width, height)
    const xRange = [0, lVal]
    const yRange = [-2.5, 2.5]
    const { mapX, mapY } = createMapper(area, xRange, yRange)

    const item = waveData.perN[nIndex]
    const xArr = waveData.x
    clipToPlotArea(ctx, area, () => {
      fillArea(ctx, xArr, item.psi2, mapX, mapY, 0, 'rgba(255, 0, 0, 0.2)')
      drawLine(ctx, xArr, item.psi2, mapX, mapY, 'red', 2)
      drawLine(ctx, xArr, item.psi, mapX, mapY, colors[nIndex], 2.5)
    })

    drawInlineLegend(ctx, area, [
      {
        type: 'line',
        color: colors[nIndex],
        width: 2.5,
        label: [[{ text: '\u03C8' }, { text: String(nIndex + 1), script: 'sub' }]]
      },
      {
        type: 'line',
        color: 'red',
        width: 2,
        label: [[
          { text: `|\u03C8` },
          { text: String(nIndex + 1), script: 'sub' },
          { text: '|' },
          { text: '2', script: 'sup' }
        ]]
      }
    ])
  }
  const drawPlot2Static = () => {
    if (!energyTraces.length) return
    const canvasInfo = setupCanvas('plot2-bg')
    if (!canvasInfo) return
    const { ctx, width, height } = canvasInfo
    plot2StaticSize = { width, height }
    const area = getPlotArea(width, height)
    const xRange = [L_MIN, L_MAX]
    const yRange = [-5, 130]
    const { mapX, mapY } = createMapper(area, xRange, yRange)
    const yTicks = []
    for (let val = 0; val <= yRange[1] + 1e-9; val += 20) {
      yTicks.push(val)
    }
    const yTickLabels = yTicks.map((val) => val.toFixed(0))
    drawAxes(ctx, area, xRange, yRange, {
      title: 'Energy Levels',
      xLabel: 'L',
      yLabel: 'E (a.u.)',
      xDecimals: 1,
      yDecimals: 0,
      yTicks,
      yTickLabels,
      drawAxisLabels: false
    })

    clipToPlotArea(ctx, area, () => {
      energyTraces.forEach((trace, i) => {
        drawLine(ctx, trace.x, trace.y, mapX, mapY, colors[i], 2)
      })
      ctx.save()
      ctx.strokeStyle = '#555'
      ctx.lineWidth = 1.5
      ctx.beginPath()
      ctx.moveTo(mapX(L_MIN), mapY(0))
      ctx.lineTo(mapX(L_MAX), mapY(0))
      ctx.stroke()
      ctx.restore()
    })
    drawInlineLegend(ctx, area, [
      ...energyTraces.slice(0, 7).map((_, idx) => ({
        type: 'line',
        color: colors[idx],
        width: 2,
        label: [[{ text: 'E' }, { text: String(idx + 1), script: 'sub' }]]
      })),
      {
        type: 'marker',
        color: 'red',
        label: [[{ text: 'E' }, { text: 'current', script: 'sub' }]]
      }
    ], {
      columns: 2,
      maxColumns: 2,
      maxHeightRatio: 0.48
    })
    plot2StaticReady = true
  }

  const ensurePlot2Static = () => {
    const bg = document.getElementById('plot2-bg')
    if (!bg) return
    const rect = bg.getBoundingClientRect()
    const width = Math.max(1, Math.round(rect.width))
    const height = Math.max(1, Math.round(rect.height))
    if (!plot2StaticReady || width !== plot2StaticSize.width || height !== plot2StaticSize.height) {
      drawPlot2Static()
    }
  }

  const drawPlot2 = (lVal, energyVal) => {
    ensurePlot2Static()
    const canvasInfo = setupCanvas('plot2-canvas')
    if (!canvasInfo) return
    const { ctx, width, height } = canvasInfo
    const area = getPlotArea(width, height)
    const xRange = [L_MIN, L_MAX]
    const yRange = [-5, 130]
    const { mapX, mapY } = createMapper(area, xRange, yRange)

    clipToPlotArea(ctx, area, () => {
      ctx.save()
      ctx.fillStyle = 'red'
      ctx.beginPath()
      ctx.arc(mapX(lVal), mapY(energyVal), 4, 0, Math.PI * 2)
      ctx.fill()
      ctx.restore()
    })
  }
  const drawPlot3Static = (waveData, lVal) => {
    const canvasInfo = setupCanvas('plot3-bg')
    if (!canvasInfo) return
    const { ctx, width, height } = canvasInfo
    plot3StaticSize = { width, height }
    plot3StaticL = getLKey(lVal)
    const area = getPlotArea(width, height)
    const yRange = waveData.layout3.yaxis.range
    const xRange = [0, lVal]
    const { mapX, mapY } = createMapper(area, xRange, yRange)
    const xTicks = buildXTicks(lVal)

    drawAxes(ctx, area, xRange, yRange, {
      title: 'Wavefunctions with Energy Levels',
      xLabel: 'x',
      yLabel: 'E (a.u.)',
      xDecimals: 1,
      yDecimals: 1,
      yLabelOffset: -12,
      yTicks: waveData.layout3.yaxis.tickvals,
      yTickLabels: waveData.layout3.yaxis.ticktext,
      xTicks,
      drawGrid: true,
      drawAxisLabels: false
    })

    const yTicks = waveData.layout3.yaxis.tickvals || []
    renderPlot3PsiLabels(area, mapY, yTicks)
    plot3StaticReady = true
  }

  const ensurePlot3Static = (waveData, lVal) => {
    const bg = document.getElementById('plot3-bg')
    if (!bg) return
    const rect = bg.getBoundingClientRect()
    const width = Math.max(1, Math.round(rect.width))
    const height = Math.max(1, Math.round(rect.height))
    const lKey = getLKey(lVal)
    if (!plot3StaticReady || width !== plot3StaticSize.width || height !== plot3StaticSize.height || plot3StaticL !== lKey) {
      drawPlot3Static(waveData, lVal)
    }
  }

  const drawPlot3 = (waveData, lVal) => {
    ensurePlot3Static(waveData, lVal)
    const canvasInfo = setupCanvas('plot3-canvas')
    if (!canvasInfo) return
    const { ctx, width, height } = canvasInfo
    const area = getPlotArea(width, height)
    const yRange = waveData.layout3.yaxis.range
    const xRange = [0, lVal]
    const { mapX, mapY } = createMapper(area, xRange, yRange)
    clipToPlotArea(ctx, area, () => {
      waveData.perN.forEach((item, i) => {
        drawLine(ctx, waveData.x, item.offset, mapX, mapY, colors[i], 2)
      })
    })
  }

  const buildFreeParticleWaveData = () => {
    const x = []
    const psi = []
    const psi2 = []
    for (let val = FREE_X_MIN; val <= FREE_X_MAX + 1e-9; val += FREE_X_STEP) {
      const xVal = Number(val.toFixed(4))
      const psiVal = A.value * Math.cos(k.value * xVal) + B.value * Math.sin(k.value * xVal)
      x.push(xVal)
      psi.push(psiVal)
      psi2.push(psiVal * psiVal)
    }
    return { x, psi, psi2 }
  }

  const buildFreeEnergyTrace = () => {
    const x = []
    const y = []
    for (let val = K_MIN; val <= K_MAX + 1e-9; val += 0.1) {
      const kVal = Number(val.toFixed(4))
      x.push(kVal)
      y.push(0.5 * kVal * kVal)
    }
    return { x, y }
  }

  const drawFreePlot1 = (waveData) => {
    const canvasInfo = setupCanvas('plot1-bg')
    if (!canvasInfo) return
    const { ctx, width, height } = canvasInfo
    const area = getPlotArea(width, height)
    const xRange = [FREE_X_MIN, FREE_X_MAX]
    const yRange = [-3, 3]
    const xTicks = [FREE_X_MIN, -2.5, 0, 2.5, FREE_X_MAX]
    const { mapX, mapY } = createMapper(area, xRange, yRange)

    drawAxes(ctx, area, xRange, yRange, {
      title: 'Wavefunction and Probabilitity Density',
      xLabel: 'x',
      yLabel: 'psi and psi^2',
      xTicks,
      xDecimals: 1,
      yDecimals: 1,
      drawGrid: true,
      drawAxisLabels: false
    })

    const fgCanvasInfo = setupCanvas('plot1-canvas')
    if (!fgCanvasInfo) return
    const fgCtx = fgCanvasInfo.ctx
    clipToPlotArea(fgCtx, area, () => {
      fillArea(fgCtx, waveData.x, waveData.psi2, mapX, mapY, 0, 'rgba(255, 0, 0, 0.2)')
      drawLine(fgCtx, waveData.x, waveData.psi2, mapX, mapY, 'red', 2)
      drawLine(fgCtx, waveData.x, waveData.psi, mapX, mapY, colors[0], 2.5)
    })

    drawInlineLegend(fgCtx, area, [
      {
        type: 'line',
        color: colors[0],
        width: 2.5,
        label: [[{ text: '\u03C8' }]]
      },
      {
        type: 'line',
        color: 'red',
        width: 2,
        label: [[
          { text: '|\u03C8|' },
          { text: '2', script: 'sup' }
        ]]
      }
    ])
  }

  const drawFreeEnergyPlotStatic = () => {
    const canvasInfo = setupCanvas('plot2-bg')
    if (!canvasInfo) return
    const { ctx, width, height } = canvasInfo
    freeEnergyStaticSize = { width, height }
    const area = getPlotArea(width, height)
    const xRange = [K_MIN, K_MAX]
    const yRange = [0, 6]
    const { mapX, mapY } = createMapper(area, xRange, yRange)
    const trace = buildFreeEnergyTrace()
    const yTicks = []
    for (let val = 0; val <= 6 + 1e-9; val += 1) yTicks.push(val)

    drawAxes(ctx, area, xRange, yRange, {
      title: 'Energy',
      xLabel: 'k',
      yLabel: 'E (a.u.)',
      xDecimals: 1,
      yDecimals: 0,
      yTicks,
      drawGrid: true,
      drawAxisLabels: false
    })

    clipToPlotArea(ctx, area, () => {
      drawLine(ctx, trace.x, trace.y, mapX, mapY, colors[2], 2.2)
    })

    drawInlineLegend(ctx, area, [
      {
        type: 'line',
        color: colors[2],
        width: 2.2,
        label: [[{ text: 'E(k)' }]]
      },
      {
        type: 'marker',
        color: 'red',
        label: [[
          { text: 'E' },
          { text: 'current', script: 'sub' }
        ]]
      }
    ])
    freeEnergyStaticReady = true
  }

  const ensureFreeEnergyPlotStatic = () => {
    const bg = document.getElementById('plot2-bg')
    if (!bg) return
    const rect = bg.getBoundingClientRect()
    const width = Math.max(1, Math.round(rect.width))
    const height = Math.max(1, Math.round(rect.height))
    if (!freeEnergyStaticReady || width !== freeEnergyStaticSize.width || height !== freeEnergyStaticSize.height) {
      drawFreeEnergyPlotStatic()
    }
  }

  const drawFreeEnergyPlot = () => {
    ensureFreeEnergyPlotStatic()
    const canvasInfo = setupCanvas('plot2-canvas')
    if (!canvasInfo) return
    const { ctx, width, height } = canvasInfo
    const area = getPlotArea(width, height)
    const xRange = [K_MIN, K_MAX]
    const yRange = [0, 6]
    const { mapX, mapY } = createMapper(area, xRange, yRange)
    const currentEnergy = 0.5 * k.value * k.value
    clipToPlotArea(ctx, area, () => {
      ctx.save()
      ctx.fillStyle = 'red'
      ctx.beginPath()
      ctx.arc(mapX(k.value), mapY(currentEnergy), 4, 0, Math.PI * 2)
      ctx.fill()
      ctx.restore()
    })
  }
  const ensurePlotContainer = (mode) => {
    const plotContainer = document.getElementById('infinite-well-1d')
    if (!plotContainer) return
    const needsInit = mode === 'free'
      ? !document.getElementById('plot1') || !document.getElementById('plot2') || !!document.getElementById('plot3')
      : !document.getElementById('plot1') || !document.getElementById('plot2') || !document.getElementById('plot3')
    if (!needsInit) return

    if (mode === 'free') {
      plotContainer.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: minmax(0, 1fr); align-items: stretch; gap: 16px; height: 100%; width: 100%; box-sizing: border-box;">
        <div id="plot1-wrap" style="position: relative; width: 100%; height: 100%; box-sizing: border-box; min-width: 0;">
          <div id="plot1" style="position: relative; width: 100%; height: 100%; box-sizing: border-box;">
            <canvas id="plot1-bg" style="position: absolute; inset: 0; width: 100%; height: 100%; display: block;"></canvas>
            <canvas id="plot1-canvas" style="position: absolute; inset: 0; width: 100%; height: 100%; display: block;"></canvas>
          </div>
          <div id="plot1-xlabel" style="position: absolute; left: ${PLOT_MARGIN.left}px; right: ${PLOT_MARGIN.right}px; bottom: 6px; text-align: center; pointer-events: none; font-size: 18px;"></div>
          <div id="plot1-ylabel" style="position: absolute; top: 50%; left: 16px; transform: translate(-50%, -50%) rotate(-90deg); transform-origin: center; pointer-events: none; font-size: 18px;"></div>
        </div>
        <div id="plot2-wrap" style="position: relative; width: 100%; height: 100%; box-sizing: border-box; min-width: 0;">
          <div id="plot2" style="position: relative; width: 100%; height: 100%; box-sizing: border-box;">
            <canvas id="plot2-bg" style="position: absolute; inset: 0; width: 100%; height: 100%; display: block;"></canvas>
            <canvas id="plot2-canvas" style="position: absolute; inset: 0; width: 100%; height: 100%; display: block;"></canvas>
          </div>
          <div id="plot2-xlabel" style="position: absolute; left: ${PLOT_MARGIN.left}px; right: ${PLOT_MARGIN.right}px; bottom: 6px; text-align: center; pointer-events: none; font-size: 18px;"></div>
          <div id="plot2-ylabel" style="position: absolute; top: 50%; left: 16px; transform: translate(-50%, -50%) rotate(-90deg); transform-origin: center; pointer-events: none; font-size: 18px;"></div>
        </div>
      </div>
    `
    } else {
      plotContainer.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: repeat(2, minmax(0, 1fr)); align-items: stretch; gap: 16px; height: 100%; width: 100%; box-sizing: border-box;">
        <div id="plot1-wrap" style="position: relative; width: 100%; height: 100%; box-sizing: border-box;">
          <div id="plot1" style="position: relative; width: 100%; height: 100%; box-sizing: border-box;">
            <canvas id="plot1-bg" style="position: absolute; inset: 0; width: 100%; height: 100%; display: block;"></canvas>
            <canvas id="plot1-canvas" style="position: absolute; inset: 0; width: 100%; height: 100%; display: block;"></canvas>
          </div>
          <div id="plot1-xlabel" style="position: absolute; left: ${PLOT_MARGIN.left}px; right: ${PLOT_MARGIN.right}px; bottom: 6px; text-align: center; pointer-events: none; font-size: 18px;"></div>
          <div id="plot1-ylabel" style="position: absolute; top: 50%; left: 16px; transform: translate(-50%, -50%) rotate(-90deg); transform-origin: center; pointer-events: none; font-size: 18px;"></div>
        </div>
        <div id="plot3-wrap" style="position: relative; width: 100%; height: 100%; grid-row: span 2; box-sizing: border-box;">
          <div id="plot3" style="position: relative; width: 100%; height: 100%; box-sizing: border-box;">
            <canvas id="plot3-bg" style="position: absolute; inset: 0; width: 100%; height: 100%; display: block;"></canvas>
            <canvas id="plot3-canvas" style="position: absolute; inset: 0; width: 100%; height: 100%; display: block;"></canvas>
          </div>
          <div id="plot3-psi-labels" style="position: absolute; inset: 0; pointer-events: none;"></div>
          <div id="plot3-xlabel" style="position: absolute; left: ${PLOT_MARGIN.left}px; right: ${PLOT_MARGIN.right}px; bottom: 6px; text-align: center; pointer-events: none; font-size: 18px;"></div>
          <div id="plot3-ylabel" style="position: absolute; top: 50%; left: 10px; transform: translate(-50%, -50%) rotate(-90deg); transform-origin: center; pointer-events: none; font-size: 18px;"></div>
        </div>
        <div id="plot2-wrap" style="position: relative; width: 100%; height: 100%; box-sizing: border-box;">
          <div id="plot2" style="position: relative; width: 100%; height: 100%; box-sizing: border-box;">
            <canvas id="plot2-bg" style="position: absolute; inset: 0; width: 100%; height: 100%; display: block;"></canvas>
            <canvas id="plot2-canvas" style="position: absolute; inset: 0; width: 100%; height: 100%; display: block;"></canvas>
          </div>
          <div id="plot2-xlabel" style="position: absolute; left: ${PLOT_MARGIN.left}px; right: ${PLOT_MARGIN.right}px; bottom: 6px; text-align: center; pointer-events: none; font-size: 18px;"></div>
          <div id="plot2-ylabel" style="position: absolute; top: 50%; left: 16px; transform: translate(-50%, -50%) rotate(-90deg); transform-origin: center; pointer-events: none; font-size: 18px;"></div>
        </div>
      </div>
    `
    }
    currentLayoutMode = mode
    plot1StaticReady = false
    plot2StaticReady = false
    plot3StaticReady = false
    freeEnergyStaticReady = false
    renderAxisLabels(mode)
  }

  const updateOverlayTypography = () => {
    const plotContainer = document.getElementById('infinite-well-1d')
    if (!plotContainer) return
    const containerWidth = plotContainer.getBoundingClientRect().width || window.innerWidth
    const axisFontSize = Math.max(12, Math.min(18, Math.round(containerWidth / 55)))
    ;['plot1-xlabel', 'plot1-ylabel', 'plot2-xlabel', 'plot2-ylabel', 'plot3-xlabel', 'plot3-ylabel'].forEach((id) => {
      const el = document.getElementById(id)
      if (!el) return
      el.style.fontSize = `${axisFontSize}px`
    })
  }
  const supportsAspectRatio = () => {
    return typeof CSS !== 'undefined' &&
      typeof CSS.supports === 'function' &&
      CSS.supports('aspect-ratio: 3 / 2')
  }

  const syncPlotContainerSize = () => {
    const plotContainer = document.getElementById('infinite-well-1d')
    if (!plotContainer) return
    const width = plotContainer.clientWidth
    if (!width) return
    const rect = plotContainer.getBoundingClientRect()
    const viewportGap = 16
    const availableHeight = Math.max(1, Math.floor(window.innerHeight - rect.top - viewportGap))
    const height = Math.max(1, Math.min(Math.round(width / PLOT_ASPECT_RATIO), availableHeight))
    if (supportsAspectRatio()) {
      plotContainer.style.aspectRatio = 'auto'
    }
    plotContainer.style.height = `${height}px`
  }
  const drawInfiniteWell1D = () => {
    syncPlotContainerSize()
    const mode = isInfiniteL.value ? 'free' : 'finite'
    if (currentLayoutMode !== mode) {
      currentLayoutMode = ''
    }
    ensurePlotContainer(mode)
    updateOverlayTypography()
    if (isInfiniteL.value) {
      const freeWaveData = buildFreeParticleWaveData()
      drawFreePlot1(freeWaveData)
      drawFreeEnergyPlot()
      return
    }

    if (!data1D) return
    const lVal = normalizeL(L.value)
    const waveData = buildWaveData(lVal)
    if (!waveData) return
    const nIndex = n.value - 1
    const energyVal = waveData.perN[nIndex]?.energy
    if (energyVal === undefined) return

    drawPlot1(waveData, nIndex, lVal)
    drawPlot2(lVal, energyVal)
    drawPlot3(waveData, lVal)
  }
  let rafId = 0
  const scheduleDraw = () => {
    if (rafId) return
    rafId = window.requestAnimationFrame(() => {
      rafId = 0
      drawInfiniteWell1D()
    })
  }
  const debouncedDraw = debounce(scheduleDraw, 16)
  let resizeObserver = null
  const observePlotSize = () => {
    if (typeof ResizeObserver === 'undefined') return
    const targets = [
      document.getElementById('infinite-well-1d'),
      document.querySelector('.layout-content')
    ].filter(Boolean)
    if (!targets.length) return
    resizeObserver = new ResizeObserver(() => {
      debouncedDraw()
    })
    targets.forEach((el) => resizeObserver.observe(el))
  }

  watch([n, L, isInfiniteL, A, B, k], () => {
    scheduleDraw()
  })
  watch(isInfiniteL, (next) => {
    if (next) {
      lastFiniteL.value = L.value
      L.value = L_MAX
      return
    }
    L.value = normalizeL(lastFiniteL.value)
  })
  onMounted(async () => {
    startFpsMonitor()
    try {
      await loadData1D()
    } catch (err) {
      console.error('Failed to load 1D data', err)
      return
    }
    scheduleDraw()
    observePlotSize()
  })

  onUnmounted(() => {
    if (resizeObserver) {
      resizeObserver.disconnect()
      resizeObserver = null
    }
    if (rafId) {
      window.cancelAnimationFrame(rafId)
      rafId = 0
    }
    if (fpsRaf) {
      window.cancelAnimationFrame(fpsRaf)
      fpsRaf = 0
    }
    plot1StaticReady = false
    plot2StaticReady = false
    plot3StaticReady = false
    freeEnergyStaticReady = false
    currentLayoutMode = ''
  })
</script>

<style scoped>
  @import './style.css';
</style>









