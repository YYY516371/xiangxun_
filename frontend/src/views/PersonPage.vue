<template>
  <div class="person-page">
    <div class="header">
      <el-button @click="$router.back()" type="primary" plain>← 返回</el-button>
      <h1>个人中心</h1>
    </div>

    <!-- 用户信息卡片 -->
    <el-card class="profile-card">
      <div class="profile-header">
        <div class="avatar-wrapper" @click="showAvatarUpload">
<el-avatar 
  :size="80" 
  :src="userInfo.avatar || defaultAvatar" 
  :fallback-src="defaultAvatar"
/>
          <div class="avatar-overlay">点击更换</div>
        </div>
        <div class="info">
          <div class="name-row">
            <h2>{{ userInfo.nickname || userInfo.username }}</h2>
            <el-button link type="primary" @click="editProfile">编辑资料</el-button>
          </div>
          <p>ID: {{ userInfo.id }}</p>
          <p>注册时间：{{ formatDate(userInfo.created_at) }}</p>
          <p class="signature">{{ userInfo.signature || '这个人很懒，什么都没写~' }}</p>
          <div class="user-details">
          <span v-if="userInfo.gender" :style="{ color: genderColor }">
            {{ genderSymbol }}
          </span>
          <span v-if="userInfo.birthday"> · 生日：{{ userInfo.birthday }}</span>
          <span v-if="userInfo.province"> · 来自：{{ userInfo.province }}</span>
         </div>
        </div>
      </div>
    </el-card>

    <!-- 数据概览卡片 -->
    <el-card class="stats-card">
      <h3>数据概览</h3>
      <div class="stats-grid">
        <div class="stat-item">
          <span class="stat-value">{{ stats.favorites }}</span>
          <span class="stat-label">收藏</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ stats.wants }}</span>
          <span class="stat-label">想去</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ stats.likes }}</span>
          <span class="stat-label">点赞</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ stats.comments }}</span>
          <span class="stat-label">评论</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ stats.publish_count }}</span>
          <span class="stat-label">发布</span>
        </div>
      </div>
    </el-card>

    <!-- 标签页（简化命名） -->
    <el-tabs v-model="activeTab" class="tabs">
      <el-tab-pane label="收藏" name="favorites">
        <div class="list-container">
          <el-row :gutter="20">
            <el-col :span="12" v-for="v in paginatedFavorites" :key="v.id" style="margin-bottom: 20px;">
              <el-card class="item-card" @click="goDetail(v.id)">
                <div class="item-content">
                  <img :src="v.image_url || defaultImage" class="item-img" />
                  <div class="item-info">
                    <h4>{{ simplifyName(v.name) }}</h4>
                    <p>{{ v.product_name || '特色产品' }}</p>
                  </div>
                </div>
                <div class="item-actions">
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
              @current-change="favPageChange"
            />
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="想去" name="wants">
        <!-- 结构与收藏类似，数据为 wantsList -->
        <el-row :gutter="20">
          <el-col :span="12" v-for="v in paginatedWants" :key="v.id" style="margin-bottom: 20px;">
            <el-card class="item-card" @click="goDetail(v.id)">
              <div class="item-content">
                <img :src="v.image_url || defaultImage" class="item-img" />
                <div class="item-info">
                  <h4>{{ simplifyName(v.name) }}</h4>
                  <p>{{ v.product_name || '特色产品' }}</p>
                </div>
              </div>
              <div class="item-actions">
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
            @current-change="wantPageChange"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane label="点赞" name="likes">
        <!-- 结构与收藏类似，数据为 likesList -->
        <el-row :gutter="20">
          <el-col :span="12" v-for="v in paginatedLikes" :key="v.id" style="margin-bottom: 20px;">
            <el-card class="item-card" @click="goDetail(v.id)">
              <div class="item-content">
                <img :src="v.image_url || defaultImage" class="item-img" />
                <div class="item-info">
                  <h4>{{ simplifyName(v.name) }}</h4>
                  <p>{{ v.product_name || '特色产品' }}</p>
                </div>
              </div>
              <div class="item-actions">
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
            @current-change="likePageChange"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane label="评论" name="comments">
        <div class="comment-list">
          <div v-for="c in paginatedComments" :key="c.id" class="comment-item">
            <div class="comment-header">
              <strong>{{ c.village_name }}</strong>
              <span>{{ formatDate(c.created_at) }}</span>
            </div>
            <div class="comment-content">{{ c.content }}</div>
            <div class="comment-meta">👍 {{ c.like_count }}</div>
            <el-button size="small" link @click="goDetail(c.village_id)">查看村庄</el-button>
          </div>
          <div class="pagination" v-if="commentsList.length > commentPageSize">
            <el-pagination
              v-model:current-page="commentPage"
              :page-size="commentPageSize"
              :total="commentsList.length"
              layout="prev, pager, next"
              @current-change="commentPageChange"
            />
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 编辑资料对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑资料" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="昵称">
          <el-input v-model="editForm.nickname" />
        </el-form-item>
        <el-form-item label="个性签名">
          <el-input type="textarea" v-model="editForm.signature" rows="2" />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="editForm.gender">
            <el-radio label="男">男</el-radio>
            <el-radio label="女">女</el-radio>
            <el-radio label="保密">保密</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="生日">
          <el-date-picker v-model="editForm.birthday" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" />
        </el-form-item>
       <el-form-item label="地区">
  <el-select v-model="editForm.province" placeholder="请选择省份" clearable>
    <el-option v-for="p in provinces" :key="p" :label="p" :value="p" />
  </el-select>
