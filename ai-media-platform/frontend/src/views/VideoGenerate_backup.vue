<template>
  <div class="video-generate">
    <el-card class="page-header">
      <template #header>
        <div class="card-header">
          <el-icon><VideoPlay /></el-icon>
          <span>AI视频生成</span>
        </div>
      </template>
      <p>使用AI根据文本描述生成视频内容</p>
    </el-card>

    <el-row :gutter="20" class="main-content">
      <el-col :span="8">
        <el-card class="input-card">
          <template #header>
            <div class="card-header">
              <span>生成设置</span>
            </div>
          </template>

          <el-form :model="form" label-width="100px">
            <el-form-item label="视频提供商">
              <el-select v-model="form.provider" placeholder="选择视频生成提供商" @change="onProviderChange">
                <el-option label="🌟 ComfyUI Wan 2.2 (标准工作流)" value="comfyui_wan" />
                <el-option label="🆓 免费开源AI风格 (本地)" value="simple_open" />
                <el-option label="💻 本地GPU服务器" value="local_gpu" />
              </el-select>
              <div class="provider-info" v-if="currentProvider">
                <span class="provider-desc">{{ currentProvider.description }}</span>
                <span class="provider-limit">最大时长: {{ currentProvider.max_duration }}秒, 最大分辨率: {{ currentProvider.max_resolution }}</span>
              </div>
            </el-form-item>

            <el-form-item label="导入优化文本">
              <el-button
                type="info"
                size="small"
                @click="importOptimizedText"
                :disabled="!hasOptimizedText"
                style="width: 100%"
              >
                <el-icon><Download /></el-icon>
                {{ hasOptimizedText ? '导入优化后的文本' : '无优化文本可用' }}
              </el-button>
              <span v-if="hasOptimizedText" class="optimized-text-hint">
                发现来自文本优化的内容
              </span>
            </el-form-item>

            <el-form-item label="视频描述">
              <div class="prompt-template-section">
                <el-button
                  type="info"
                  size="small"
                  @click="showPromptTemplates = !showPromptTemplates"
                  style="margin-bottom: 8px;"
                >
                  <el-icon><Document /></el-icon>
                  {{ showPromptTemplates ? '隐藏' : '显示' }}Prompt模板
                </el-button>

                <div v-if="showPromptTemplates" class="prompt-templates">
                  <el-button
                    v-for="(template, index) in promptTemplates"
                    :key="index"
                    size="small"
                    @click="usePromptTemplate(template)"
                    style="margin: 2px;"
                  >
                    {{ template.name }}
                  </el-button>
                </div>
              </div>

              <el-input
                v-model="form.prompt"
                type="textarea"
                :rows="8"
                placeholder="描述你想要生成的视频内容，支持场景首尾相接的描述..."
                maxlength="5000"
                show-word-limit
              />
              <div class="prompt-hint">
                💡 提示：系统会自动优化prompt，使场景首尾相接，提升视频流畅度
              </div>
            </el-form-item>

            <el-form-item label="视频时长">
              <el-slider
                v-model="form.duration"
                :min="3"
                :max="30"
                :step="1"
                show-input
              />
              <span class="hint">{{ form.duration }}秒</span>
            </el-form-item>

            <el-form-item label="视频质量">
              <el-radio-group v-model="form.quality">
                <el-radio label="low">低质量</el-radio>
                <el-radio label="medium">中等质量</el-radio>
                <el-radio label="high">高质量</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="风格">
              <el-input
                v-model="form.style"
                placeholder="例如：赛博朋克、水彩画、写实风格等"
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="generateVideo"
                :loading="loading"
                style="width: 100%"
              >
                <el-icon><Tools /></el-icon>
                生成视频
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="progress-card">
          <template #header>
            <div class="card-header">
              <span>生成进度</span>
            </div>
          </template>

          <div v-if="loading" class="progress-container">
            <el-progress
              type="circle"
              :percentage="progress"
              :status="progressStatus"
            />
            <div class="progress-info">
              <p class="progress-text">{{ progressText }}</p>
              <p class="progress-time">已用时: {{ formatTime(elapsedTime) }}</p>
              <div class="current-prompt" v-if="form.prompt">
                <el-text type="info" size="small">当前描述: </el-text>
                <el-text size="small" class="prompt-text">{{ form.prompt }}</el-text>
              </div>
            </div>
          </div>

          <div v-else-if="result" class="result-container">
            <div class="video-preview">
              <div v-if="getVideoUrl(result)">
                <video
                  v-if="!result.isImage && !isWebP(getVideoUrl(result))"
                  controls
                  autoplay
                  loop
                  muted
                  style="width: 100%; max-height: 300px;"
                  @error="handleVideoError"
                  @loadeddata="handleVideoLoaded"
                  key="video-player"
                >
                  <!-- 优先使用本地MP4格式 -->
                  <source v-if="isMP4(getVideoUrl(result))" :src="getVideoUrl(result)" type="video/mp4">
                  <source :src="getVideoUrl(result)" type="video/mp4">
                  <source :src="getVideoUrl(result)" type="video/webm">
                  <source :src="getProxyUrl(getVideoUrl(result))">
                </video>
                <div v-else class="image-preview">
                  <img
                    :src="getVideoUrl(result)"
                    style="width: 100%; max-height: 300px;"
                    alt="AI生成的动图/图片"
                    @error="handleImageError"
                  >
                  <div class="image-controls">
                    <el-button size="small" @click="openVideoInNewTab">
                      <el-icon><Link /></el-icon>
                      新窗口打开
                    </el-button>
                    <el-button size="small" @click="downloadVideo">
                      <el-icon><Download /></el-icon>
                      下载文件
                    </el-button>
                  </div>
                </div>
              </div>
              <div v-else class="no-video">
                <el-icon><VideoPlay /></el-icon>
                <p>视频生成完成，但无法预览</p>
                <el-button type="primary" size="small" @click="openVideoInNewTab" v-if="getVideoUrl(result)">
                  <el-icon><Link /></el-icon>
                  在新标签页打开
                </el-button>
              </div>
            </div>

            <div class="result-info">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="视频描述" v-if="result.prompt">
                  <el-text class="prompt-display">{{ result.prompt }}</el-text>
                </el-descriptions-item>
                <el-descriptions-item label="视频时长">
                  {{ result.duration || '未知' }}秒
                </el-descriptions-item>
                <el-descriptions-item label="文件大小">
                  {{ formatFileSize(result.file_size) }}
                </el-descriptions-item>
                <el-descriptions-item label="生成时间">
                  {{ result.generation_time || '未知' }}秒
                </el-descriptions-item>
                <el-descriptions-item label="分辨率">
                  {{ result.width || '未知' }}×{{ result.height || '未知' }}
                </el-descriptions-item>
                <el-descriptions-item label="帧率">
                  {{ result.fps || '未知' }} FPS
                </el-descriptions-item>
                <el-descriptions-item label="费用" v-if="result.cost">
                  ${{ result.cost }}
                </el-descriptions-item>
                <el-descriptions-item label="生成时间戳" v-if="result.created_at">
                  {{ formatDateTime(result.created_at) }}
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <div class="result-actions">
              <el-button type="primary" @click="downloadVideo">
                <el-icon><Download /></el-icon>
                下载视频
              </el-button>
              <el-button type="success" @click="addToMaterialLibrary" :loading="addToMaterialLoading">
                <el-icon><FolderAdd /></el-icon>
                添加到素材库
              </el-button>
              <el-button @click="useVideoForSocial">
                <el-icon><Share /></el-icon>
                发布到社交平台
              </el-button>
            </div>
          </div>

          <el-empty v-else description="设置参数并点击生成视频开始创作" />
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="history-card">
          <template #header>
            <div class="card-header">
              <el-icon><Clock /></el-icon>
              <span>生成历史</span>
            </div>
          </template>

          <el-table
            :data="videoHistory"
            stripe
            style="max-height: 500px; overflow-y: auto;"
          >
            <el-table-column prop="prompt" label="描述" show-overflow-tooltip min-width="200">
              <template #default="{ row }">
                <el-text size="small" :title="row.prompt">{{ truncateText(row.prompt, 30) }}</el-text>
              </template>
            </el-table-column>
            <el-table-column prop="provider" label="提供商" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ row.provider }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="140">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row, $index }">
                <el-button type="text" size="small" @click="showHistoryDetail(row, $index)">
                  <el-icon><View /></el-icon>
                  详情
                </el-button>
                <el-button type="text" size="small" @click="useHistoryVideo(row)" v-if="row.video_url">
                  <el-icon><VideoPlay /></el-icon>
                  使用
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 历史详情展开面板 -->
          <el-collapse v-if="selectedHistory" class="history-detail-panel">
            <el-collapse-item name="detail" title="详细信息">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="完整描述" span="2">
                  <el-text>{{ selectedHistory.prompt }}</el-text>
                </el-descriptions-item>
                <el-descriptions-item label="提供商">
                  <el-tag size="small">{{ selectedHistory.provider }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="创建时间">
                  {{ formatDateTime(selectedHistory.created_at) }}
                </el-descriptions-item>
                <el-descriptions-item label="视频时长">
                  {{ selectedHistory.duration || 0 }}秒
                </el-descriptions-item>
                <el-descriptions-item label="文件大小">
                  {{ formatFileSize(selectedHistory.file_size) }}
                </el-descriptions-item>
                <el-descriptions-item label="生成耗时">
                  {{ selectedHistory.generation_time || 0 }}秒
                </el-descriptions-item>
                <el-descriptions-item label="分辨率">
                  {{ selectedHistory.width || 0 }}×{{ selectedHistory.height || 0 }}
                </el-descriptions-item>
                <el-descriptions-item label="帧率">
                  {{ selectedHistory.fps || 0 }} FPS
                </el-descriptions-item>
                <el-descriptions-item label="操作" span="2">
                  <el-button type="primary" size="small" @click="useHistoryVideo(selectedHistory)" v-if="selectedHistory.video_url">
                    <el-icon><VideoPlay /></el-icon>
                    使用此视频
                  </el-button>
                  <el-button size="small" @click="previewVideo(selectedHistory)">
                    <el-icon><View /></el-icon>
                    预览视频
                  </el-button>
                </el-descriptions-item>
              </el-descriptions>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoPlay, Tools, Download, Share, Clock, Document, Link, FolderAdd, View } from '@element-plus/icons-vue'
