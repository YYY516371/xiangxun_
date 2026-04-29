<template>
  <div class="search-page">
    <div class="header">
      <el-button @click="$router.back()" type="primary" plain>← 返回</el-button>
      <h1>搜索结果：{{ keyword }}</h1>
      <div class="count">共 {{ villages.length }} 个村庄</div>
    </div>

    <el-row :gutter="20">
      <el-col :span="12" v-for="v in paginatedVillages" :key="v.id" style="margin-bottom: 20px;">
        <el-card class="village-card">
          <div class="card-content" @click="goDetail(v.id)">
            <img :src="v.image_url || defaultImage" class="village-img" />
            <div class="info">
              <h3>{{ simplifyName(v.name) }}</h3>
              <p class="product"><strong>产品：</strong>{{ v.product_name || '无' }}</p>
              <p class="sub-category"><strong>种类：</strong>{{ v.sub_category || '无' }}</p>
              <p class="location"><strong>地区：</strong>{{ v.province }} · {{ v.city }}</p>
            </div>
          </div>
          <div class="baike-buttons">
         <el-button link type="primary" size="small" @click="openBaike(v, 0)">
            📖 村庄简介
        </el-button>
      <el-button link type="success" size="small" @click="openBaike(v, 1)">
        🛒 产品介绍
    </el-button>
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

    <!-- 分页组件 -->
    <div class="pagination-row" v-if="villages.length > pageSize">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[6, 12, 18, 24]"
        :total="villages.length"
        layout="prev, pager, next"
        @current-change="handleCurrentChange"
      />
    </div>

    <div v-if="villages.length === 0" class="empty">未找到相关村庄或产品</div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Star, StarFilled } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const keyword = route.query.keyword || ''
const villages = ref([])
const currentPage = ref(1)
const pageSize = ref(6)
const defaultImage = 'https://picsum.photos/id/104/150/150'
const favoriteIds = ref([])

const paginatedVillages = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return villages.value.slice(start, start + pageSize.value)
})

const handleCurrentChange = (val) => { currentPage.value = val }

// 辅助函数（与省份页相同）
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
  return urls.split(/[,|]/).map(u => u.trim()).filter(u => u.startsWith('http'))
}

const isFavorited = (id) => favoriteIds.value.includes(id)

const toggleFavorite = (id) => {
  const index = favoriteIds.value.indexOf(id)
  if (index !== -1) {
    favoriteIds.value.splice(index, 1)
    ElMessage.success('已取消收藏')
  } else {
    favoriteIds.value.push(id)
    ElMessage.success('已添加收藏')
  }
  localStorage.setItem('favoriteVillages', JSON.stringify(favoriteIds.value))
}

// 将 baike_urls 按竖线分割成数组，过滤无效链接
const getBaikeLinks = (urls) => {
  if (!urls || urls === 'NaN') return []
  return urls.split('|').filter(u => u && u.trim().startsWith('http'))
}

// 打开百科链接，index 0 = 村庄简介，1 = 产品介绍
const openBaike = (village, index) => {
  const links = getBaikeLinks(village.baike_urls)
  const url = links[index]
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
  const favs = JSON.parse(localStorage.getItem('favoriteVillages') || '[]')
  favoriteIds.value = favs
})
</script>

<style scoped>
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
.product, .sub-category, .location {
  margin: 4px 0;
  font-size: 13px;
}
.baike-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 8px;
}
.card-footer {
  display: flex;
  justify-content: flex-end;
  padding: 8px 12px;
}
.favorite-icon {
  font-size: 24px;
  cursor: pointer;
}
.empty {
  text-align: center;
  padding: 50px;
  color: #999;
}
.pagination-row {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>