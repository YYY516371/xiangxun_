<template>
  <div class="ranking-page">
    <div class="header">
      <el-button @click="$router.back()" type="primary" plain>← 返回</el-button>
      <h1>排行榜</h1>
    </div>

    <el-tabs v-model="activeRanking" class="ranking-tabs">
      <!-- 点赞排行榜 -->
      <el-tab-pane label="点赞排行榜" name="like">
        <div v-for="item in likeRankingList" :key="item.id" class="ranking-item">
          <el-card>
            <div class="village-info">
              <span class="rank">#{{ item.rank }}</span>
              <span class="name">{{ item.name }}</span>
              <span class="product" v-if="item.productName">🍃 {{ item.productName }}</span>
              <span class="count">{{ item.likeCount }} ❤️</span>
              <el-button size="small" @click="goDetail(item.id)">查看详情</el-button>
              <!-- 收藏图标（纯文本） -->
              <span class="favorite-icon" @click.stop="toggleFavorite(item.id)">
                {{ isFavorited(item.id) ? '⭐' : '☆' }}
              </span>
            </div>
            <div class="hot-comments">
              <h4>热门评论</h4>
              <div v-if="item.topComments && item.topComments.length">
                <div v-for="comment in item.topComments" :key="comment.id" class="comment">
                  <div class="comment-user">{{ comment.username }}</div>
                  <div class="comment-content">{{ comment.content }}</div>
                  <div class="comment-footer">
                    <span class="comment-like-count">{{ comment.likeCount }} </span>
                    <span
                      class="comment-like-heart"
                      @click.stop="toggleCommentLike(comment, item.id, activeRanking)"
                    >
                      {{ comment.userLiked ? '❤️' : '🤍' }}
                    </span>
                  </div>
                </div>
              </div>
              <div v-else class="no-comment">暂无热门评论</div>
            </div>
          </el-card>
        </div>
      </el-tab-pane>

      <!-- 旅行排行榜 -->
      <el-tab-pane label="旅行排行榜" name="want">
        <div v-for="item in wantRankingList" :key="item.id" class="ranking-item">
          <el-card>
            <div class="village-info">
              <span class="rank">#{{ item.rank }}</span>
              <span class="name">{{ item.name }}</span>
              <span class="product" v-if="item.productName">🍃 {{ item.productName }}</span>
              <span class="count">{{ item.wantCount }} <span style="color: red;">🚩</span></span>
              <el-button size="small" @click="goDetail(item.id)">查看详情</el-button>
              <!-- 收藏图标（纯文本） -->
              <span class="favorite-icon" @click.stop="toggleFavorite(item.id)">
                {{ isFavorited(item.id) ? '⭐' : '☆' }}
              </span>
            </div>
            <div class="hot-comments">
              <h4>热门评论</h4>
              <div v-if="item.topComments && item.topComments.length">
                <div v-for="comment in item.topComments" :key="comment.id" class="comment">
                  <div class="comment-user">{{ comment.username }}</div>
                  <div class="comment-content">{{ comment.content }}</div>
                  <div class="comment-footer">
                    <span class="comment-like-count">{{ comment.likeCount }} </span>
                    <span
                      class="comment-like-heart"
                      @click.stop="toggleCommentLike(comment, item.id, 'want')"
                    >
                      {{ comment.userLiked ? '❤️' : '🤍' }}
                    </span>
                  </div>
                </div>
              </div>
              <div v-else class="no-comment">暂无热门评论</div>
            </div>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const activeRanking = ref('like')
const likeRankingList = ref([])
const wantRankingList = ref([])
const favoriteIds = ref([])

// 加载用户收藏列表
const loadFavorites = async () => {
  if (!userStore.token) return
  try {
    const res = await axios.get('/api/user/favorites')
    favoriteIds.value = res.data.map(v => v.id)
  } catch (error) {
    console.error('加载收藏列表失败', error)
  }
}

const isFavorited = (id) => favoriteIds.value.includes(id)

// 切换收藏
const toggleFavorite = async (id) => {
  if (!userStore.token) {
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

// 适配后端字段
const normalizeItem = (item, index) => {
  return {
    id: item.village_id,
    name: item.village_name,
    productName: item.product_name,
    likeCount: item.like_count,
    wantCount: item.want_count || 0,
    rank: index + 1,
    topComments: Array.isArray(item.top_comments)
      ? item.top_comments.map(c => ({
          id: c.id,
          username: c.username,
          content: c.content,
          likeCount: c.like_count,
          userLiked: c.user_liked || false
        }))
      : []
  }
}

const loadRankings = async () => {
  try {
    const likeRes = await axios.get('/api/rankings/like')
    if (Array.isArray(likeRes.data)) {
      likeRankingList.value = likeRes.data.map((item, idx) => normalizeItem(item, idx))
    }
    const wantRes = await axios.get('/api/rankings/want')
    if (Array.isArray(wantRes.data)) {
      wantRankingList.value = wantRes.data.map((item, idx) => normalizeItem(item, idx))
    }
  } catch (error) {
    console.error('加载排行榜失败', error)
    ElMessage.error('加载排行榜失败，请稍后重试')
  }
}

const goDetail = (id) => {
  if (!id) {
    ElMessage.error('村庄ID无效')
    return
  }
  router.push(`/village/${id}`)
}

// 评论点赞/取消点赞（爱心点击）
const toggleCommentLike = async (comment, villageId, listType) => {
  if (!userStore.token) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }

  const originalLiked = comment.userLiked
  const originalCount = comment.likeCount
  // 乐观更新
  comment.userLiked = !originalLiked
  comment.likeCount += comment.userLiked ? 1 : -1

  try {
    const url = originalLiked
      ? `/api/comments/${comment.id}/unlike`
      : `/api/comments/${comment.id}/like`
    await axios.post(url)
  } catch (error) {
    // 回滚
    comment.userLiked = originalLiked
    comment.likeCount = originalCount
    ElMessage.error(error.response?.data?.message || '操作失败')
  }
}

onMounted(() => {
  loadRankings()
  if (userStore.token) loadFavorites()
})
</script>

<style scoped>
/* 与原样式相同，增加对心形和星形鼠标样式 */
.ranking-page {
  max-width: 1000px;
  margin: 20px auto;
  padding: 0 20px;
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
.ranking-item {
  margin-bottom: 24px;
}
.village-info {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.rank {
  font-size: 1.5rem;
  font-weight: bold;
  color: #e67e22;
}
.name {
  font-size: 1.2rem;
  font-weight: bold;
}
.product {
  font-size: 0.9rem;
  color: #2b5e2b;
  background: #eef5e8;
  padding: 2px 8px;
  border-radius: 20px;
}
.count {
  color: #666;
}
.hot-comments {
  background: #f9f9f0;
  padding: 12px;
  border-radius: 12px;
  margin-top: 12px;
}
.comment {
  border-bottom: 1px solid #e0e0d0;
  padding: 8px 0;
  display: flex;
  flex-direction: column;
}
.comment-user {
  font-weight: bold;
}
.comment-footer {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-top: 4px;
  font-size: 12px;
  color: #888;
}
.comment-like-heart {
  cursor: pointer;
  font-size: 16px;
  user-select: none;
}
.favorite-icon {
  cursor: pointer;
  font-size: 20px;
  user-select: none;
}
.no-comment {
  text-align: center;
  padding: 12px;
  color: #aaa;
}
@media (max-width: 768px) {
  .village-info {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>