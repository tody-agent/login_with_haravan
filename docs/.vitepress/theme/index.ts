import DefaultTheme from 'vitepress/theme'
import UatChecklist from './UatChecklist.vue'
import './uat-checklist.css'

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('UatChecklist', UatChecklist)
  }
}
