<template>
  <div class="village-detail" v-loading="loading">
    <div class="header">
      <el-button @click="$router.back()" type="primary" plain>← 返回</el-button>
      <el-button @click="$router.push('/ranking')" type="info" plain>🔥 排行榜</el-button>
    </div>

    <div v-if="village" class="content">
      <div class="title-section">
        <h1>{{ simplifyName(village.name) }}</h1>
        <div class="tags">
          <el-tag type="success">{{ village.industry_type || '特色产业' }}</el-tag>
          <el-tag v-if="village.product_name" type="info">主打产品：{{ village.product_name }}</el-tag>
        </div>
        <div class="action-buttons">
  <el-button :type="isLiked ? 'danger' : 'default'" @click="toggleLike" :loading="likeLoading">
    <span class="action-icon">{{ isLiked ? '❤️' : '🤍' }}</span>
    {{ isLiked ? '已点赞' : '点赞' }}
  </el-button>
  <el-button :type="isFavorited ? 'warning' : 'default'" @click="toggleFavorite" :loading="favLoading">
    <span class="action-icon">{{ isFavorited ? '⭐' : '☆' }}</span>
    {{ isFavorited ? '已收藏' : '收藏' }}
  </el-button>
  <el-button :type="isWanted ? 'success' : 'default'" @click="toggleWant" :loading="wantLoading">
    <el-icon><Flag /></el-icon>
    {{ isWanted ? '已想去' : '想去' }}
  </el-button>
</div>
      </div>

      <div class="image-wrapper">
        <img src="https://picsum.photos/id/104/800/400" class="main-image" />
      </div>
<div class="section">
  <h2>村庄简介</h2>
  <p><strong>地址：</strong>{{ village.province }} · {{ village.city }} · {{ village.name || '' }}</p>
  <p><strong>特产：</strong>{{ village.sub_category ? village.sub_category + ' - ' : '' }}{{ village.product_name || '无' }}</p>
  <div class="baike-buttons">
    <el-button type="primary" link @click="openBaike(village, 0)">
      📖 村庄简介
    </el-button>
    <el-button type="success" link @click="openBaike(village, 1)" v-if="getBaikeLinks(village.baike_urls).length > 1">
      🛒 产品介绍
    </el-button>
  </div>
</div>

      <!-- 评论与回复区域 -->
      <div class="section comments-section">
        <h2>💬 用户评论</h2>
        <div v-if="comments.length" class="comment-list">
          <div v-for="comment in comments" :key="comment.id" class="comment-item">
            <div class="comment-meta">
              <strong class="comment-user">{{ comment.username }}</strong>
              <span class="comment-time">{{ formatDate(comment.created_at) }}</span>
              <div class="comment-actions">
                <span class="comment-like" @click="toggleCommentLike(comment)">
                  {{ comment.userLiked ? '❤️' : '🤍' }} {{ comment.likeCount }}
                </span>
                <span class="comment-reply" @click="startReply(comment.id)">回复</span>
              </div>
            </div>
            <div class="comment-content">{{ comment.content }}</div>

            <!-- 回复列表 -->
            <div v-if="comment.replies && comment.replies.length" class="replies">
              <div v-for="reply in (comment.showAllReplies ? comment.replies : comment.replies.slice(0, 3))" :key="reply.id" class="reply-item">
                <div class="reply-meta">
                  <strong class="reply-user">{{ reply.username }}</strong>
                  <span class="reply-time">{{ formatDate(reply.created_at) }}</span>
                  <span class="reply-like" @click="toggleCommentLike(reply)">{{ reply.userLiked ? '❤️' : '🤍' }} {{ reply.likeCount }}</span>
                </div>
                <div class="reply-content">{{ reply.content }}</div>
              </div>
              <div v-if="comment.replies.length > 3" class="toggle-replies">
                <el-button link @click="comment.showAllReplies = !comment.showAllReplies">
                  {{ comment.showAllReplies ? '收起回复' : `展开 ${comment.replies.length - 3} 条回复` }}
                </el-button>
              </div>
            </div>

            <!-- 回复输入框 -->
            <div v-if="replyingToId === comment.id" class="reply-input">
              <div class="reply-to">回复 {{ comment.username }}</div>
              <el-input v-model="replyContent" type="textarea" rows="2" :placeholder="`回复 ${comment.username}`" />
              <div class="reply-actions">
                <el-button size="small" @click="cancelReply">取消</el-button>
                <el-button size="small" type="primary" @click="submitReply(comment.id)" :loading="replyLoading">回复</el-button>
              </div>
            </div>
          </div>
          <div v-if="showMoreComments" class="show-more">
            <el-button link @click="loadAllComments">查看全部评论</el-button>
          </div>
        </div>
        <div v-else class="comment-empty">暂无评论，抢个沙发吧～</div>

        <!-- 发表顶级评论 -->
        <div v-if="isLoggedIn" class="comment-input">
          <el-input v-model="newComment" type="textarea" rows="3" placeholder="分享你的看法..." />
          <div class="comment-actions">
            <el-button type="primary" @click="submitComment" :loading="commentLoading">发表评论</el-button>
          </div>
        </div>
        <div v-else class="login-prompt">
          <el-button link @click="goLogin">登录后发表评论</el-button>
        </div>
      </div>
    </div>

    <div v-else class="empty">
      <h2>未找到该村庄信息</h2>
      <el-button @click="$router.back()">返回上一页</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Star, StarFilled, Collection, Flag } from '@element-plus/icons-vue'
