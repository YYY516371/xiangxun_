<template>
  <div id="app">
    <div class="nav-bar">
      <router-link to="/">首页</router-link>
      <router-link to="/favorites">我的收藏</router-link>
      <router-link to="/products">产品浏览</router-link>
      <router-link to="/ranking">热门排行榜</router-link>

      <!-- 右侧区域：搜索 + 用户菜单 -->
      <div class="nav-right">
        <!-- 全局搜索组件 -->
        <div class="global-search">
          <transition name="slide-fade">
            <el-input
              v-if="showSearchInput"
              ref="searchInputRef"
              v-model="globalKeyword"
              placeholder="搜索村庄或产品"
              size="small"
              clearable
              @keyup.enter="doSearch"
              @blur="handleBlur"
              class="global-search-input"
            />
          </transition>
          <el-icon class="search-icon" @click="toggleSearch"><Search /></el-icon>
        </div>

        <!-- 登录/用户菜单 -->
        <div class="user-menu" v-if="userStore.token">
          <el-dropdown @command="handleCommand">
           <span class="el-dropdown-link">
  {{ userStore.user?.nickname || userStore.user?.username || '用户' }}
  <el-icon><ArrowDown /></el-icon>
</span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        <router-link v-else to="/login" class="login-link">登录/注册</router-link>
      </div>
    </div>

    <router-view :key="$route.fullPath" v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup>
import { useUserStore } from './stores/user'
import { onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowDown, Search } from '@element-plus/icons-vue'
import { ref, nextTick } from 'vue'

const userStore = useUserStore()
const router = useRouter()

// 全局搜索状态
const showSearchInput = ref(false)
const globalKeyword = ref('')
const searchInputRef = ref(null)

const toggleSearch = () => {
  showSearchInput.value = !showSearchInput.value
  if (showSearchInput.value) {
    nextTick(() => {
      searchInputRef.value?.focus()
    })
  } else {
    globalKeyword.value = ''
  }
}

const doSearch = () => {
  if (globalKeyword.value.trim()) {
    router.push(`/search?keyword=${encodeURIComponent(globalKeyword.value.trim())}`)
    showSearchInput.value = false
    globalKeyword.value = ''
  }
}

const handleBlur = () => {
  setTimeout(() => {
    if (!searchInputRef.value?.isFocused) {
      showSearchInput.value = false
      globalKeyword.value = ''
    }
  }, 150)
}

const handleCommand = (command) => {
  if (command === 'profile') {
    router.push('/person')
  } else if (command === 'logout') {
    userStore.logout()
    ElMessage.success('已退出登录')
    router.push('/')
  }
}
// 页面加载时获取用户详细信息（昵称、头像等）
onMounted(async () => {
  const token = localStorage.getItem('token')
  if (token) {
    try {
      const res = await axios.get('/api/user/profile')
      userStore.setUser({
        ...userStore.user,
        ...res.data
      })
    } catch (error) {
      console.error('获取用户信息失败', error)
    }
  }
})
</script>

<style>
/* ========== 全局 CSS 变量 ========== */
:root {
  --primary-green: #2b5e2b;
  --primary-dark: #1e3f1e;
  --primary-light: #4c8b4c;
  --accent-orange: #e67e22;
  --accent-warm: #f5a65b;
  --bg-light: #fef9ef;
  --bg-gradient: linear-gradient(135deg, #fef9ef 0%, #f0ede5 100%);
  --card-bg: rgba(255, 255, 255, 0.85);
  --card-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.02);
  --card-hover-shadow: 0 20px 30px -12px rgba(43, 94, 43, 0.15);
  --nav-bg: rgba(43, 94, 43, 0.92);
  --transition-default: all 0.25s cubic-bezier(0.2, 0.9, 0.4, 1.1);
}

html {
  overflow-y: scroll;
}

/* 平滑滚动 */
html {
  scroll-behavior: smooth;
}

/* ========== 基础重置 ========== */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', 'Roboto', 'Noto Sans', system-ui, -apple-system, sans-serif;
  background: var(--bg-gradient);
  color: #2c3e2f;
  line-height: 1.5;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ========== 滚动条美化 ========== */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: #e8e0d5;
  border-radius: 10px;
}
::-webkit-scrollbar-thumb {
  background: #9b7b5c;
  border-radius: 10px;
  transition: background 0.2s;
}
::-webkit-scrollbar-thumb:hover {
  background: #7a5a3e;
}