import { http } from '@/utils/request'

const router = useRouter()

const loading = ref(false)
const result = ref(null)
const progress = ref(0)
const progressStatus = ref('')
const progressText = ref('')
const elapsedTime = ref(0)
const videoHistory = ref([])
const showPromptTemplates = ref(false)
const addToMaterialLoading = ref(false)
const selectedHistory = ref(null)

// 场景首尾相接的prompt模板
const promptTemplates = ref([
  {
    name: '科技开场',
    prompt: '【场景1：科技感视频开场】屏幕上出现动态的代码行，背景是抽象的数字网格，代码行随着节奏逐渐构建出炫酷的界面，最后形成完整的科技logo'
  },
  {
    name: '自然风光',
    prompt: '【场景1：山水美景】从远山开始，镜头逐渐推近，展现层峦叠嶂的山脉，云雾缭绕其间，阳光穿透云层洒在山间，形成美丽的光影效果，最后镜头停留在平静的湖面上'
  },
  {
    name: '城市夜景',
    prompt: '【场景1：城市夜景】从高空俯瞰城市的璀璨夜景，万家灯火如同繁星点点，车流如织形成光带，摩天大楼的霓虹灯闪烁，展现现代都市的繁华与活力'
  },
  {
    name: '抽象艺术',
    prompt: '【场景1：抽象艺术】色彩斑斓的几何图形在空间中舞动，形状不断变化融合，从简单的圆形逐渐演变成复杂的图案，色彩过渡自然流畅'
  },
  {
    name: '动物世界',
    prompt: '【场景1：动物世界】一只雄鹰在雪山之巅翱翔，背景是壮丽的雪山和蓝天，镜头跟随雄鹰的飞行轨迹，展现大自然的壮美'
  }
])

