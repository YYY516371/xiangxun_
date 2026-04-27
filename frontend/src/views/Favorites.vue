<template>
  <div class="favorites-page">
    <div class="header">
      <el-button @click="$router.back()" type="primary" plain>← 返回</el-button>
      <h1>我的收藏</h1>
      <div class="count">{{ favoritesList.length }} 个村庄</div>
    </div>

    <el-row :gutter="20">
      <el-col :span="12" v-for="v in paginatedFavorites" :key="v.id" style="margin-bottom: 20px;">
        <el-card class="village-card">
          <!-- 卡片主体（点击跳转详情） -->
          <div class="card-content" @click="goDetail(v.id)">
            <img :src="v.image_url || defaultImage" class="village-img" />
            <div class="info">
              <h3>{{ simplifyName(v.name) }}</h3>
              <p class="product">{{ v.product_name || '特色产品' }}</p>
              <p class="location">{{ v.province }} · {{ v.city }} · {{ v.county || '' }}</p>
            </div>
          </div>

          <!-- 百科链接按钮组 -->
          <div class="baike-buttons">
            <el-button link type="primary" size="small" @click.stop="openBaike(v, 0)">
              📖 村庄简介
            </el-button>
            <el-button link type="success" size="small" @click.stop="openBaike(v, 1)">
              🛒 产品介绍
            </el-button>
          </div>

          <!-- 收藏图标（可取消收藏） -->
          <div class="card-footer">
            <el-icon class="favorite-icon" color="#f56c6c" @click.stop="removeFavorite(v.id)">
              <StarFilled />
            </el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 分页组件 -->
    <div class="pagination-row" v-if="favoritesList.length > pageSize">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="favoritesList.length"
        layout="prev, pager, next"
        @current-change="handleCurrentChange"
      />
    </div>

    <div v-if="favoritesList.length === 0" class="empty">
      <el-empty description="暂无收藏，去首页添加吧" />
      <el-button type="primary" @click="$router.push('/')">去首页浏览</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { StarFilled } from '@element-plus/icons-vue'
import axios from 'axios'

const router = useRouter()
const favoritesList = ref([])
const currentPage = ref(1)
const pageSize = ref(6)   // 每页显示6个
const defaultImage = 'https://picsum.photos/id/104/150/150'

// 分页数据
const paginatedFavorites = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return favoritesList.value.slice(start, start + pageSize.value)
})

// 简化村名（去除区镇前缀）
const simplifyName = (fullName) => {
  if (!fullName) return ''
  let name = fullName
  const districtIdx = name.indexOf('区')
  if (districtIdx !== -1) name = name.substring(districtIdx + 1)
  const townIdx = name.indexOf('镇')
  if (townIdx !== -1) name = name.substring(townIdx + 1)
  return name || fullName
}

// 解析百科链接
const parseBaikeUrls = (urls) => {
  if (!urls || urls === 'NaN') return []
  return urls.split(/[,|]/).map(u => u.trim()).filter(u => u.startsWith('http'))
}

// 打开百科
const openBaike = (village, index) => {
  const urls = parseBaikeUrls(village.baike_urls)
  const url = urls[index]
  if (url) {
    window.open(url, '_blank')
  } else {
    ElMessage.warning(index === 0 ? '暂无村庄简介' : '暂无产品介绍')
  }
}

// 取消收藏
const removeFavorite = async (id) => {
  try {
    await axios.post(`/api/villages/${id}/unfavorite`)
    favoritesList.value = favoritesList.value.filter(v => v.id !== id)
    ElMessage.success('已取消收藏')
    // 如果当前页没有数据了，且不是第一页，则回退一页
    if (paginatedFavorites.value.length === 0 && currentPage.value > 1) {
      currentPage.value--
    }
  } catch (error) {
    console.error('取消收藏失败', error)
    ElMessage.error('操作失败，请稍后重试')
  }
}

// 跳转详情
const goDetail = (id) => router.push(`/village/${id}`)

// 分页切换
const handleCurrentChange = (val) => {
  currentPage.value = val
}

// 加载收藏列表（需要从后端获取完整的村庄数据）
const loadFavorites = async () => {
  const token = localStorage.getItem('token')
  if (!token) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  try {
    const res = await axios.get('/api/user/favorites')
    favoritesList.value = res.data
  } catch (error) {
    console.error('加载收藏失败', error)
    ElMessage.error('加载收藏失败，请检查后端接口')
    favoritesList.value = []
  }
}

onMounted(() => {
  loadFavorites()
})
</script>

<style scoped>
.favorites-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}
.header {
  display: flex;
  align-items: baseline;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 24px;
  border-left: 5px solid #e67e22;
  padding-left: 20px;
}
.header h1 {
  font-size: 1.8rem;
  font-weight: 600;
  color: #2b5e2b;
}
.count {
  background: #e8dccc;
  padding: 4px 12px;
  border-radius: 40px;
  font-size: 14px;
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
  gap: 16px;
  padding: 12px;
}
.village-img {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 16px;
}
.info h3 {
  margin: 0 0 5px;
  font-size: 1.2rem;
  color: #2b5e2b;
}
.product {
  color: #e67e22;
  font-weight: bold;
  margin: 5px 0;
}
.location {
  font-size: 12px;
  color: #888;
}
.baike-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 8px;
  padding: 0 12px;
}
.card-footer {
  display: flex;
  justify-content: flex-end;
  padding: 8px 12px;
}
.favorite-icon {
  font-size: 24px;
  cursor: pointer;
  transition: transform 0.2s;
}
.favorite-icon:hover {
  transform: scale(1.1);
}
.pagination-row {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
.empty {
  text-align: center;
  padding: 80px 20px;
}
</style>