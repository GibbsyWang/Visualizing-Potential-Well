<template>
  <!-- 返回首页按钮：放在各维度页面的侧边栏底部。 -->
  <div class="back">
    <AppButton @click="handleBackToHome">back to home</AppButton>
  </div>
</template>

<script setup>
  // 组件职责很单一：仅负责执行回到首页的跳转。
  import AppButton from '../btn/AppButton.vue'
  import { useRouter } from 'vue-router'

  const router = useRouter()

  const handleBackToHome = () => {
    router.push({ name: 'home' })
  }
</script>

<style scoped>
  /* 让返回按钮始终占满侧边栏可用宽度。 */
  .back {
    margin-bottom: 1rem;
    width: 100%;
    text-align: center;
  }

  .back :deep(.button) {
    width: 100%;
    justify-content: center;
  }

</style>