const form = reactive({
  provider: 'comfyui_wan',
  prompt: '【场景1：科技感视频开场】屏幕上出现动态的代码行，背景是抽象的数字网格，代码行随着节奏逐渐构建出炫酷的界面，最后形成完整的科技logo，电影级视觉效果',
  duration: 10,  // 增加默认视频时长
  quality: 'high',
  style: '',
  width: 720,
  height: 720,
  fps: 30,
  aspect_ratio: '16:9'
})

const providers = ref([])
const currentProvider = ref(null)

// 检查是否有优化后的文本
const hasOptimizedText = computed(() => {
  return localStorage.getItem('optimized-text-for-video') !== null
})

// 检查是否为WebP格式
const isWebP = (url) => {
  if (!url) return false
  return url.toLowerCase().includes('.webp') || url.toLowerCase().includes('.gif')
}

const isMP4 = (url) => {
  if (!url) return false
  return url.toLowerCase().includes('.mp4')
}

// 导入优化后的文本
const importOptimizedText = () => {
  const optimizedText = localStorage.getItem('optimized-text-for-video')
  if (optimizedText) {
    try {
      const content = JSON.parse(optimizedText)
      form.prompt = content.text
      ElMessage.success(`已导入优化文本 (来源: ${content.provider})`)
      // 导入后清除localStorage，避免重复导入
      localStorage.removeItem('optimized-text-for-video')
    } catch (error) {
      ElMessage.error('导入优化文本失败')
    }
  } else {
    ElMessage.warning('没有找到优化后的文本')
  }
}