import axios from 'axios'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const villageId = route.params.id
const userStore = useUserStore()

const village = ref(null)
const loading = ref(false)
const storyLoading = ref(false)

// 交互状态
const isLiked = ref(false)
const isFavorited = ref(false)
const isWanted = ref(false)
const likeLoading = ref(false)
const favLoading = ref(false)
const wantLoading = ref(false)

// 评论相关
const comments = ref([])
const newComment = ref('')
const commentLoading = ref(false)
const showMoreComments = ref(false)
const allCommentsLoaded = ref(false)

// 回复相关
const replyingToId = ref(null)
const replyContent = ref('')
const replyLoading = ref(false)

const isLoggedIn = computed(() => !!userStore.token)

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
  const date = new Date(isoString)
  return `${date.getMonth()+1}/${date.getDate()} ${date.getHours()}:${date.getMinutes().toString().padStart(2,'0')}`
}

// 获取用户交互状态
const fetchUserInteractions = async () => {
  if (!isLoggedIn.value) return
  try {
    const [favIds, wantIds, likeIds] = await Promise.all([
      axios.get('/api/user/favorites').catch(() => ({ data: [] })),
      axios.get('/api/user/wants').catch(() => ({ data: [] })),
      axios.get('/api/user/likes').catch(() => ({ data: [] }))
    ])
    isFavorited.value = favIds.data.some(v => v.id === village.value?.id)
    isWanted.value = wantIds.data.some(v => v.id === village.value?.id)
    isLiked.value = likeIds.data.some(v => v.id === village.value?.id)
  } catch (error) {
    console.error('获取用户交互状态失败', error)
  }
}

// 点赞/取消点赞村庄
const toggleLike = async () => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  likeLoading.value = true
  try {
    if (isLiked.value) {
      await axios.post(`/api/villages/${villageId}/unlike`)
      isLiked.value = false
      ElMessage.success('已取消点赞')
    } else {
      await axios.post(`/api/villages/${villageId}/like`)
      isLiked.value = true
      ElMessage.success('点赞成功')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    likeLoading.value = false
  }
}

// 收藏/取消收藏
const toggleFavorite = async () => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  favLoading.value = true
  try {
    if (isFavorited.value) {
      await axios.post(`/api/villages/${villageId}/unfavorite`)
      isFavorited.value = false
      ElMessage.success('已取消收藏')
    } else {
      await axios.post(`/api/villages/${villageId}/favorite`)
      isFavorited.value = true
      ElMessage.success('收藏成功')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    favLoading.value = false
  }
}

// 想去/取消想去
const toggleWant = async () => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  wantLoading.value = true
  try {
    if (isWanted.value) {
      await axios.post(`/api/villages/${villageId}/unwant`)
      isWanted.value = false
      ElMessage.success('已取消想去')
    } else {
      await axios.post(`/api/villages/${villageId}/want`)
      isWanted.value = true
      ElMessage.success('已添加到想去列表')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    wantLoading.value = false
  }
}

