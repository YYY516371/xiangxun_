<template>
  <div class="products-page">
    <div class="header">
      <el-button @click="$router.back()" type="primary" plain>← 返回</el-button>
      <h1>产品浏览</h1>
    </div>

    <!-- 一级产业筛选 -->
    <div class="filter-row">
      <el-radio-group v-model="selectedIndustry" size="small" @change="onIndustryChange">
        <el-radio-button label="">全部产业</el-radio-button>
        <el-radio-button v-for="ind in industryList" :key="ind" :label="ind">{{ ind }}</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 二级产品筛选（动态） -->
    <div v-if="subCategoryList.length" class="filter-row">
      <el-radio-group v-model="selectedSubCategory" size="small">
        <el-radio-button label="">全部产品</el-radio-button>
        <el-radio-button v-for="cat in subCategoryList" :key="cat" :label="cat">{{ cat }}</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 地区筛选：省 → 市 → 区/镇 级联 -->
    <div class="filter-row">
      <el-cascader
        v-model="selectedRegion"
        :options="regionOptions"
        :props="{ expandTrigger: 'hover', label: 'name', value: 'name', children: 'children', checkStrictly: true }"
        placeholder="请选择省/市/区/镇"
        clearable
        size="small"
        style="width: 260px;"
      />
    </div>

    <!-- 村庄卡片网格 -->
    <el-row :gutter="20">
      <el-col :span="12" v-for="v in paginatedVillages" :key="v.id" style="margin-bottom: 20px;">
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

         <div class="baike-buttons">
       <el-button link type="primary" size="small" @click="openBaike(v, 0)">
        📖 村庄简介
     </el-button>
  <el-button link type="success" size="small" @click="openBaike(v, 1)">
    🛒 产品介绍
 </el-button>
</div>

          <!-- 收藏图标 -->
          <div class="card-footer">
            <el-icon class="favorite-icon" :color="favoriteIds.includes(v.id) ? '#f56c6c' : '#999'" @click.stop="toggleFavorite(v.id)">
              <StarFilled v-if="favoriteIds.includes(v.id)" />
              <Star v-else />
            </el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 分页组件 -->
    <div class="pagination-row">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[6, 12, 18, 24]"
        :total="filteredVillages.length"
        layout="total, sizes, prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <div v-if="filteredVillages.length === 0" class="empty">暂无村庄数据</div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Star, StarFilled } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const isLoggedIn = computed(() => !!userStore.token)

// 预设产业列表（用于“其他”归类）
const predefinedIndustries = ['茶', '果', '药', '渔', '蔬', '花', '畜', '粮']

const allVillages = ref([])
const usingMockData = ref(false)
const favoriteIds = ref([])          // 收藏的村庄 ID 列表（响应式）
const defaultImage = 'https://picsum.photos/id/104/150/150'

// 筛选状态
const selectedIndustry = ref('')
const selectedSubCategory = ref('')
const selectedRegion = ref([])
const regionOptions = ref([])

// 分页
const currentPage = ref(1)
const pageSize = ref(6)

// 辅助函数
const parseDistrictTown = (fullName) => {
  let district = null, town = null
  const districtMatch = fullName.match(/(.+?区)/)
  if (districtMatch) district = districtMatch[1]
  const townMatch = fullName.match(/(.+?镇)/)
  if (townMatch) town = townMatch[1]
  return { district, town }
}

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

// 构建全国地区级联选项
const buildRegionOptions = () => {
  const provinceMap = new Map()
  allVillages.value.forEach(v => {
    const province = v.province || '未知'
    const city = v.city || '未知'
    const { district, town } = parseDistrictTown(v.name)
    if (!provinceMap.has(province)) provinceMap.set(province, new Map())
    const cityMap = provinceMap.get(province)
    if (!cityMap.has(city)) cityMap.set(city, new Map())
    const districtMap = cityMap.get(city)
    if (district) {
      if (!districtMap.has(district)) districtMap.set(district, new Set())
      if (town) districtMap.get(district).add(town)
    } else if (town) {
      if (!districtMap.has('')) districtMap.set('', new Set())
      districtMap.get('').add(town)
    }
  })
  const options = []
  for (let [province, cityMap] of provinceMap.entries()) {
    const provinceNode = { name: province, children: [] }
    for (let [city, districtMap] of cityMap.entries()) {
      const cityNode = { name: city, children: [] }
      for (let [district, towns] of districtMap.entries()) {
        const districtNode = { name: district || '直接镇', children: [] }
        for (let town of towns) districtNode.children.push({ name: town })
        cityNode.children.push(districtNode)
      }
      provinceNode.children.push(cityNode)
    }
    options.push(provinceNode)
  }
  return options
}