const usePromptTemplate = (template) => {
  form.prompt = template.prompt
  ElMessage.success(`已使用"${template.name}"模板`)
  showPromptTemplates.value = false
}

let progressTimer = null
let startTime = null

const generateVideo = async () => {
  if (!form.prompt.trim()) {
    ElMessage.warning('请输入视频描述')
    return
  }

  loading.value = true
  progress.value = 0
  progressStatus.value = ''
  progressText.value = '正在初始化...'
  elapsedTime.value = 0
  startTime = Date.now()

  // 模拟进度更新
  progressTimer = setInterval(() => {
    if (progress.value < 90) {
      progress.value += Math.random() * 20
      if (progress.value > 90) progress.value = 90

      if (progress.value < 30) {
        progressText.value = '正在处理视频描述...'
      } else if (progress.value < 60) {
        progressText.value = '正在生成视频内容...'
      } else if (progress.value < 90) {
        progressText.value = '正在优化视频质量...'
      }
    }
    elapsedTime.value = Math.floor((Date.now() - startTime) / 1000)
  }, 2000)

  try {
    console.log('发送视频生成请求...', {
      provider: form.provider,
      prompt: form.prompt.substring(0, 50) + '...',
      duration: form.duration
    })

    const response = await http.post('/api/v1/video/generate', {
      provider: form.provider,
      prompt: form.prompt,
      duration: form.duration,
      quality: form.quality,
      style: form.style,
      width: form.width,
      height: form.height,
      fps: form.fps,
      aspect_ratio: form.aspect_ratio
    })

    console.log('收到API响应:', response)

    clearInterval(progressTimer)
    progress.value = 100
    progressStatus.value = 'success'
    progressText.value = '生成完成！'

    if (response.success) {
      result.value = response.data
      videoHistory.value.unshift({
        ...response.data,
        prompt: form.prompt,
        provider: form.provider,
        created_at: new Date().toLocaleString()
      })
    } else {
      throw new Error(response.message || '生成失败')
    }

    ElMessage.success('视频生成完成')
  } catch (error) {
    clearInterval(progressTimer)
    progressStatus.value = 'exception'
    progressText.value = '生成失败'

    console.error('生成失败:', error)
    let errorMsg = '生成失败'
    if (error.response?.data?.detail) {
      errorMsg = error.response.data.detail
    } else if (error.response?.data?.message) {
      errorMsg = error.response.data.message
    } else if (error.message) {
      errorMsg = error.message
    } else if (typeof error === 'object') {
      errorMsg = JSON.stringify(error)
    }
    ElMessage.error('生成失败: ' + errorMsg)
  } finally {
    loading.value = false
    clearInterval(progressTimer)
  }
}