/* ========== 路由过渡动画 ========== */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ========== 导航栏 ========== */
.nav-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  background: var(--nav-bg);
  backdrop-filter: blur(12px);
  padding: 12px 32px;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.nav-bar a {
  color: white;
  text-decoration: none;
  font-weight: 500;
  letter-spacing: 0.3px;
  padding: 6px 12px;
  border-radius: 40px;
  transition: var(--transition-default);
  position: relative;
}

.nav-bar a::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 50%;
  width: 0;
  height: 2px;
  background: var(--accent-orange);
  transition: all 0.2s;
  transform: translateX(-50%);
}

.nav-bar a:hover::after {
  width: 70%;
}

.nav-bar a:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateY(-1px);
}

/* 右侧区域（搜索+用户）整体靠右 */
.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-left: auto;
}

/* 全局搜索样式 */
.global-search {
  display: flex;
  align-items: center;
  gap: 8px;
}
.search-icon {
  font-size: 20px;
  cursor: pointer;
  color: white !important;
  transition: transform 0.2s;
}
.search-icon:hover {
  transform: scale(1.1);
}
.global-search-input {
  width: 200px;
  transition: all 0.3s;
}
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.2s ease;
}
.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateX(20px);
  opacity: 0;
}

.user-menu {
  cursor: pointer;
  color: white;
}
.el-dropdown-link {
  color: white;
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.12);
  padding: 6px 14px;
  border-radius: 40px;
  transition: var(--transition-default);
}
.el-dropdown-link:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
}

.login-link {
  /* 无需额外 margin，因为父容器 .nav-right 已经靠右 */
}

/* ========== 全局按钮 ========== */
.el-button {
  border-radius: 40px !important;
  transition: var(--transition-default) !important;
  font-weight: 500;
  letter-spacing: 0.3px;
}

.el-button--primary {
  background-color: var(--primary-green);
  border-color: var(--primary-green);
}

.el-button--primary:hover {
  background-color: var(--primary-dark);
  border-color: var(--primary-dark);
  transform: translateY(-2px);
  box-shadow: 0 6px 14px rgba(43, 94, 43, 0.25);
}

.el-button.is-plain {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(4px);
  border: 1px solid rgba(219, 203, 184, 0.6);
}

.el-button.is-plain:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-2px);
}

/* ========== 卡片 ========== */
.el-card {
  background: var(--card-bg) !important;
  backdrop-filter: blur(4px);
  border: 1px solid rgba(219, 203, 184, 0.3) !important;
  border-radius: 24px !important;
  box-shadow: var(--card-shadow);
  transition: var(--transition-default);
}

.el-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--card-hover-shadow);
}

.el-tag {
  border-radius: 40px;
  padding: 0 12px;
  font-weight: 500;
}

.el-table {
  --el-table-bg-color: rgba(255, 255, 245, 0.7);
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(43, 94, 43, 0.08);
  border-radius: 24px;
  overflow: hidden;
  backdrop-filter: blur(4px);
}

.el-table th.el-table__cell {
  font-weight: 600;
  color: var(--primary-dark);
}

/* ========== 响应式 ========== */
@media (max-width: 768px) {
  .nav-bar {
    flex-wrap: wrap;
    justify-content: center;
    gap: 12px;
    padding: 12px 16px;
  }
  .nav-bar a {
    font-size: 14px;
    padding: 4px 10px;
  }
  .nav-right {
    margin-left: 0;
    width: 100%;
    justify-content: flex-end;
  }
  .global-search-input {
    width: 150px;
  }
}

/* ========== 加载状态 ========== */
.el-loading-mask {
  background-color: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(2px);
}

.el-empty__image {
  opacity: 0.7;
}
.el-empty__description p {
  color: #8b6b4a;
}

/* ========== 模拟数据提示条 ========== */
.mock-banner {
  background: #fff3e0;
  color: #e6a23c;
  text-align: center;
  padding: 8px;
  font-size: 14px;
  border-bottom: 1px solid #ffe0b3;
  backdrop-filter: blur(4px);
  position: sticky;
  top: 60px;
  z-index: 99;
}
</style>