// 构建评论树（依赖 parent_id）
const buildCommentTree = (flatList) => {
  const map = new Map()
  const roots = []
  flatList.forEach(item => {
    const likeCount = Number(item.like_count) || 0
    map.set(item.id, { ...item, likeCount, replies: [], showAllReplies: false })
  })
  flatList.forEach(item => {
    const node = map.get(item.id)
    if (item.parent_id && map.has(item.parent_id)) {
      map.get(item.parent_id).replies.push(node)
    } else {
      roots.push(node)
    }
  })
  roots.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  return roots
}

// 加载评论
const loadComments = async (loadAll = false) => {
  try {
    const params = loadAll ? {} : { limit: 5 }
    const res = await axios.get(`/api/comments/village/${villageId}`, { params })
    const flatComments = res.data
    // 构建嵌套树
    const buildTree = (items, parentId = null) => {
      return items.filter(i => i.parent_id === parentId).map(i => ({
        ...i,
        replies: buildTree(items, i.id),
        showAllReplies: false
      }))
    }
    comments.value = buildTree(flatComments)
    showMoreComments.value = (!loadAll && flatComments.length === 5)
    allCommentsLoaded.value = loadAll
  } catch (error) {
    console.error('加载评论失败', error)
  }
}

const loadAllComments = () => loadComments(true)