const downloadVideo = () => {
  const url = getVideoUrl(result.value)
  if (url) {
    // 创建下载链接
    const a = document.createElement('a')
    a.href = url
    a.style.display = 'none'

    // 处理跨域下载 - 先fetch再下载
    fetch(url)
      .then(response => {
        if (!response.ok) {
          throw new Error('网络请求失败')
        }
        return response.blob()
      })
      .then(blob => {
        const blobUrl = window.URL.createObjectURL(blob)
        a.href = blobUrl

        // 根据URL确定文件扩展名 - 智能检测
        let extension = 'mp4'  // 默认为MP4

        if (isWebP(url)) {
          extension = 'webp'
        } else if (isMP4(url)) {
          extension = 'mp4'
        } else if (url.toLowerCase().includes('.webm')) {
          extension = 'webm'
        } else if (url.toLowerCase().includes('.gif')) {
          extension = 'gif'
        }

        const filename = `ai_video_${Date.now()}.${extension}`

        a.download = filename
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)

        // 清理blob URL
        window.URL.revokeObjectURL(blobUrl)

        ElMessage.success(`${extension === 'webp' ? '动图' : '视频'}下载已开始`)
      })
      .catch(error => {
        console.error('下载失败:', error)
        // 降级方案：直接链接下载
        const extension = isWebP(url) ? 'webp' : 'mp4'
        const filename = `ai_video_${Date.now()}.${extension}`
        a.download = filename
        a.target = '_blank'
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        ElMessage.warning('尝试直接打开下载，如果无法下载请右键另存为')
      })
  }
}

const useVideoForSocial = () => {
  if (result.value) {
    // 跳转到发布中心并传递视频数据
    // 生成基于prompt的视频标题（取前20个字符）
    const promptTitle = form.prompt ? form.prompt.substring(0, 20) : 'AI视频'
    const videoData = {
      url: getVideoUrl(result.value),
      name: promptTitle,
      size: result.value.file_size || 0,
      duration: result.value.duration || 0,
      prompt: form.prompt,
      provider: form.provider
    }

    // 将视频数据存储到localStorage供发布中心使用
    localStorage.setItem('video-for-publish', JSON.stringify(videoData))

    // 跳转到发布中心
    router.push('/publish-center')
    ElMessage.success('视频已准备，即将跳转到发布中心')
  }
}

// 添加视频到素材库
const addToMaterialLibrary = async () => {
  if (!result.value) {
    ElMessage.warning('没有可添加的视频')
    return
  }

  addToMaterialLoading.value = true

  try {
    console.log('🚀 开始addToMaterialLibrary方法')

    const videoUrl = getVideoUrl(result.value)
    if (!videoUrl) {
      ElMessage.error('视频链接无效')
      return
    }

    console.log('🎬 开始下载视频:', videoUrl)

    // 下载视频文件
    const downloadResponse = await fetch(videoUrl)
    if (!downloadResponse.ok) {
      throw new Error(`下载视频失败: ${downloadResponse.status} ${downloadResponse.statusText}`)
    }

    console.log('✅ 视频下载成功，开始处理文件')

    // 简化方案：直接使用原始的fetch和FormData
    const fileExtension = result.value.video_info?.local_video_url?.includes('.mp4') ? 'mp4' : 'webp'
    const formData = new FormData()

    // 直接从URL创建文件引用，避免大文件处理问题
    try {
      // 使用fetch获取响应的arrayBuffer，然后创建File对象
      const response = await fetch(videoUrl)
      if (!response.ok) {
        throw new Error(`获取视频文件失败: ${response.status}`)
      }

      const arrayBuffer = await response.arrayBuffer()
      // 生成基于prompt的文件名（取前20个字符）
      const promptTitle = form.prompt ? form.prompt.substring(0, 20) : 'AI视频'
      const fileName = `${promptTitle}.${fileExtension}`

      // 创建File对象
      const file = new File([arrayBuffer], fileName, {
        type: fileExtension === 'mp4' ? 'video/mp4' : 'image/webp'
      })

      formData.append('file', file)
      formData.append('filename', fileName)

      console.log('📋 简化FormData创建完成:', {
        fileName,
        fileSize: (file.size / 1024 / 1024).toFixed(2) + 'MB',
        fileType: file.type
      })

    } catch (fileError) {
      console.error('文件创建失败:', fileError)
      throw new Error('视频文件处理失败')
    }

    console.log('📤 开始上传到素材库...')

    // 直接使用fetch上传，避免axios的复杂性
    const uploadResponse = await fetch('http://localhost:9000/uploadSave', {
      method: 'POST',
      body: formData
    })
      if (uploadResponse.ok) {
      const responseData = await uploadResponse.json()
      console.log('✅ 上传响应:', responseData)

      if (responseData.code === 200) {
        ElMessage.success(`视频已成功添加到素材库`)
        console.log('🎉 添加到素材库成功')

        // 跳转到素材库页面
        setTimeout(() => {
          console.log('🔗 准备跳转到素材库页面')
          router.push('/material-management')
        }, 1500)
      } else {
        throw new Error(responseData.msg || '服务器返回错误')
      }
    } else {
      throw new Error(`HTTP错误: ${uploadResponse.status}`)
    }

  } catch (error) {
    console.error('❌ 添加到素材库失败:', error)

    let errorMessage = '添加到素材库失败'
    if (error.response?.data?.msg) {
      errorMessage += `: ${error.response.data.msg}`
    } else if (error.message) {
      errorMessage += `: ${error.message}`
    } else {
      errorMessage += ': 未知错误'
    }

    ElMessage.error(errorMessage)
  } finally {
    addToMaterialLoading.value = false
  }
}

