<template>
  <div class="spider-tool">
    <el-card class="page-header">
      <template #header>
        <div class="card-header">
          <el-icon><Connection /></el-icon>
          <span>智能爬虫工具</span>
        </div>
      </template>
      <p>智能抓取网页内容，获取创作灵感和素材</p>
    </el-card>

    <el-row :gutter="20" class="main-content">
      <el-col :span="8">
        <el-card class="input-card">
          <template #header>
            <div class="card-header">
              <span>爬虫设置</span>
            </div>
          </template>

          <el-form :model="form" label-width="100px">
            <el-form-item label="目标网址">
              <el-input
                v-model="form.url"
                placeholder="请输入要抓取的网页URL"
              />
            </el-form-item>

            <el-form-item label="抓取模式">
              <el-select v-model="form.mode" placeholder="选择抓取模式">
                <el-option label="全文抓取" value="full" />
                <el-option label="标题+正文" value="content" />
                <el-option label="仅标题" value="title" />
                <el-option label="图片链接" value="images" />
                <el-option label="视频链接" value="videos" />
                <el-option label="社交媒体" value="social" />
              </el-select>
            </el-form-item>

            <el-form-item label="抓取深度">
              <el-slider
                v-model="form.depth"
                :min="1"
                :max="3"
                :step="1"
                show-input
              />
              <span class="hint">{{ form.depth }}层</span>
            </el-form-item>

            <el-form-item label="内容过滤">
              <el-checkbox-group v-model="form.filters">
                <el-checkbox label="ads">过滤广告</el-checkbox>
                <el-checkbox label="scripts">过滤脚本</el-checkbox>
                <el-checkbox label="styles">过滤样式</el-checkbox>
                <el-checkbox label="comments">过滤评论</el-checkbox>
              </el-checkbox-group>
            </el-form-item>

            <el-form-item label="请求延迟">
              <el-input-number
                v-model="form.delay"
                :min="0"
                :max="10"
                :step="0.5"
                placeholder="秒"
              />
              <span class="hint">秒</span>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="startSpider"
                :loading="loading"
                style="width: 100%"
              >
                <el-icon><Connection /></el-icon>
                开始抓取
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="result-card">
          <template #header>
            <div class="card-header">
              <span>抓取结果</span>
              <div class="header-actions">
                <el-button size="small" @click="exportResult" v-if="result">
                  <el-icon><Download /></el-icon>
                  导出
                </el-button>
                <el-button size="small" @click="clearResult" v-if="result">
                  <el-icon><Delete /></el-icon>
                  清空
                </el-button>
              </div>
            </div>
          </template>

          <div v-if="loading" class="loading-container">
            <el-skeleton :rows="6" animated />
            <div class="progress-info">
              <p class="progress-text">{{ progressText }}</p>
              <el-progress :percentage="progress" />
            </div>
          </div>

          <div v-else-if="result" class="result-container">
            <el-tabs v-model="activeTab">
              <el-tab-pane label="内容摘要" name="summary">
                <div class="content-summary">
                  <h4>{{ result.title || '无标题' }}</h4>
                  <p class="url-info">{{ form.url }}</p>
                  <div class="content-preview">
                    {{ result.content ? result.content.substring(0, 300) + '...' : '无内容' }}
                  </div>
                  <el-descriptions :column="1" border>
                    <el-descriptions-item label="字数统计">
                      {{ result.word_count || 0 }}字
                    </el-descriptions-item>
                    <el-descriptions-item label="图片数量">
                      {{ result.image_count || 0 }}张
                    </el-descriptions-item>
                    <el-descriptions-item label="链接数量">
                      {{ result.link_count || 0 }}个
                    </el-descriptions-item>
                    <el-descriptions-item label="抓取时间">
                      {{ result.crawl_time || '未知' }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </el-tab-pane>

              <el-tab-pane label="完整内容" name="content">
                <div class="full-content">
                  <pre>{{ result.content || '无内容' }}</pre>
                </div>
              </el-tab-pane>

              <el-tab-pane label="图片列表" name="images">
                <div class="image-list">
                  <div
                    v-for="(image, index) in result.images"
                    :key="index"
                    class="image-item"
                  >
                    <img :src="image.url" :alt="image.alt" @error="onImageError" />
                    <p class="image-info">{{ image.alt || '无描述' }}</p>
                  </div>
                  <el-empty v-if="!result.images || result.images.length === 0" description="未找到图片" />
                </div>
              </el-tab-pane>

              <el-tab-pane label="链接列表" name="links">
                <div class="link-list">
                  <el-link
                    v-for="(link, index) in result.links"
                    :key="index"
                    :href="link.url"
                    target="_blank"
                    type="primary"
                    class="link-item"
                  >
                    {{ link.text || link.url }}
                  </el-link>
                  <el-empty v-if="!result.links || result.links.length === 0" description="未找到链接" />
                </div>
              </el-tab-pane>
            </el-tabs>

            <div class="result-actions">
              <el-button @click="useForAI">
                <el-icon><Tools /></el-icon>
                用于AI创作
              </el-button>
              <el-button @click="useForSocial">
                <el-icon><Share /></el-icon>
                发布到社交平台
              </el-button>
            </div>
          </div>

          <el-empty v-else description="设置参数并点击开始抓取" />
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="history-card">
          <template #header>
            <div class="card-header">
              <el-icon><Clock /></el-icon>
              <span>抓取历史</span>
            </div>
          </template>

          <el-table
            :data="spiderHistory"
            stripe
            style="max-height: 500px; overflow-y: auto;"
          >
            <el-table-column prop="url" label="网址" show-overflow-tooltip />
            <el-table-column prop="mode" label="模式" width="80" />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
                  {{ row.status === 'success' ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="120" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button size="small" @click="viewResult(row)" v-if="row.status === 'success'">
                  查看
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 批量抓取 -->
    <el-card class="batch-card">
      <template #header>
        <div class="card-header">
          <el-icon><List /></el-icon>
          <span>批量抓取</span>
        </div>
      </template>

      <el-form :model="batchForm" inline>
        <el-form-item label="URL列表">
          <el-input
            v-model="batchForm.urls"
            type="textarea"
            :rows="4"
            placeholder="每行一个URL，将批量抓取"
            style="width: 400px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="batchSpider" :loading="batchLoading">
            <el-icon><Connection /></el-icon>
            批量抓取
          </el-button>
        </el-form-item>
      </el-form>

      <div v-if="batchResults.length > 0" class="batch-results">
        <h4>抓取结果</h4>
        <el-table :data="batchResults" stripe>
          <el-table-column prop="index" label="序号" width="80" />
          <el-table-column prop="url" label="URL" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
                {{ row.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="word_count" label="字数" width="80" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" @click="viewBatchResult(row)" v-if="row.status === 'success'">
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 热门推荐 -->
    <el-card class="recommend-card">
      <template #header>
        <div class="card-header">
          <el-icon><Star /></el-icon>
          <span>热门推荐</span>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="6" v-for="site in recommendSites" :key="site.url">
          <el-card class="site-card" @click="useRecommendedSite(site)">
            <div class="site-info">
              <h4>{{ site.name }}</h4>
              <p>{{ site.description }}</p>
              <el-tag size="small">{{ site.category }}</el-tag>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Connection, Download, Delete, Clock, Tools, Share, List, Star } from '@element-plus/icons-vue'
import { http } from '@/utils/request'

const router = useRouter()
const loading = ref(false)
const result = ref(null)
const activeTab = ref('summary')
const progress = ref(0)
const progressText = ref('')
const spiderHistory = ref([])
const batchLoading = ref(false)
const batchResults = ref([])

const form = reactive({
  url: '',
  mode: 'content',
  depth: 1,
  filters: ['ads', 'scripts'],
  delay: 1
})

const batchForm = reactive({
  urls: ''
})

const recommendSites = [
  { name: '知乎热榜', url: 'https://www.zhihu.com/hot', description: '获取热门话题', category: '热点' },
  { name: '微博热搜', url: 'https://s.weibo.com/top/summary', description: '获取热搜内容', category: '热点' },
  { name: '今日头条', url: 'https://www.toutiao.com', description: '获取新闻资讯', category: '新闻' },
  { name: '豆瓣电影', url: 'https://movie.douban.com', description: '获取电影评论', category: '影视' }
]

const startSpider = async () => {
  if (!form.url.trim()) {
    ElMessage.warning('请输入目标网址')
    return
  }

  loading.value = true
  progress.value = 0
  progressText.value = '正在初始化...'

  try {
    // 模拟进度
    const progressInterval = setInterval(() => {
      if (progress.value < 90) {
        progress.value += Math.random() * 30
        if (progress.value > 90) progress.value = 90

        if (progress.value < 30) {
          progressText.value = '正在分析网页结构...'
        } else if (progress.value < 60) {
          progressText.value = '正在抓取内容...'
        } else if (progress.value < 90) {
          progressText.value = '正在处理数据...'
        }
      }
    }, 1000)

    // 调用真实的爬虫API
    const response = await http.post('/api/v1/spider/crawl', {
      url: form.url,
      mode: form.mode,
      depth: form.depth,
      filters: form.filters,
      delay: form.delay
    }, {
      timeout: 30000  // 30秒超时
    })

    clearInterval(progressInterval)
    progress.value = 100
    progressText.value = '抓取完成'

    console.log('API响应:', response) // 调试日志

    if (response.success) {
      result.value = response.data
      spiderHistory.value.unshift({
        url: form.url,
        mode: form.mode,
        status: 'success',
        created_at: new Date().toLocaleString(),
        data: response.data
      })
      ElMessage.success('网页抓取完成')
      console.log('爬虫结果已设置:', result.value)
    } else {
      throw new Error(response.message || '抓取失败')
    }

  } catch (error) {
    console.error('抓取失败:', error)
    ElMessage.error('抓取失败: ' + (error.response?.data?.detail || error.message))

    spiderHistory.value.unshift({
      url: form.url,
      mode: form.mode,
      status: 'error',
      created_at: new Date().toLocaleString()
    })
  } finally {
    loading.value = false
  }
}

const exportResult = () => {
  if (result.value) {
    const data = JSON.stringify(result.value, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `spider_result_${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('数据导出成功')
  }
}

const clearResult = () => {
  result.value = null
  activeTab.value = 'summary'
}

const useForAI = () => {
  if (result.value?.content) {
    // 将爬取的内容存储到localStorage，供AI功能使用
    localStorage.setItem('spider-content-for-ai', JSON.stringify({
      title: result.value.title,
      content: result.value.content,
      keywords: result.value.keywords || [],
      source: result.value.url,
      timestamp: new Date().toISOString()
    }))

    ElMessage.success('内容已准备用于AI创作，请前往文本优化或视频生成页面')

    // 询问用户要跳转到哪个功能
    setTimeout(() => {
      ElMessageBox.confirm(
        '内容已准备好，您想要跳转到哪个AI功能？',
        '选择AI功能',
        {
          confirmButtonText: '文本优化',
          cancelButtonText: '视频生成',
          type: 'info',
        }
      ).then(() => {
        // 跳转到文本优化页面
        router.push('/text-optimize')
      }).catch(() => {
        // 跳转到视频生成页面
        router.push('/video-generate')
      })
    }, 1000)
  } else {
    ElMessage.warning('没有可用的内容')
  }
}

const useForSocial = () => {
  if (result.value) {
    ElMessage.success('内容已准备用于社交发布')
    // 这里可以实现跳转到发布页面的逻辑
  }
}

const viewResult = (item) => {
  console.log('查看结果:', item) // 调试日志
  if (item.data) {
    result.value = item.data
    form.url = item.url
    form.mode = item.mode
    activeTab.value = 'summary' // 确保切换到摘要标签页

    // 强制更新响应式数据
    nextTick(() => {
      console.log('结果更新后:', result.value)
    })
  } else {
    ElMessage.warning('没有可查看的详细数据')
  }
}

const batchSpider = async () => {
  if (!batchForm.urls.trim()) {
    ElMessage.warning('请输入URL列表')
    return
  }

  const urls = batchForm.urls.trim().split('\n').filter(url => url.trim())
  if (urls.length === 0) {
    ElMessage.warning('请输入有效的URL')
    return
  }

  batchLoading.value = true
  batchResults.value = []

  for (let i = 0; i < urls.length; i++) {
    const url = urls[i].trim()
    try {
      // 模拟批量抓取
      await new Promise(resolve => setTimeout(resolve, 2000))

      batchResults.value.push({
        index: i + 1,
        url: url,
        status: 'success',
        word_count: Math.floor(Math.random() * 1000) + 100
      })
    } catch (error) {
      batchResults.value.push({
        index: i + 1,
        url: url,
        status: 'error',
        error: error.message
      })
    }
  }

  batchLoading.value = false
  ElMessage.success(`批量抓取完成，成功 ${batchResults.value.filter(r => r.status === 'success').length} 个`)
}

const viewBatchResult = (row) => {
  // 可以查看批量抓取的详细结果
  ElMessage.info(`查看 ${row.url} 的抓取结果`)
}

const useRecommendedSite = (site) => {
  form.url = site.url
  ElMessage.info(`已选择推荐网站: ${site.name}`)
}

const onImageError = (event) => {
  event.target.src = 'https://picsum.photos/300/200?error'
}

onMounted(() => {
  // 加载历史记录
  const savedHistory = localStorage.getItem('spider-history')
  if (savedHistory) {
    spiderHistory.value = JSON.parse(savedHistory)
  }
})

// 保存历史记录
const saveHistory = () => {
  localStorage.setItem('spider-history', JSON.stringify(spiderHistory.value.slice(0, 20)))
}

import { watch } from 'vue'
watch(spiderHistory, saveHistory, { deep: true })
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.spider-tool {
  .page-header {
    margin-bottom: 20px;

    .card-header {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-weight: bold;
    }
  }

  .main-content {
    margin-bottom: 20px;

    .input-card, .result-card, .history-card {
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .header-actions {
          display: flex;
          gap: 0.5rem;
        }
      }

      .hint {
        font-size: 0.9rem;
        color: #666;
        margin-left: 0.5rem;
      }

      .loading-container {
        .progress-info {
          margin-top: 1rem;

          .progress-text {
            margin-bottom: 0.5rem;
            font-weight: bold;
          }
        }
      }

      .result-container {
        .content-summary {
          h4 {
            margin-bottom: 0.5rem;
          }

          .url-info {
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 1rem;
          }

          .content-preview {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 6px;
            line-height: 1.6;
            margin-bottom: 1rem;
          }
        }

        .full-content {
          pre {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 6px;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
          }
        }

        .image-list {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 1rem;
          max-height: 400px;
          overflow-y: auto;

          .image-item {
            text-align: center;

            img {
              width: 100%;
              height: 120px;
              object-fit: cover;
              border-radius: 4px;
            }

            .image-info {
              margin: 0.5rem 0;
              font-size: 0.9rem;
              color: #666;
            }
          }
        }

        .link-list {
          max-height: 400px;
          overflow-y: auto;

          .link-item {
            display: block;
            margin-bottom: 0.5rem;
            word-break: break-all;
          }
        }

        .result-actions {
          display: flex;
          gap: 0.5rem;
          margin-top: 1rem;
        }
      }
    }
  }

  .batch-card, .recommend-card {
    margin-bottom: 20px;

    .card-header {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-weight: bold;
    }

    .batch-results {
      margin-top: 1rem;
    }

    .site-card {
      cursor: pointer;
      transition: all 0.3s;

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      }

      .site-info {
        h4 {
          margin-bottom: 0.5rem;
        }

        p {
          color: #666;
          font-size: 0.9rem;
          margin-bottom: 0.5rem;
        }
      }
    }
  }
}
</style>