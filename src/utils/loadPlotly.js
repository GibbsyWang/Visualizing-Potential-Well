// 延迟加载 Plotly：多个页面共用同一个 Promise，避免重复下载。
let plotlyPromise

export const loadPlotly = async () => {
  if (!plotlyPromise) {
    plotlyPromise = import('plotly.js-dist-min').then((module) => module.default)
  }

  return plotlyPromise
}
