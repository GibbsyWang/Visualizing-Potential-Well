# Visualizing Potential Well

基于 Vue 3 + Vite 的 n 维无限深势阱可视化应用

## 版本信息

- 当前版本：`V1.0.0`

## 作者

- Lequan Wang
- Haibei Li

## 主要功能

- `1D` 页面：Canvas 绘制波函数、概率密度与能级联动图，支持图片导出。
- `2D` 页面：Plotly 展示波函数曲面、概率密度曲面和能级柱状图，Canvas绘制能级热力图。
- `3D` 页面：Plotly 展示三维波函数点云与概率密度点云。
- 统一布局：支持宽屏/窄屏侧边栏切换与参数面板交互。

## 技术栈

- `Vue 3`
- `Vue Router`
- `Vite`
- `Ant Design Vue`
- `Plotly.js`
- `KaTeX`
- `html2canvas`
- `Electron`

## 项目结构

```text
src/
  components/
    backToHome/
    btn/
    katex/
    layout/
  pages/
    home/
    1d/
    2d/
    3d/
  routers/
  utils/
  App.vue
  main.js
  style.css
electron/
```

## 开发说明

当前版本release文件夹内包含Windows可执行程序(.exe)，可直接双击打开

### 环境要求

- `Node.js >= 18`
- `npm >= 9`

### 安装依赖

```bash
npm install
```

### 本地开发（Web）

```bash
npm run dev
```

### 本地开发（桌面联调）

```bash
npm run dev:desktop
```

### 构建 Web

```bash
npm run build
```

### 打包 Windows 免安装版

```bash
npm run build:desktop
```
