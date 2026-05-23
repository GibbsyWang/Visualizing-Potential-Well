<template>
  <!-- 通用页面布局：左侧为参数面板，右侧为图形内容区。 -->
  <div class="layout" :class="{ 'layout--compact': isCompact }">
    <div class="layout-sidebar" v-show="state.showSidebar" :style="sidebarStyle">
      <div class="layout-sidebar-retract">
        <button
          type="button"
          class="layout-toggle-button"
          aria-label="Collapse sidebar"
          @click="handleRetractSidebar"
        >
          <span class="layout-toggle-icon">‹</span>
        </button>
      </div>
      <div class="layout-sidebar-content">
        <slot name="sidebar"></slot>
      </div>
      <div v-if="!isCompact" class="layout-sidebar-resizer" @mousedown="handleResizeStart"></div>
    </div>
    <div class="layout-content" :class="{ 'layout-content--collapsed': !state.showSidebar }" :style="contentStyle">
      <div class="layout-content-retract" v-if="!state.showSidebar">
        <button
          type="button"
          class="layout-toggle-button"
          aria-label="Expand sidebar"
          @click="handleRetractSidebar"
        >
          <span class="layout-toggle-icon">›</span>
        </button>
      </div>
      <slot name="content"></slot>
    </div>
  </div>
</template>


<script setup>
  // 布局组件：统一处理侧边栏显隐、宽度拖拽与窄屏切换。
  import { reactive, ref, onMounted, onUnmounted, nextTick, computed } from 'vue'

  // 布局阈值：控制桌面端最小内容区宽度与窄屏切换断点。
  const MIN_SIDEBAR_WIDTH = 220
  const MAX_SIDEBAR_WIDTH = 600
  const MIN_CONTENT_WIDTH = 720
  const COMPACT_BREAKPOINT = 1080
  const sidebarWidth = ref(480)
  const isCompact = ref(false)

  const state = reactive({
    showSidebar: true
  })

  // 根据当前模式动态计算侧边栏与内容区样式。
  const sidebarStyle = computed(() => (
    isCompact.value
      ? null
      : { width: `${sidebarWidth.value}px` }
  ))

  const contentStyle = computed(() => (
    isCompact.value
      ? { minWidth: '0' }
      : { minWidth: `${MIN_CONTENT_WIDTH}px` }
  ))

  // 每次布局切换后重置横向滚动，防止内容区停留在错误位置。
  const resetLayoutPosition = () => {
    const layoutEl = document.querySelector('.layout')
    if (layoutEl) {
      layoutEl.scrollLeft = 0
    }
    const contentEl = document.querySelector('.layout-content')
    if (contentEl) {
      contentEl.scrollLeft = 0
    }
    window.dispatchEvent(new Event('resize'))
  }

  // 展开/收起侧边栏后，等待 DOM 更新再统一重置布局位置。
  const handleRetractSidebar = () => {
    state.showSidebar = !state.showSidebar
    nextTick(() => {
      resetLayoutPosition()
    })
  }

  let isResizing = false
  let resizeStartX = 0
  let resizeStartWidth = 0

  // 拖拽缩放时需要读取外层布局宽度，用于限制侧边栏最大值。
  const getLayoutWidth = () => {
    const layoutEl = document.querySelector('.layout')
    return layoutEl ? layoutEl.clientWidth : window.innerWidth
  }

  // 计算当前可允许的侧边栏宽度上下限。
  const getSidebarBounds = () => {
    const layoutWidth = getLayoutWidth()
    const maxAllowed = Math.min(MAX_SIDEBAR_WIDTH, Math.max(0, layoutWidth - MIN_CONTENT_WIDTH))
    const minAllowed = Math.min(MIN_SIDEBAR_WIDTH, maxAllowed)
    return { minAllowed, maxAllowed }
  }

  // 鼠标移动时持续更新侧边栏宽度。
  const handleResizeMove = (event) => {
    if (!isResizing) return
    const nextWidth = resizeStartWidth + (event.clientX - resizeStartX)
    const { minAllowed, maxAllowed } = getSidebarBounds()
    sidebarWidth.value = Math.min(maxAllowed, Math.max(minAllowed, nextWidth))
  }

  // 拖拽结束后移除全局监听，恢复页面可选中文本状态。
  const handleResizeEnd = () => {
    if (!isResizing) return
    isResizing = false
    document.body.style.userSelect = ''
    window.removeEventListener('mousemove', handleResizeMove)
    window.removeEventListener('mouseup', handleResizeEnd)
  }

  // 仅在桌面端允许左键拖拽调整侧边栏宽度。
  const handleResizeStart = (event) => {
    if (isCompact.value) return
    if (event.button !== 0) return
    isResizing = true
    resizeStartX = event.clientX
    resizeStartWidth = sidebarWidth.value
    document.body.style.userSelect = 'none'
    window.addEventListener('mousemove', handleResizeMove)
    window.addEventListener('mouseup', handleResizeEnd)
  }

  // 浏览器宽度变化后，保证侧边栏宽度仍处于合法范围内。
  const clampSidebarWidth = () => {
    if (isCompact.value || !state.showSidebar) return
    const { minAllowed, maxAllowed } = getSidebarBounds()
    if (sidebarWidth.value > maxAllowed) {
      sidebarWidth.value = maxAllowed
    } else if (sidebarWidth.value < minAllowed) {
      sidebarWidth.value = minAllowed
    }
  }

  // 根据断点在宽屏布局与窄屏浮层布局之间切换。
  const syncLayoutMode = () => {
    const compact = window.innerWidth <= COMPACT_BREAKPOINT
    if (compact === isCompact.value) {
      clampSidebarWidth()
      return
    }
    isCompact.value = compact
    state.showSidebar = !compact
    nextTick(() => {
      resetLayoutPosition()
      clampSidebarWidth()
    })
  }

  // 生命周期：挂载时同步模式，卸载时清理监听与拖拽状态。
  onMounted(() => {
    window.addEventListener('resize', syncLayoutMode)
    syncLayoutMode()
  })

  onUnmounted(() => {
    window.removeEventListener('resize', syncLayoutMode)
    handleResizeEnd()
  })
