<template>
  <div class="person-page">
    <div class="header">
      <el-button @click="$router.back()" type="primary" plain>← 返回</el-button>
      <h1>个人中心</h1>
    </div>

    <!-- 用户信息卡片 -->
    <el-card class="profile-card">
      <div class="profile-header">
        <el-avatar :size="80" :src="userInfo.avatar || 'https://picsum.photos/id/64/80/80'" />
        <div class="info">
          <h2>{{ userInfo.username || '游客' }}</h2>
          <p>注册时间：{{ userInfo.regtime || '未知' }}</p>
        </div>
      </div>
    </el-card>

    <!-- 三个标签页 -->
    <el-tabs v-model="activeTab" class="tabs">
      <el-tab-pane label="我的收藏" name="favorites">
        <el-row :gutter="20">
          <el-col :span="12" v-for="v in paginatedFavorites" :key="v.id" style="margin-bottom: 20px;">
            <el-card class="village-card">
              <div class="card-content" @click="goDetail(v.id)">
                <img src="https://picsum.photos/id/104/100/100" class="village-img" />
                <div class="info">
                  <h3>{{ simplifyName(v.name) }}</h3>
                  <p>{{ v.product_name || '特色产品' }}</p>
                </div>
              </div>
              <div class="card-actions">
                <el-button type="danger" size="small" @click.stop="removeFavorite(v.id)">取消收藏</el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <div class="pagination" v-if="favoritesList.length > pageSize">
          <el-pagination
            v-model:current-page="favPage"
            :page-size="pageSize"
            :total="favoritesList.length"
            layout="prev, pager, next"
            @current-change="handleFavPageChange"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane label="我的想去" name="wants">
        <el-row :gutter="20">
          <el-col :span="12" v-for="v in paginatedWants" :key="v.id" style="margin-bottom: 20px;">
            <el-card class="village-card">
              <div class="card-content" @click="goDetail(v.id)">
                <img src="https://picsum.photos/id/104/100/100" class="village-img" />
                <div class="info">
                  <h3>{{ simplifyName(v.name) }}</h3>
                  <p>{{ v.product_name || '特色产品' }}</p>
                </div>
              </div>
              <div class="card-actions">
                <el-button type="danger" size="small" @click.stop="removeWant(v.id)">取消想去</el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <div class="pagination" v-if="wantsList.length > pageSize">
          <el-pagination
            v-model:current-page="wantPage"
            :page-size="pageSize"
            :total="wantsList.length"
            layout="prev, pager, next"
            @current-change="handleWantPageChange"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane label="我的点赞" name="likes">
        <el-row :gutter="20">
          <el-col :span="12" v-for="v in paginatedLikes" :key="v.id" style="margin-bottom: 20px;">
            <el-card class="village-card">
              <div class="card-content" @click="goDetail(v.id)">
                <img src="https://picsum.photos/id/104/100/100" class="village-img" />
                <div class="info">
                  <h3>{{ simplifyName(v.name) }}</h3>
                  <p>{{ v.product_name || '特色产品' }}</p>
                </div>
              </div>
              <div class="card-actions">
                <el-button type="danger" size="small" @click.stop="removeLike(v.id)">取消点赞</el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <div class="pagination" v-if="likesList.length > pageSize">
          <el-pagination
            v-model:current-page="likePage"
            :page-size="pageSize"
            :total="likesList.length"
            layout="prev, pager, next"
            @current-change="handleLikePageChange"
          />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const activeTab = ref('favorites')

// 用户信息
const userInfo = ref({})

// 收藏列表
const favoritesList = ref([])
const favPage = ref(1)
const pageSize = ref(6) // 每页显示6条
const paginatedFavorites = computed(() => {
  const start = (favPage.value - 1) * pageSize.value
  return favoritesList.value.slice(start, start + pageSize.value)
})

// 想去列表
const wantsList = ref([])
const wantPage = ref(1)
const paginatedWants = computed(() => {
  const start = (wantPage.value - 1) * pageSize.value
  return wantsList.value.slice(start, start + pageSize.value)
})

