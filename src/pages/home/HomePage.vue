<template>
  <!-- 首页：展示项目标题与 1D / 2D / 3D 三个入口卡片。 -->
  <div class="container">
    <div class="hero-panel">
      <h1 class="title">
        <span class="red">Visualizing</span> n-Dimensional Infinite Potential Well
      </h1>
      <h2 class="subtitle">
        <span class="dimgray">By Lequan Wang and Haibei Li</span>
      </h2>
      <p class="intro">
        Choose a dimension to explore the infinite potential well through tailored visualizations.
      </p>

      <div class="home-page">
        <div class="buttons-container">
          <AppButton
            v-for="card in dimensionCards"
            :key="card.page"
            class="dimension-card"
            :style="{ '--card-accent': card.accent }"
            @click="gotoPage(card.page)"
          >
            <span
              class="dimension-card-media"
              :style="{ backgroundImage: `url(${card.image})` }"
            ></span>
            <span class="dimension-card-overlay"></span>
            <span class="dimension-card-bottom">
              <span class="dimension-card-content">
                <span class="dimension-card-title">{{ card.title }}</span>
              </span>
              <span class="dimension-card-footer">
                <span class="dimension-card-description">{{ card.description }}</span>
                <span class="dimension-card-action">Open</span>
              </span>
            </span>
          </AppButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
  // 首页仅负责组织卡片数据并执行页面跳转。
  import { useRouter } from 'vue-router'
  import AppButton from '@/components/btn/AppButton.vue'
  import image1d from './1d.png'
  import image2d from './2d.png'
  import image3d from './3d.png'

  const router = useRouter()

  // 卡片配置：统一维护标题、描述、配图与强调色。
  const dimensionCards = [
    {
      page: '1',
      title: '1-Dimensional',
      description: 'Wavefunctions and energy levels along a single axis.',
      image: image1d,
      accent: 'rgba(50, 89, 206, 0.82)'
    },
    {
      page: '2',
      title: '2-Dimensional',
      description: 'Surface views of wavefunctions across the square well.',
      image: image2d,
      accent: 'rgba(23, 130, 127, 0.82)'
    },
    {
      page: '3',
      title: '3-Dimensional',
      description: 'Point-cloud views of wavefunction structure in volume.',
      image: image3d,
      accent: 'rgba(81, 41, 129, 0.84)'
    }
  ]

  function gotoPage(page) {
    router.push(`/${page}`)
  }
</script>

<style scoped>
  @import './style.css';
</style>
