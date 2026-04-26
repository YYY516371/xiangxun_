<template>
  <div class="search-page">
    <div class="header">
      <el-button @click="$router.back()" type="primary" plain>← 返回</el-button>
      <h1>搜索结果：{{ keyword }}</h1>
      <div class="count">{{ villages.length }} 个村庄</div>
    </div>

    <el-row :gutter="20">
      <el-col :span="12" v-for="v in villages" :key="v.id" style="margin-bottom: 20px;">
        <el-card class="village-card" @click="goDetail(v.id)">
          <div class="card-content">
            <img :src="v.image_url || defaultImage" class="village-img" />
            <div class="info">
              <h3>{{ simplifyName(v.name) }}</h3>
              <p class="product">{{ v.product_name || '特色产品' }}</p>
              <p class="location">{{ v.province }} · {{ v.city }}</p>
            </div>
          </div>
          <!-- 百科链接等（可选） -->
          <div class="baike-buttons">
            <el-button link type="primary" size="small" @click.stop="openBaike(v, 0)">📖 村庄简介</el-button>
            <el-button link type="success" size="small" @click.stop="openBaike(v, 1)">🛒 产品介绍</el-button>
          </div>
          <div class="card-footer">
            <el-icon class="favorite-icon" :color="isFavorited(v.id) ? '#f56c6c' : '#999'" @click.stop="toggleFavorite(v.id)">
              <StarFilled v-if="isFavorited(v.id)" />
              <Star v-else />
            </el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div v-if="villages.length === 0" class="empty">未找到相关村庄或产品</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Star, StarFilled } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const keyword = route.query.keyword || ''
const villages = ref([])
const defaultImage = 'https://picsum.photos/id/104/150/150'

// 复用已实现的简化村名、收藏、百科等函数（可从 ProvincePage 复制）
const simplifyName = (fullName) => {
  if (!fullName) return ''
  let name = fullName
  const districtIdx = name.indexOf('区')
  if (districtIdx !== -1) name = name.substring(districtIdx + 1)
  const townIdx = name.indexOf('镇')
  if (townIdx !== -1) name = name.substring(townIdx + 1)
  return name || fullName
}

const parseBaikeUrls = (urls) => {
  if (!urls || urls === 'NaN') return []
  const splitUrls = urls.split(/[,|]/).map(u => u.trim())
  return splitUrls.filter(u => u.startsWith('http'))
}

const isFavorited = (id) => {
  const favs = JSON.parse(localStorage.getItem('favoriteVillages') || '[]')
  return favs.includes(id)
}

const toggleFavorite = (id) => {
  let favs = JSON.parse(localStorage.getItem('favoriteVillages') || '[]')
  if (favs.includes(id)) {
    favs = favs.filter(i => i !== id)
    ElMessage.success('已取消收藏')
  } else {
    favs.push(id)
    ElMessage.success('已添加收藏')
  }
  localStorage.setItem('favoriteVillages', JSON.stringify(favs))
}

const openBaike = (village, index) => {
  const urls = parseBaikeUrls(village.baike_urls)
  const url = urls[index]
  if (url) {
    window.open(url, '_blank')
  } else {
    ElMessage.warning(index === 0 ? '暂无村庄简介' : '暂无产品介绍')
  }
}

const goDetail = (id) => router.push(`/village/${id}`)

const loadSearch = async () => {
  if (!keyword) return
  try {
    const res = await axios.get(`/api/villages?keyword=${keyword}`)
    villages.value = res.data
  } catch (error) {
    console.error('搜索失败', error)
    villages.value = []
  }
}

onMounted(() => {
  loadSearch()
})
</script>

<style scoped>
/* 复用与 ProvincePage 相同的卡片样式，可复制之前的卡片样式 */
.search-page {
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
.count {
  background: #e8dccc;
  padding: 4px 12px;
  border-radius: 40px;
  font-size: 0.85rem;
}
/* 卡片样式（精简） */
.village-card { cursor: pointer; transition: 0.25s; border-radius: 24px; background: rgba(255,255,245,0.8); backdrop-filter: blur(4px); }
.village-card:hover { transform: translateY(-5px); box-shadow: 0 20px 30px -12px rgba(43,94,43,0.15); }
.card-content { display: flex; gap: 16px; padding: 12px; }
.village-img { width: 100px; height: 100px; object-fit: cover; border-radius: 16px; }
.info h3 { margin: 0 0 5px; font-size: 1.2rem; color: #2b5e2b; }
.product { color: #e67e22; font-weight: bold; margin: 5px 0; }
.location { font-size: 12px; color: #888; }
.baike-buttons { display: flex; gap: 12px; justify-content: center; margin-top: 8px; }
.card-footer { display: flex; justify-content: flex-end; padding: 8px 12px; }
.favorite-icon { font-size: 24px; cursor: pointer; transition: transform 0.2s; }
.favorite-icon:hover { transform: scale(1.1); }
.empty { text-align: center; padding: 50px; color: #999; }
</style>