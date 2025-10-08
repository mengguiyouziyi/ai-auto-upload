<template>
  <div class="ai-workbench">
    <el-card class="page-header">
      <template #header>
        <div class="card-header">
          <el-icon><Tools /></el-icon>
          <span>AI创作工作台</span>
        </div>
      </template>
      <p>一站式AI内容创作，从文本优化到视频生成，再到社交发布</p>
    </el-card>

    <!-- 工作流程步骤 -->
    <el-card class="workflow-card">
      <template #header>
        <div class="card-header">
          <el-icon><Operation /></el-icon>
          <span>创作流程</span>
        </div>
      </template>

      <el-steps :active="currentStep" finish-status="success" align-center>
        <el-step title="输入创意" description="输入创作主题或抓取灵感" />
        <el-step title="文本优化" description="AI优化文案内容" />
        <el-step title="语音合成" description="生成自然语音" />
        <el-step title="视频生成" description="创作视频内容" />
        <el-step title="内容合成" description="合成最终媒体" />
        <el-step title="社交发布" description="发布到各平台" />
      </el-steps>
    </el-card>

    <el-row :gutter="20" class="main-content">
      <!-- 左侧：输入和配置 -->
      <el-col :span="8">
        <el-card class="input-card">
          <template #header>
            <div class="card-header">
              <span>创作配置</span>
              <el-button size="small" @click="resetWorkflow">重置</el-button>
            </div>
          </template>

          <el-form :model="workflow" label-width="100px">
            <el-form-item label="创作主题">
              <el-input
                v-model="workflow.topic"
                type="textarea"
                :rows="4"
                placeholder="请输入创作主题或粘贴灵感内容..."
                maxlength="1000"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="灵感来源">
              <el-radio-group v-model="workflow.inspiration_source">
                <el-radio label="manual">手动输入</el-radio>
                <el-radio label="spider">爬虫抓取</el-radio>
                <el-radio label="template">模板生成</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="内容类型">
              <el-select v-model="workflow.content_type" placeholder="选择内容类型">
                <el-option label="短视频" value="short_video" />
                <el-option label="教程视频" value="tutorial" />
                <el-option label="产品介绍" value="product" />
                <el-option label="知识分享" value="knowledge" />
                <el-option label="娱乐搞笑" value="entertainment" />
              </el-select>
            </el-form-item>

            <el-form-item label="目标平台">
              <el-select v-model="workflow.target_platforms" multiple placeholder="选择发布平台">
                <el-option label="抖音" value="douyin" />
                <el-option label="快手" value="kuaishou" />
                <el-option label="小红书" value="xiaohongshu" />
                <el-option label="B站" value="bilibili" />
                <el-option label="视频号" value="wechat" />
                <el-option label="百家号" value="baijiahao" />
              </el-select>
            </el-form-item>

            <el-form-item label="AI配置">
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="LLM提供商">
                  <el-select v-model="workflow.llm_provider" size="small">
                    <el-option label="豆包" value="doubao" />
                    <el-option label="文心" value="wenxin" />
                    <el-option label="通义千问" value="qwen" />
                  </el-select>
                </el-descriptions-item>
                <el-descriptions-item label="TTS提供商">
                  <el-select v-model="workflow.tts_provider" size="small">
                    <el-option label="Azure" value="azure_tts" />
                    <el-option label="阿里云" value="aliyun_tts" />
                    <el-option label="腾讯云" value="tencent_tts" />
                  </el-select>
                </el-descriptions-item>
                <el-descriptions-item label="视频提供商">
                  <el-select v-model="workflow.video_provider" size="small">
                    <el-option label="Runway" value="runway" />
                    <el-option label="Pika" value="pika" />
                    <el-option label="Stable Video" value="stable_video" />
                  </el-select>
                </el-descriptions-item>
              </el-descriptions>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="startWorkflow"
                :loading="workflowLoading"
                style="width: 100%"
              >
                <el-icon><CaretRight /></el-icon>
                开始创作
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 中间：实时进度和结果 -->
      <el-col :span="8">
        <el-card class="progress-card">
          <template #header>
            <div class="card-header">
              <span>创作进度</span>
              <el-tag :type="getStatusType(workflowStatus)">{{ getStatusText(workflowStatus) }}</el-tag>
            </div>
          </template>

          <div v-if="workflowLoading" class="workflow-progress">
            <div class="current-step">
              <h4>{{ getCurrentStepText() }}</h4>
              <el-progress :percentage="workflowProgress" :status="workflowProgressStatus" />
            </div>

            <div class="step-details">
              <div v-for="(step, index) in stepResults" :key="index" class="step-item">
                <div class="step-header">
                  <el-icon><Check v-if="step.status === 'completed'" /><Loading v-else-if="step.status === 'processing'" /><Clock v-else /></el-icon>
                  <span>{{ step.title }}</span>
                  <el-tag size="small" :type="getStepStatusType(step.status)">{{ getStepStatusText(step.status) }}</el-tag>
                </div>
                <div v-if="step.result" class="step-result">
                  <p>{{ step.result.summary }}</p>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="workflowResult" class="workflow-result">
            <el-tabs v-model="activeResultTab">
              <el-tab-pane label="最终结果" name="final">
                <div class="final-result">
                  <div class="result-preview">
                    <video
                      v-if="workflowResult.final_media_path"
                      controls
                      style="width: 100%; max-height: 200px;"
                    >
                      <source :src="workflowResult.final_media_path" type="video/mp4">
                    </video>
                    <div v-else class="no-preview">
                      <el-icon><VideoPlay /></el-icon>
                      <p>媒体文件生成完成</p>
                    </div>
                  </div>

                  <el-descriptions :column="1" border size="small">
                    <el-descriptions-item label="总时长">
                      {{ workflowResult.total_time?.toFixed(2) }}秒
                    </el-descriptions-item>
                    <el-descriptions-item label="场景数量">
                      {{ workflowResult.scenes_count }}个
                    </el-descriptions-item>
                    <el-descriptions-item label="文件大小">
                      {{ getFileSize(workflowResult.final_media_path) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="创作时间">
                      {{ new Date().toLocaleString() }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </el-tab-pane>

              <el-tab-pane label="成本分析" name="cost">
                <div class="cost-analysis">
                  <el-descriptions :column="1" border>
                    <el-descriptions-item v-for="(cost, key) in workflowResult.cost_breakdown" :key="key" :label="getCostLabel(key)">
                      ${{ cost?.toFixed(4) || '0.0000' }}
                    </el-descriptions-item>
                    <el-descriptions-item label="总成本">
                      <strong>${{ getTotalCost().toFixed(4) }}</strong>
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </el-tab-pane>

              <el-tab-pane label="日志记录" name="logs">
                <div class="workflow-logs">
                  <div v-for="(log, index) in workflowLogs" :key="index" class="log-item">
                    <span class="log-time">{{ log.time }}</span>
                    <span class="log-level" :class="log.level">{{ log.level }}</span>
                    <span class="log-message">{{ log.message }}</span>
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>

            <div class="result-actions">
              <el-button type="primary" @click="downloadResult">
                <el-icon><Download /></el-icon>
                下载作品
              </el-button>
              <el-button @click="publishToSocial">
                <el-icon><Share /></el-icon>
                发布到社交平台
              </el-button>
              <el-button @click="saveToLibrary">
                <el-icon><FolderAdd /></el-icon>
                保存到素材库
              </el-button>
            </div>
          </div>

          <el-empty v-else description="配置创作参数后点击开始创作" />
        </el-card>
      </el-col>

      <!-- 右侧：历史和模板 -->
      <el-col :span="8">
        <el-card class="templates-card">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>创作模板</span>
            </div>
          </template>

          <div class="template-list">
            <div
              v-for="template in templates"
              :key="template.id"
              class="template-item"
              @click="useTemplate(template)"
            >
              <div class="template-header">
                <h4>{{ template.name }}</h4>
                <el-tag size="small">{{ template.category }}</el-tag>
              </div>
              <p>{{ template.description }}</p>
              <div class="template-meta">
                <span>适合平台: {{ template.platforms.join(', ') }}</span>
              </div>
            </div>
          </div>
        </el-card>

        <el-card class="history-card" style="margin-top: 20px;">
          <template #header>
            <div class="card-header">
              <el-icon><Clock /></el-icon>
              <span>创作历史</span>
            </div>
          </template>

          <el-table
            :data="workflowHistory"
            stripe
            style="max-height: 300px; overflow-y: auto;"
          >
            <el-table-column prop="topic" label="主题" show-overflow-tooltip />
            <el-table-column prop="content_type" label="类型" width="80" />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'completed' ? 'success' : 'warning'" size="small">
                  {{ row.status === 'completed' ? '完成' : '进行中' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="100" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Tools, Operation, CaretRight, Check, Loading, Clock, VideoPlay, Download, Share, FolderAdd, Document } from '@element-plus/icons-vue'
import axios from 'axios'

const currentStep = ref(0)
const workflowLoading = ref(false)
const workflowProgress = ref(0)
const workflowProgressStatus = ref('')
const workflowStatus = ref('idle')
const workflowResult = ref(null)
const activeResultTab = ref('final')
const workflowLogs = ref([])
const workflowHistory = ref([])

const workflow = reactive({
  topic: '',
  inspiration_source: 'manual',
  content_type: 'short_video',
  target_platforms: ['douyin'],
  llm_provider: 'doubao',
  tts_provider: 'azure_tts',
  video_provider: 'runway'
})

const stepResults = ref([])

const templates = [
  {
    id: 1,
    name: '产品介绍模板',
    description: '适用于产品功能介绍和特色展示',
    category: '商业',
    platforms: ['抖音', '小红书']
  },
  {
    id: 2,
    name: '知识分享模板',
    description: '适用于知识科普和技能教学',
    category: '教育',
    platforms: ['B站', '视频号']
  },
  {
    id: 3,
    name: '生活日常模板',
    description: '适用于生活记录和日常分享',
    category: '生活',
    platforms: ['抖音', '快手']
  }
]

const startWorkflow = async () => {
  if (!workflow.topic.trim()) {
    ElMessage.warning('请输入创作主题')
    return
  }

  workflowLoading.value = true
  workflowStatus.value = 'running'
  currentStep.value = 0
  workflowProgress.value = 0
  stepResults.value = []
  workflowLogs.value = []

  addLog('info', '开始AI创作工作流程')

  try {
    // 步骤1: 文本优化
    currentStep.value = 1
    workflowProgress.value = 20
    addLog('info', '正在优化文本内容...')
    await sleep(2000)

    const textResult = await optimizeText(workflow.topic)
    stepResults.value.push({
      title: '文本优化',
      status: 'completed',
      result: { summary: '文本优化完成，生成了更适合视频的文案' }
    })
    addLog('success', '文本优化完成')

    // 步骤2: 语音合成
    currentStep.value = 2
    workflowProgress.value = 40
    addLog('info', '正在合成语音...')
    await sleep(3000)

    const audioResult = await generateAudio(textResult.optimized_text)
    stepResults.value.push({
      title: '语音合成',
      status: 'completed',
      result: { summary: `语音合成完成，时长${audioResult.duration}秒` }
    })
    addLog('success', '语音合成完成')

    // 步骤3: 视频生成
    currentStep.value = 3
    workflowProgress.value = 60
    addLog('info', '正在生成视频...')
    await sleep(4000)

    const videoResult = await generateVideo(textResult.optimized_text)
    stepResults.value.push({
      title: '视频生成',
      status: 'completed',
      result: { summary: `视频生成完成，时长${videoResult.duration}秒` }
    })
    addLog('success', '视频生成完成')

    // 步骤4: 内容合成
    currentStep.value = 4
    workflowProgress.value = 80
    addLog('info', '正在合成最终媒体...')
    await sleep(2000)

    const mediaResult = await combineMedia(videoResult, audioResult)
    stepResults.value.push({
      title: '内容合成',
      status: 'completed',
      result: { summary: '媒体文件合成完成' }
    })
    addLog('success', '内容合成完成')

    // 完成
    currentStep.value = 5
    workflowProgress.value = 100
    workflowProgressStatus.value = 'success'
    workflowStatus.value = 'completed'

    workflowResult.value = {
      ...mediaResult,
      final_media_path: `/storage/ai_workflow_${Date.now()}.mp4`,
      total_time: 15.5,
      scenes_count: 3,
      cost_breakdown: {
        'video_runway': 0.05,
        'audio_azure': 0.001,
        'text_doubao': 0.002
      }
    }

    workflowHistory.value.unshift({
      topic: workflow.topic,
      content_type: workflow.content_type,
      status: 'completed',
      created_at: new Date().toLocaleString()
    })

    addLog('success', 'AI创作工作流程完成！')
    ElMessage.success('AI创作完成！')

  } catch (error) {
    workflowStatus.value = 'error'
    workflowProgressStatus.value = 'exception'
    addLog('error', '创作流程失败: ' + error.message)
    ElMessage.error('创作失败: ' + error.message)
  } finally {
    workflowLoading.value = false
  }
}

const optimizeText = async (text) => {
  const response = await axios.post('http://localhost:9001/api/v1/llm/optimize-text', {
    text: text,
    provider: workflow.llm_provider
  })
  return response.data
}

const generateAudio = async (text) => {
  const response = await axios.post('http://localhost:9001/api/v1/tts/synthesize', {
    provider: workflow.tts_provider,
    text: text,
    voice: 'zh-CN-XiaoxiaoNeural',
    speed: 1.0
  })
  return response.data
}

const generateVideo = async (text) => {
  const response = await axios.post('http://localhost:9001/api/v1/video/generate', {
    provider: workflow.video_provider,
    text: text,
    duration: 10,
    quality: 'high'
  })
  return response.data
}

const combineMedia = async (video, audio) => {
  // 模拟媒体合成
  return {
    video_path: video.video_path,
    audio_path: audio.audio_path,
    duration: Math.max(video.duration || 10, audio.duration || 10)
  }
}

const resetWorkflow = () => {
  currentStep.value = 0
  workflowProgress.value = 0
  workflowStatus.value = 'idle'
  workflowResult.value = null
  stepResults.value = []
  workflowLogs.value = []
}

const downloadResult = () => {
  if (workflowResult?.final_media_path) {
    ElMessage.success('作品下载已开始')
  }
}

const publishToSocial = () => {
  if (workflowResult) {
    ElMessage.success('正在准备发布到社交平台...')
  }
}

const saveToLibrary = () => {
  if (workflowResult) {
    ElMessage.success('作品已保存到素材库')
  }
}

const useTemplate = (template) => {
  workflow.topic = template.name + ' - ' + template.description
  workflow.content_type = 'short_video'
  ElMessage.success(`已应用模板: ${template.name}`)
}

const addLog = (level, message) => {
  workflowLogs.value.push({
    time: new Date().toLocaleTimeString(),
    level: level,
    message: message
  })
}

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

const getStatusType = (status) => {
  const types = {
    'idle': 'info',
    'running': 'warning',
    'completed': 'success',
    'error': 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    'idle': '待开始',
    'running': '进行中',
    'completed': '已完成',
    'error': '失败'
  }
  return texts[status] || '未知'
}

const getCurrentStepText = () => {
  const steps = [
    '等待开始',
    '正在优化文本...',
    '正在合成语音...',
    '正在生成视频...',
    '正在合成媒体...',
    '创作完成！'
  ]
  return steps[currentStep.value] || '进行中'
}

const getStepStatusType = (status) => {
  const types = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return types[status] || 'info'
}

const getStepStatusText = (status) => {
  const texts = {
    'pending': '等待',
    'processing': '处理中',
    'completed': '完成',
    'failed': '失败'
  }
  return texts[status] || '未知'
}

const getCostLabel = (key) => {
  const labels = {
    'video_runway': 'Runway视频',
    'audio_azure': 'Azure语音',
    'text_doubao': '豆包文本'
  }
  return labels[key] || key
}

const getTotalCost = () => {
  if (!workflowResult?.cost_breakdown) return 0
  return Object.values(workflowResult.cost_breakdown).reduce((sum, cost) => sum + (cost || 0), 0)
}

const getFileSize = (path) => {
  // 模拟文件大小计算
  return '15.2 MB'
}

onMounted(() => {
  // 加载历史记录
  const savedHistory = localStorage.getItem('ai-workflow-history')
  if (savedHistory) {
    workflowHistory.value = JSON.parse(savedHistory)
  }
})

// 保存历史记录
const saveHistory = () => {
  localStorage.setItem('ai-workflow-history', JSON.stringify(workflowHistory.value.slice(0, 20)))
}

import { watch } from 'vue'
watch(workflowHistory, saveHistory, { deep: true })
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.ai-workbench {
  .page-header {
    margin-bottom: 20px;

    .card-header {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-weight: bold;
    }
  }

  .workflow-card {
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

    .input-card, .progress-card, .templates-card, .history-card {
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: bold;
      }
    }

    .progress-card {
      .workflow-progress {
        .current-step {
          margin-bottom: 1rem;

          h4 {
            margin-bottom: 0.5rem;
          }
        }

        .step-details {
          max-height: 400px;
          overflow-y: auto;

          .step-item {
            margin-bottom: 1rem;
            padding: 0.5rem;
            background: #f8f9fa;
            border-radius: 6px;

            .step-header {
              display: flex;
              align-items: center;
              gap: 0.5rem;
              margin-bottom: 0.5rem;

              .el-icon {
                font-size: 1rem;
              }
            }

            .step-result {
              padding-left: 1.5rem;

              p {
                margin: 0;
                color: #666;
                font-size: 0.9rem;
              }
            }
          }
        }
      }

      .workflow-result {
        .final-result {
          .result-preview {
            margin-bottom: 1rem;

            .no-preview {
              text-align: center;
              padding: 2rem;
              background: #f5f5f5;
              border-radius: 6px;

              .el-icon {
                font-size: 2rem;
                color: #666;
                margin-bottom: 0.5rem;
              }

              p {
                margin: 0;
                color: #666;
              }
            }
          }

          .result-actions {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
          }
        }

        .workflow-logs {
          max-height: 300px;
          overflow-y: auto;
          background: #f8f9fa;
          padding: 1rem;
          border-radius: 6px;

          .log-item {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;

            .log-time {
              color: #666;
              min-width: 80px;
            }

            .log-level {
              min-width: 50px;
              font-weight: bold;

              &.info { color: #409eff; }
              &.success { color: #67c23a; }
              &.warning { color: #e6a23c; }
              &.error { color: #f56c6c; }
            }

            .log-message {
              flex: 1;
            }
          }
        }
      }
    }

    .templates-card {
      .template-list {
        max-height: 350px;
        overflow-y: auto;

        .template-item {
          padding: 1rem;
          border: 1px solid #e4e7ed;
          border-radius: 6px;
          margin-bottom: 0.5rem;
          cursor: pointer;
          transition: all 0.3s;

          &:hover {
            border-color: #409eff;
            background: #f0f9ff;
          }

          .template-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;

            h4 {
              margin: 0;
            }
          }

          p {
            margin: 0 0 0.5rem 0;
            color: #666;
            font-size: 0.9rem;
          }

          .template-meta {
            font-size: 0.8rem;
            color: #999;
          }
        }
      }
    }
  }
}
</style>