// 发表顶级评论
const submitComment = async () => {
  if (!newComment.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  commentLoading.value = true
  const tempId = Date.now()
  const newCommentObj = {
    id: tempId,
    username: userStore.user?.username || '我',
    content: newComment.value,
    created_at: new Date().toISOString(),
    likeCount: 0,
    userLiked: false,
    parent_id: null,
    replies: [],
    showAllReplies: false
  }
  comments.value.unshift(newCommentObj)
  newComment.value = ''
  ElMessage.success('评论成功')
  try {
    await axios.post('/api/comments', {
      village_id: Number(villageId),
      content: newCommentObj.content,
      parent_id: null
    }).catch(err => console.error('后端保存失败', err))
  } catch (error) {
    comments.value = comments.value.filter(c => c.id !== tempId)
    ElMessage.error('评论保存失败，请重试')
  } finally {
    commentLoading.value = false
  }
}

// 回复相关
const startReply = (commentId) => {
  replyingToId.value = commentId
  replyContent.value = ''
}
const cancelReply = () => {
  replyingToId.value = null
  replyContent.value = ''
}
const submitReply = async (parentId) => {
  if (!replyContent.value.trim()) {
    ElMessage.warning('请输入回复内容')
    return
  }
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  replyLoading.value = true
  try {
    await axios.post('/api/comments', {
      village_id: Number(villageId),
      content: replyContent.value,
      parent_id: parentId
    })
    // 回复成功后重新加载评论列表（从后端获取最新数据）
    await loadComments(false)
    cancelReply()
    ElMessage.success('回复成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '回复失败')
  } finally {
    replyLoading.value = false
  }
}

// 评论点赞/取消点赞
const toggleCommentLike = async (comment) => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  // 确保 likeCount 是数字
  comment.likeCount = Number(comment.likeCount) || 0
  const originalLiked = comment.userLiked
  const originalCount = comment.likeCount
  // 乐观更新
  comment.userLiked = !originalLiked
  comment.likeCount += comment.userLiked ? 1 : -1

  try {
    const url = originalLiked ? `/api/comments/${comment.id}/unlike` : `/api/comments/${comment.id}/like`
    await axios.post(url)
  } catch (error) {
    // 回滚
    comment.userLiked = originalLiked
    comment.likeCount = originalCount
    // 如果是 400 错误且后端返回 "Already liked"，尝试刷新评论列表以同步状态
    if (error.response?.status === 400 && error.response?.data?.error === 'Already liked') {
      await loadComments(allCommentsLoaded.value)
    }
    ElMessage.error(error.response?.data?.message || '操作失败')
  }
}

// 解析 baike_urls 字段（后端已统一为 | 分隔）
const getBaikeLinks = (urls) => {
  if (!urls || urls === 'NaN') return []
  // 按竖线分割，过滤空字符串
  return urls.split('|').filter(u => u && u.trim().startsWith('http'))
}

// 打开百度百科
const openBaike = (village, index) => {
  const links = getBaikeLinks(village.baike_urls)
  const url = links[index]
  if (url) {
    window.open(url, '_blank')
  } else {
    ElMessage.warning(index === 0 ? '暂无村庄简介' : '暂无产品介绍')
  }
}

// 加载村庄详情
const loadVillage = async () => {
  loading.value = true
  try {
    const res = await axios.get(`/api/village/${villageId}`)
    if (res.data && res.data.id) {
      village.value = res.data
    } else {
      throw new Error('数据格式错误')
    }
  } catch (error) {
    console.error('加载失败', error)
    ElMessage.error('加载村庄信息失败，请检查后端接口')
    village.value = null
  } finally {
    loading.value = false
  }
}

const goLogin = () => router.push('/login')

// 监听路由参数变化
watch(
  () => route.params.id,
  async (newId, oldId) => {
    if (newId !== oldId) {
      await loadVillage()
      if (village.value) {
        await fetchUserInteractions()
        await loadComments(false)
      }
    }
  }
)

onMounted(async () => {
  await loadVillage()
  if (village.value) {
    await fetchUserInteractions()
    await loadComments(false)
  }
})
</script>

<style scoped>
/* 保留原有所有样式，在此基础上添加回复相关样式 */
.village-detail {
  max-width: 1000px;
  margin: 40px auto;
  padding: 0 24px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.title-section {
  background: white;
  border-radius: 32px;
  padding: 24px 28px;
  margin-bottom: 24px;
  box-shadow: 0 8px 20px rgba(0,0,0,0.05);
  border: 1px solid rgba(219,203,184,0.5);
}
.title-section h1 {
  font-size: 2.2rem;
  font-weight: 700;
  color: #2b5e2b;
  margin: 0 0 12px;
}
.tags {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.image-wrapper {
  margin: 24px 0;
  border-radius: 32px;
  overflow: hidden;
  box-shadow: 0 8px 20px rgba(0,0,0,0.1);
}
.main-image {
  width: 100%;
  max-height: 420px;
  object-fit: cover;
  display: block;
  transition: transform 0.3s;
}
.image-wrapper:hover .main-image {
  transform: scale(1.02);
}
.section {
  background: white;
  border-radius: 28px;
  padding: 24px 28px;
  margin: 24px 0;
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
  border: 1px solid #f1e7dd;
}
.section h2 {
  font-size: 1.6rem;
  font-weight: 600;
  color: #2b5e2b;
  border-left: 4px solid #e67e22;
  padding-left: 16px;
  margin-bottom: 20px;
}
.baike-link {
  margin-top: 20px;
  padding-top: 12px;
  border-top: 1px dashed #ddd0bc;
}
.comments-section {
  background: #fefcf7;
}
.comment-item {
  border-bottom: 1px solid #eee;
  padding: 12px 0;
}
.comment-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.comment-user {
  font-weight: bold;
  color: #2b5e2b;
}
.comment-time {
  font-size: 12px;
  color: #999;
}
.comment-actions {
  display: flex;
  gap: 16px;
}
.comment-like, .comment-reply {
  cursor: pointer;
  font-size: 12px;
  color: #666;
}
.comment-like:hover, .comment-reply:hover {
  color: #e67e22;
}
.comment-content {
  margin-bottom: 8px;
}
.replies {
  margin-left: 30px;
  margin-top: 8px;
  border-left: 2px solid #e0e0d0;
  padding-left: 16px;
}
.reply-item {
  margin-top: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #f0f0e0;
}
.reply-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  margin-bottom: 4px;
}
.reply-user {
  font-weight: bold;
  color: #8b8b8b;
}
.reply-time {
  font-size: 12px;
  color: #999;
}
.reply-like {
  cursor: pointer;
  font-size: 12px;
  color: #666;
}
.reply-like:hover {
  color: #e67e22;
}
.reply-content {
  font-size: 13px;
  color: #555;
}
.toggle-replies {
  margin-top: 6px;
  text-align: right;
}
.reply-input {
  margin-top: 12px;
  margin-left: 30px;
}
.reply-to {
  font-size: 12px;
  color: #888;
  margin-bottom: 6px;
}
.reply-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
.comment-empty {
  text-align: center;
  padding: 20px;
  color: #aaa;
}
.comment-input {
  margin-top: 20px;
}
.comment-actions {
  margin-top: 12px;
  text-align: right;
}
.login-prompt {
  text-align: center;
  margin-top: 16px;
}
.show-more {
  text-align: center;
  margin-top: 12px;
}
.empty {
  text-align: center;
  padding: 80px 20px;
}
@media (max-width: 768px) {
  .village-detail { padding: 0 16px; margin: 20px auto; }
  .title-section h1 { font-size: 1.6rem; }
}
</style>