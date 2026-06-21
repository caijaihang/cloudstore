import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Upload from '../views/Upload.vue'
import Manage from '../views/Manage.vue'
import Download from '../views/Download.vue'
import Help from '../views/Help.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/upload', name: 'Upload', component: Upload },
  { path: '/manage', name: 'Manage', component: Manage },
  { path: '/download/:fileId', name: 'Download', component: Download },
  { path: '/help', name: 'Help', component: Help },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