// 点赞列表
const likesList = ref([])
const likePage = ref(1)
const paginatedLikes = computed(() => {
  const start = (likePage.value - 1) * pageSize.value
  return likesList.value.slice(start, start + pageSize.value)
})

// 简化村名（复用）
const simplifyName = (fullName) => {
  if (!fullName) return ''
  let name = fullName
  const districtIdx = name.indexOf('区')
  if (districtIdx !== -1) name = name.substring(districtIdx + 1)
  const townIdx = name.indexOf('镇')
  if (townIdx !== -1) name = name.substring(townIdx + 1)
  return name || fullName
}

// 分页切换
const handleFavPageChange = (val) => { favPage.value = val }
const handleWantPageChange = (val) => { wantPage.value = val }
const handleLikePageChange = (val) => { likePage.value = val }

// 取消收藏
const removeFavorite = async (id) => {
  try {
    await axios.post(`/api/villages/${id}/unfavorite`)
    favoritesList.value = favoritesList.value.filter(v => v.id !== id)
    ElMessage.success('已取消收藏')
    // 如果当前页没有数据了，自动回退一页
    if (paginatedFavorites.value.length === 0 && favPage.value > 1) {
      favPage.value--
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 取消想去
const removeWant = async (id) => {
  try {
    await axios.post(`/api/villages/${id}/unwant`)
    wantsList.value = wantsList.value.filter(v => v.id !== id)
    ElMessage.success('已取消想去')
    if (paginatedWants.value.length === 0 && wantPage.value > 1) {
      wantPage.value--
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 取消点赞
const removeLike = async (id) => {
  try {
    await axios.post(`/api/villages/${id}/unlike`)
    likesList.value = likesList.value.filter(v => v.id !== id)
    ElMessage.success('已取消点赞')
    if (paginatedLikes.value.length === 0 && likePage.value > 1) {
      likePage.value--
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 跳转详情
const goDetail = (id) => {
  router.push(`/village/${id}`)
}

// 加载用户个人数据
const loadUserData = async () => {
  if (!userStore.token) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  try {
    // 获取用户信息
    const profileRes = await axios.get('/api/user/profile')
    userInfo.value = profileRes.data

    // 获取收藏列表
    const favRes = await axios.get('/api/user/favorites')
    favoritesList.value = favRes.data

    // 获取想去列表
    const wantRes = await axios.get('/api/user/wants')
    wantsList.value = wantRes.data

    // 获取点赞列表
    const likeRes = await axios.get('/api/user/likes')
    likesList.value = likeRes.data
  } catch (error) {
    console.error('加载个人数据失败', error)
    ElMessage.error('加载个人数据失败，请检查后端接口')
    // 如果后端接口未实现，可以使用模拟数据测试
    if (error.response?.status === 404) {
      userInfo.value = { username: userStore.user?.username || '测试用户', regtime: '2026-01-01' }
      favoritesList.value = []
      wantsList.value = []
      likesList.value = []
    }
  }
}

onMounted(() => {
  loadUserData()
})
</script>

<style scoped>
.person-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}
.header {
  display: flex;
  align-items: baseline;
  gap: 20px;
  margin-bottom: 24px;
  border-left: 5px solid #e67e22;
  padding-left: 20px;
}
.header h1 {
  font-size: 1.8rem;
  font-weight: 600;
  color: #2b5e2b;
}
.profile-card {
  margin-bottom: 24px;
}
.profile-header {
  display: flex;
  gap: 20px;
  align-items: center;
}
.profile-header .info h2 {
  margin: 0;
}
.village-card {
  cursor: pointer;
  transition: all 0.25s ease;
  border-radius: 24px;
  overflow: hidden;
  background: rgba(255, 255, 245, 0.8);
  backdrop-filter: blur(4px);
}
.village-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 30px -12px rgba(43, 94, 43, 0.15);
}
.card-content {
  display: flex;
  gap: 12px;
  padding: 12px;
}
.village-img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 12px;
}
.info h3 {
  margin: 0 0 4px;
  font-size: 1rem;
}
.card-actions {
  text-align: right;
  padding: 0 12px 12px 0;
}
.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>