const formatFileSize = (bytes) => {
  if (!bytes) return '未知'
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  if (bytes === 0) return '0 Bytes'
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatDateTime = (dateString) => {
  if (!dateString) return '未知'
  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (error) {
    return '未知'
  }
}

// 获取视频提供商信息
const loadProviders = async () => {
  try {
    const response = await http.get('/api/v1/video/providers')
    if (response.data.success) {
      providers.value = response.data.data
      // 设置当前提供商信息
      onProviderChange()
    }
  } catch (error) {
    console.error('获取提供商信息失败:', error)
  }
}

// 处理提供商变更
const onProviderChange = () => {
  currentProvider.value = providers.value.find(p => p.value === form.provider) || null
  // 根据提供商调整默认参数
  if (currentProvider.value) {
    form.duration = Math.min(form.duration, currentProvider.value.max_duration)
    if (currentProvider.value.default_fps) {
      form.fps = currentProvider.value.default_fps
    }
  }
}

onMounted(() => {
  // 加载提供商信息
  loadProviders()
  // 加载历史记录
  const savedHistory = localStorage.getItem('video-generate-history')
  if (savedHistory) {
    videoHistory.value = JSON.parse(savedHistory)
  }
})

const handleVideoError = (event) => {
  console.error('视频加载失败:', event)
  const videoElement = event.target
  const src = videoElement.querySelector('source')?.src

  if (src) {
    // 如果是WebP文件，尝试作为图片显示
    if (isWebP(src)) {
      result.value.isImage = true
      ElMessage.info('检测到动图文件，切换为图片显示')
    } else {
      ElMessage.error('视频加载失败，可能是文件格式不支持')
    }
  }
}

const handleVideoLoaded = (event) => {
  console.log('视频加载成功')
  ElMessage.success('视频加载完成')
}

const handleImageError = (event) => {
  console.error('图片加载失败:', event)
  ElMessage.error('图片加载失败')
}

const openVideoInNewTab = () => {
  const url = getVideoUrl(result.value)
  if (url) {
    window.open(url, '_blank')
  }
}

// 获取代理URL（用于跨域问题）
const getProxyUrl = (url) => {
  // 如果URL已经是完整的，直接返回
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  // 否则构建完整URL
  return `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:9000'}/${url}`
}

// 获取视频URL，优先使用本地视频URL
const getVideoUrl = (result) => {
  // 优先使用本地视频URL
  if (result.video_info?.local_video_url) {
    return result.video_info.local_video_url
  }
  // 其次使用传统的video_url
  if (result.video_url) {
    return result.video_url
  }
  // 最后使用video_path
  if (result.video_path) {
    return result.video_path
  }
  return null
}

// ComfyUI服务器配置
const COMFYUI_SERVER = 'http://192.168.1.246:8188'  // 双GPU视频生成服务器

// 截断文本
const truncateText = (text, maxLength) => {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

// 显示历史详情
const showHistoryDetail = (historyItem) => {
  selectedHistory.value = historyItem
}

// 使用历史视频
const useHistoryVideo = (historyItem) => {
  result.value = historyItem
  ElMessage.success('已使用历史视频')
}

// 预览视频
const previewVideo = (historyItem) => {
  const url = getVideoUrl(historyItem)
  if (url) {
    window.open(url, '_blank')
  } else {
    ElMessage.warning('无法预览该视频')
  }
}

// 保存历史记录
const saveHistory = () => {
  localStorage.setItem('video-generate-history', JSON.stringify(videoHistory.value.slice(0, 20)))
}

import { watch } from 'vue'
watch(videoHistory, saveHistory, { deep: true })
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.video-generate {
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

    .input-card {
      .card-header {
        font-weight: bold;
      }

      .hint {
        font-size: 0.9rem;
        color: #666;
        margin-left: 0.5rem;
      }

      .optimized-text-hint {
        margin-left: 0.5rem;
        font-size: 0.9rem;
        color: #67c23a;
      }

      .provider-info {
        margin-top: 8px;
        padding: 8px;
        background-color: #f5f7fa;
        border-radius: 4px;
        font-size: 0.9rem;

        .provider-desc {
          display: block;
          color: #606266;
          margin-bottom: 4px;
        }

        .provider-limit {
          display: block;
          color: #909399;
          font-size: 0.85rem;
        }
      }

      .prompt-template-section {
        margin-bottom: 8px;

        .prompt-templates {
          margin-top: 8px;
          padding: 12px;
          background-color: #f8f9fa;
          border-radius: 6px;
          border: 1px solid #e4e7ed;

          .el-button {
            margin: 2px 4px 2px 0;
          }
        }
      }

      .prompt-hint {
        margin-top: 8px;
        padding: 8px 12px;
        background-color: #f0f9ff;
        border-left: 4px solid #409eff;
        border-radius: 4px;
        font-size: 0.85rem;
        color: #606266;
      }
    }

    .progress-card {
      .card-header {
        font-weight: bold;
      }

      .progress-container {
        text-align: center;

        .progress-info {
          margin-top: 1rem;

          .progress-text {
            font-weight: bold;
            margin-bottom: 0.5rem;
          }

          .progress-time {
            color: #666;
            font-size: 0.9rem;
          }
        }
      }

      .result-container {
        .video-preview {
          margin-bottom: 1rem;

          .no-video {
            text-align: center;
            padding: 2rem;
            background: #f5f5f5;
            border-radius: 6px;

            .el-icon {
              font-size: 3rem;
              color: #666;
              margin-bottom: 0.5rem;
            }

            p {
              color: #666;
              margin: 0;
            }
          }
        }

        .result-actions {
          display: flex;
          gap: 0.5rem;
          margin-top: 1rem;
        }

        .image-controls {
          display: flex;
          justify-content: center;
          gap: 0.5rem;
          margin-top: 0.5rem;
        }
      }
    }

    .history-card {
      .card-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: bold;
      }

      .history-detail-panel {
        margin-top: 1rem;
        border: 1px solid #e4e7ed;
        border-radius: 6px;

        .el-collapse-item__header {
          font-weight: bold;
          color: #409eff;
        }
      }
    }

    .current-prompt {
      margin-top: 0.5rem;
      padding: 0.5rem;
      background-color: #f8f9fa;
      border-radius: 4px;
      border-left: 3px solid #409eff;

      .prompt-text {
        font-style: italic;
        color: #606266;
        word-break: break-word;
      }
    }

    .prompt-display {
      color: #606266;
      font-weight: 500;
      word-break: break-word;
    }
  }
}
</style>