</el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveProfile">保存</el-button>
      </template>
    </el-dialog>

    <!-- 头像上传裁剪对话框 -->
    <el-dialog v-model="avatarDialogVisible" title="上传头像" width="400px">
      <input type="file" ref="avatarInput" accept="image/*" @change="onAvatarChange" style="margin-bottom: 10px;" />
      <div v-if="avatarPreview" class="avatar-crop-area">
        <img :src="avatarPreview" ref="cropImage" style="max-width: 100%;" />
      </div>
      <div v-if="avatarPreview" class="crop-controls">
        <el-button size="small" @click="cropAvatar">裁剪并上传</el-button>
      </div>
    </el-dialog>
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
const defaultAvatar = 'https://picsum.photos/id/64/80/80'
const defaultImage = 'https://picsum.photos/id/104/150/150'

// 用户信息
const userInfo = ref({})
const editDialogVisible = ref(false)
const editForm = ref({
  nickname: '',
  signature: '',
  gender: '',
  birthday: '',
  region: []
})

const genderSymbol = computed(() => {
  if (userInfo.value.gender === '男') return '♂'
  if (userInfo.value.gender === '女') return '♀'
  return userInfo.value.gender || ''
})
const genderColor = computed(() => {
  if (userInfo.value.gender === '男') return '#409eff'  // 蓝色
  if (userInfo.value.gender === '女') return '#f56c6c'  // 红色
  return '#909399'  // 其他性别灰色
})

// 统计数据
const stats = ref({
  favorites: 0,
  wants: 0,
  likes: 0,
  comments: 0,
  publish_count: 0
})

// 收藏、想去、点赞列表
const favoritesList = ref([])
const wantsList = ref([])
const likesList = ref([])
const commentsList = ref([])

// 分页
const pageSize = ref(6)
const favPage = ref(1)
const wantPage = ref(1)
const likePage = ref(1)
const commentPage = ref(1)
const commentPageSize = ref(5)

