<template>
  <!-- 统一按钮外壳：具体行为与内容由外部组件传入。 -->
  <button v-bind="$attrs" class="button">
    <slot></slot>
  </button>
</template>
<style scoped>
  /* 基础按钮样式：供首页、返回按钮和操作按钮复用。 */
  .button {
    display: inline-flex;
    -webkit-box-align: center;
    align-items: center;
    -webkit-box-pack: center;
    justify-content: center;
    font-weight: 400;
    padding: 0.25rem 0.75rem;
    border-radius: 0.5rem;
    min-height: 2.5rem;
    margin: 0px;
    line-height: 1.6;
    text-transform: none;
    color: #333;
    cursor: pointer;
    user-select: none;
    background-color: rgb(249, 249, 251);
    border: 1px solid rgba(49, 51, 63, 0.2);
    transition: all 0.3s ease;
    outline: none;
  }

  .button:hover {
    background-color: #f0f0f0;
    border-color: #d0d0d0;
  }
</style>
