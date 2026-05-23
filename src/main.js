// 应用入口：挂载全局样式、路由与 Ant Design Vue。
import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import appRouter from './routers/appRouter'
import 'ant-design-vue/dist/reset.css'

const app = createApp(App)

app.use(appRouter)
app.mount('#app')
