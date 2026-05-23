<template>
  <!-- 公式容器：由 KaTeX 在挂载后直接写入渲染结果。 -->
  <div ref="katexRef" class="katex-container"></div>
</template>

<script setup>
  // 公式渲染组件：统一处理公式字符串与展示模式。
  import { ref, onMounted, watch } from 'vue'
  import katex from 'katex'
  import 'katex/dist/katex.min.css'

  const props = defineProps({
    expression: {
      type: String,
      required: true
    },
    // 是否按块级公式显示。
    displayMode: {
      type: Boolean,
      default: true
    }
  })

  const katexRef = ref(null)

  // 渲染入口：在挂载后或公式内容变化时重绘。
  const renderKaTeX = () => {
    if (!katexRef.value || !props.expression) return

    try {
      // 始终将传入值归一为字符串，避免 KaTeX 因类型不匹配报错。
      const expressionStr = String(props.expression)

      // 调用 KaTeX 原生渲染接口。
      katex.render(expressionStr, katexRef.value, {
        displayMode: props.displayMode,
        throwOnError: false
      })
    } catch (error) {
      console.error('KaTeX 渲染错误:', error)
      if (katexRef.value) {
        katexRef.value.innerHTML = `<span style="color: red;">KaTeX 渲染错误: ${error.message}</span>`
      }
    }
  }

  // 首次挂载后立刻渲染。
  onMounted(() => {
    renderKaTeX()
  })

  // 监听公式内容与显示模式变化，保持渲染结果同步。
  watch([() => props.expression, () => props.displayMode], () => {
    renderKaTeX()
  })
</script>

<style scoped>
  /* 公式较长时允许横向滚动，避免撑破侧边栏。 */
  .katex-container {
    width: 100%;
    overflow-x: auto;
  }
</style>