</script>


<style scoped>
  .layout {
    display: flex;
    min-height: 100vh;
    overflow-x: auto;
    overflow-y: hidden;
  }

  .layout--compact {
    overflow-x: hidden;
    overflow-y: auto;
  }

  .layout-sidebar {
    position: relative;
    user-select: auto;
    box-sizing: border-box;
    height: 100vh;
    overflow-y: auto;
    scrollbar-gutter: stable;
    top: 0px;
    background-color: rgb(240, 242, 246);
    color: rgb(49, 51, 63);
    color-scheme: light;
    z-index: 999991;
    width: 300px;
    min-width: 0;
    max-width: 600px;
    transform: translateX(0px);
    transition: transform 300ms, min-width 300ms, max-width 300ms;
  }

  .layout-sidebar-retract {
    position: absolute;
    top: 1rem;
    right: 1rem;
    display: flex;
    z-index: 2;
  }

  .layout-toggle-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2.5rem;
    height: 2.5rem;
    padding: 0;
    border: 1px solid rgba(148, 163, 184, 0.55);
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.92);
    color: #1f2937;
    cursor: pointer;
    box-shadow: 0 8px 18px rgba(15, 23, 42, 0.12);
    transition:
      background-color 0.18s ease,
      border-color 0.18s ease,
      box-shadow 0.18s ease,
      transform 0.18s ease;
    -webkit-tap-highlight-color: transparent;
  }

  .layout-toggle-button:hover {
    background: #ffffff;
    border-color: rgba(100, 116, 139, 0.72);
    box-shadow: 0 10px 22px rgba(15, 23, 42, 0.16);
  }

  .layout-toggle-button:focus-visible {
    outline: 2px solid rgba(59, 130, 246, 0.55);
    outline-offset: 2px;
  }

  .layout-toggle-icon {
    font-size: 1.2rem;
    pointer-events: none;
  }

  .layout-sidebar-resizer {
    position: absolute;
    top: 0;
    right: 0;
    width: 6px;
    height: 100%;
    cursor: col-resize;
    background: transparent;
  }

  .layout-sidebar-resizer:hover {
    background: rgba(0, 0, 0, 0.08);
  }

  .layout-content {
    position: relative;
    flex: 1;
    height: 100vh;
    min-width: 0;
    overflow-y: auto;
    scrollbar-gutter: stable;
    transition: transform 300ms, min-width 300ms, max-width 300ms;
  }

  .layout-content--collapsed {
    padding-left: 2.5rem;
  }

  .layout-content-retract {
    position: absolute;
    top: 1.1rem;
    left: 1rem;
    z-index: 10;
  }

  .layout--compact .layout-sidebar {
    position: fixed;
    top: 0.75rem;
    left: 0.75rem;
    width: min(22rem, calc(100vw - 1.5rem));
    height: auto;
    min-width: 0;
    max-width: calc(100vw - 1.5rem);
    max-height: calc(100vh - 1.5rem);
    overflow-y: auto;
    background: rgba(240, 242, 246, 0.82);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.6);
    border-radius: 16px;
    box-shadow: 0 16px 36px rgba(0, 0, 0, 0.18);
  }

  .layout--compact .layout-sidebar-retract {
    position: sticky;
    top: 1rem;
    display: flex;
    justify-content: flex-end;
    padding-right: 1rem;
    z-index: 2;
  }

  .layout--compact .layout-content {
    width: 100%;
    height: auto;
    min-height: 100vh;
    overflow: visible;
  }

  .layout--compact .layout-content--collapsed {
    padding-left: 0;
    padding-top: 0;
  }

  .layout--compact .layout-content-retract {
    position: fixed;
    top: 1rem;
    left: 1rem;
    z-index: 10;
  }
</style>