const paginatedFavorites = computed(() => {
  const start = (favPage.value - 1) * pageSize.value
  return favoritesList.value.slice(start, start + pageSize.value)
})
const paginatedWants = computed(() => {
  const start = (wantPage.value - 1) * pageSize.value
  return wantsList.value.slice(start, start + pageSize.value)
})
const paginatedLikes = computed(() => {
  const start = (likePage.value - 1) * pageSize.value
  return likesList.value.slice(start, start + pageSize.value)
})
const paginatedComments = computed(() => {
  const start = (commentPage.value - 1) * commentPageSize.value
  return commentsList.value.slice(start, start + commentPageSize.value)
})

const activeTab = ref('favorites')

const provinces = ref([
  '北京市', '天津市', '上海市', '重庆市', '河北省', '山西省', '辽宁省', '吉林省', '黑龙江省',
  '江苏省', '浙江省', '安徽省', '福建省', '江西省', '山东省', '河南省', '湖北省', '湖南省',
  '广东省', '海南省', '四川省', '贵州省', '云南省', '陕西省', '甘肃省', '青海省', '台湾省',
  '内蒙古自治区', '广西壮族自治区', '宁夏回族自治区', '新疆维吾尔自治区', '西藏自治区'
])

// 辅助函数
const simplifyName = (fullName) => {
  if (!fullName) return ''
  let name = fullName
  const districtIdx = name.indexOf('区')
  if (districtIdx !== -1) name = name.substring(districtIdx + 1)
  const townIdx = name.indexOf('镇')
  if (townIdx !== -1) name = name.substring(townIdx + 1)
  return name || fullName
}
const formatDate = (isoString) => {
  if (!isoString) return ''
  return isoString.split('T')[0]
}

// 加载数据
const loadProfile = async () => {
  try {
    const res = await axios.get('/api/user/profile')
    userInfo.value = res.data
    editForm.value = {
      nickname: res.data.nickname || '',
      signature: res.data.signature || '',
      gender: res.data.gender || '',
      birthday: res.data.birthday || '',
      province: res.data.province || ''
    }
  } catch (error) {
    console.error('加载资料失败', error)
  }
}
const loadFavorites = async () => {
  try {
    const res = await axios.get('/api/user/favorites')
    favoritesList.value = res.data
  } catch (error) {
    console.error('加载收藏失败', error)
  }
}
const loadWants = async () => {
  try {
    const res = await axios.get('/api/user/wants')
    wantsList.value = res.data
  } catch (error) {
    console.error('加载想去失败', error)
  }
}
const loadLikes = async () => {
  try {
    const res = await axios.get('/api/user/likes')
    likesList.value = res.data
  } catch (error) {
    console.error('加载点赞失败', error)
  }
}
const loadComments = async () => {
  try {
    const res = await axios.get('/api/user/comments')
    commentsList.value = res.data
  } catch (error) {
    console.error('加载评论失败', error)
  }
}
const loadStats = async () => {
  try {
    const res = await axios.get('/api/user/stats')
    stats.value = res.data
  } catch (error) {
    console.error('加载统计数据失败', error)
  }
}