// 加载全国村庄数据
const loadVillages = async () => {
  try {
    const res = await axios.get('/api/villages')
    allVillages.value = res.data
    usingMockData.value = false
    regionOptions.value = buildRegionOptions()
  } catch (error) {
    console.error('加载村庄数据失败，使用模拟数据', error)
    usingMockData.value = true
    allVillages.value = []
    regionOptions.value = []
  }
}

// 加载用户收藏列表（从后端）
const loadFavorites = async () => {
  if (!isLoggedIn.value) return
  try {
    const res = await axios.get('/api/user/favorites')
    favoriteIds.value = res.data.map(v => v.id)
  } catch (error) {
    console.error('加载收藏列表失败', error)
    favoriteIds.value = []
  }
}

// 切换收藏（调用真实后端接口）
const toggleFavorite = async (id) => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  try {
    if (favoriteIds.value.includes(id)) {
      await axios.post(`/api/villages/${id}/unfavorite`)
      favoriteIds.value = favoriteIds.value.filter(i => i !== id)
      ElMessage.success('已取消收藏')
    } else {
      await axios.post(`/api/villages/${id}/favorite`)
      favoriteIds.value.push(id)
      ElMessage.success('收藏成功')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  }
}

// 计算属性
const industryList = computed(() => {
  const types = new Set()
  allVillages.value.forEach(v => {
    let ind = v.industry_type || '其他'
    if (!predefinedIndustries.includes(ind)) ind = '其他'
    types.add(ind)
  })
  return Array.from(types).sort()
})

const getBaseVillagesByIndustry = (industry) => {
  if (industry === '其他') {
    return allVillages.value.filter(v => !predefinedIndustries.includes(v.industry_type))
  } else {
    return allVillages.value.filter(v => v.industry_type === industry)
  }
}

const subCategoryList = computed(() => {
  if (!selectedIndustry.value) return []
  const base = getBaseVillagesByIndustry(selectedIndustry.value)
  const cats = new Set()
  base.forEach(v => {
    if (v.sub_category && v.sub_category !== 'NaN') cats.add(v.sub_category)
  })
  return Array.from(cats).sort()
})

const onIndustryChange = () => {
  selectedSubCategory.value = ''
}

const filterByRegion = (villages, regionPath) => {
  if (!regionPath.length) return villages
  const [selectedProvince, selectedCity, selectedDistrict, selectedTown] = regionPath
  return villages.filter(v => {
    if (v.province !== selectedProvince) return false
    if (selectedCity && v.city !== selectedCity) return false
    if (selectedDistrict) {
      const { district } = parseDistrictTown(v.name)
      if (district !== selectedDistrict) return false
    }
    if (selectedTown) {
      const { town } = parseDistrictTown(v.name)
      if (town !== selectedTown) return false
    }
    return true
  })
}

// 基础筛选后的村庄（产业+产品+地区）
const filteredVillages = computed(() => {
  let result = allVillages.value
  if (selectedIndustry.value) {
    result = getBaseVillagesByIndustry(selectedIndustry.value)
  }
  if (selectedSubCategory.value) {
    result = result.filter(v => v.sub_category === selectedSubCategory.value)
  }
  if (selectedRegion.value.length) {
    result = filterByRegion(result, selectedRegion.value)
  }
  return result
})

// 分页后的村庄
const paginatedVillages = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredVillages.value.slice(start, start + pageSize.value)
})

// 监听筛选变化，重置页码
watch([selectedIndustry, selectedSubCategory, selectedRegion], () => {
  currentPage.value = 1
})

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}
const handleCurrentChange = (val) => {
  currentPage.value = val
}

const goDetail = (id) => router.push(`/village/${id}`)

// 生命周期
onMounted(() => {
  loadVillages()
  if (isLoggedIn.value) {
    loadFavorites()
  }
})
</script>

<style scoped>
.products-page {
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
.filter-row {
  margin: 20px 0;
  text-align: center;
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
  padding: 50px;
  color: #999;
}
@media (max-width: 768px) {
  .header h1 { font-size: 1.4rem; }
  .village-img { width: 70px; height: 70px; }
}
</style>