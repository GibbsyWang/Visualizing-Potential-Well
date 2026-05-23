// 通用防抖工具：连续触发时仅保留最后一次调用。
export const debounce = (func, delay = 200) => {
  let timeoutId

  return function debounced(...args) {
    const context = this
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => {
      func.apply(context, args)
    }, delay)
  }
}