// 编辑资料
const editProfile = () => {
  editDialogVisible.value = true
}
const saveProfile = async () => {
  const payload = {
    nickname: editForm.value.nickname,
    signature: editForm.value.signature,
    gender: editForm.value.gender,
    birthday: editForm.value.birthday,
    province: editForm.value.province
  }
  try {
    await axios.put('/api/user/profile', payload)
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    loadProfile()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

// 取消收藏/想去/点赞
const removeFavorite = async (id) => {
  try {
    await axios.post(`/api/villages/${id}/unfavorite`)
    favoritesList.value = favoritesList.value.filter(v => v.id !== id)
    ElMessage.success('已取消收藏')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}
const removeWant = async (id) => {
  try {
    await axios.post(`/api/villages/${id}/unwant`)
    wantsList.value = wantsList.value.filter(v => v.id !== id)
    ElMessage.success('已取消想去')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}
const removeLike = async (id) => {
  try {
    await axios.post(`/api/villages/${id}/unlike`)
    likesList.value = likesList.value.filter(v => v.id !== id)
    ElMessage.success('已取消点赞')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 分页切换
const favPageChange = (val) => { favPage.value = val }
const wantPageChange = (val) => { wantPage.value = val }
const likePageChange = (val) => { likePage.value = val }
const commentPageChange = (val) => { commentPage.value = val }

// 跳转详情
const goDetail = (id) => router.push(`/village/${id}`)

// 头像上传裁剪
const avatarDialogVisible = ref(false)
const avatarInput = ref(null)
const avatarPreview = ref('')
const cropImage = ref(null)
const showAvatarUpload = () => {
  avatarDialogVisible.value = true
}
const onAvatarChange = (e) => {
  const file = e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (event) => {
    avatarPreview.value = event.target.result
  }
  reader.readAsDataURL(file)
}
const cropAvatar = () => {
  if (!cropImage.value) return
  const img = cropImage.value
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  const size = Math.min(img.naturalWidth, img.naturalHeight)
  const sx = (img.naturalWidth - size) / 2
  const sy = (img.naturalHeight - size) / 2
  canvas.width = 200
  canvas.height = 200
  ctx.drawImage(img, sx, sy, size, size, 0, 0, 200, 200)
  canvas.toBlob(async (blob) => {
    const formData = new FormData()
    formData.append('avatar', blob, 'avatar.jpg')
    try {
      const res = await axios.post('/api/user/avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      userInfo.value.avatar = res.data.avatar_url + '?' + new Date().getTime()
      avatarDialogVisible.value = false
      ElMessage.success('头像上传成功')
      await loadProfile()
    } catch (error) {
      ElMessage.error('上传失败')
    }
  }, 'image/jpeg')
}

onMounted(() => {
  if (!userStore.token) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  loadProfile()
  loadFavorites()
  loadWants()
  loadLikes()
  loadComments()
  loadStats()
})
</script>

<style scoped>
.user-details {
  margin-top: 8px;
  font-size: 13px;
  color: #666;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.person-page {
  width: 1200px;
  margin: 0 auto;
  padding: 20px;
  box-sizing: border-box;
  transition: none; 
}
@media (max-width: 1240px) {
  .person-page {
    width: 100%;
    padding: 20px;
  }
}
.favorites-list .el-row,
.wants-list .el-row,
.likes-list .el-row {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -10px;
}
.favorites-list .el-col,
.wants-list .el-col,
.likes-list .el-col {
  width: 50%;
  padding: 0 10px;
  flex: 0 0 50%;
}
.header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}
.profile-card {
  margin-bottom: 24px;
}
.profile-header {
  display: flex;
  gap: 24px;
  align-items: center;
}
.avatar-wrapper {
  position: relative;
  cursor: pointer;
}
.avatar-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  background: rgba(0,0,0,0.6);
  color: white;
  text-align: center;
  font-size: 12px;
  padding: 4px 0;
  border-radius: 0 0 40px 40px;
  opacity: 0;
  transition: 0.2s;
}
.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}
.name-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.signature {
  color: #888;
  margin-top: 8px;
}
.stats-grid {
  display: flex;
  gap: 20px;
  justify-content: space-around;
  margin-top: 16px;
}
.stat-item {
  text-align: center;
}
.stat-value {
  font-size: 24px;
  font-weight: bold;
  display: block;
}
.stat-label {
  font-size: 14px;
  color: #666;
}
.item-card {
  cursor: pointer;
}
.item-content {
  display: flex;
  gap: 12px;
}
.item-img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 8px;
}
.item-actions {
  text-align: right;
  margin-top: 8px;
}
.comment-item {
  border-bottom: 1px solid #eee;
  padding: 12px 0;
}
.comment-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}
.comment-meta {
  font-size: 12px;
  color: #888;
}
.pagination {
  margin-top: 20px;
  text-align: center;
}
</style>