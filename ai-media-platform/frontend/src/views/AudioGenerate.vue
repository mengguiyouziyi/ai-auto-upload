<template>
  <div class="audio-generate">
    <el-card class="page-header">
      <template #header>
        <div class="card-header">
          <el-icon><Microphone /></el-icon>
          <span>AI语音合成</span>
        </div>
      </template>
      <p>使用AI将文本转换为自然语音</p>
    </el-card>

    <el-row :gutter="20" class="main-content">
      <el-col :span="8">
        <el-card class="input-card">
          <template #header>
            <div class="card-header">
              <span>合成设置</span>
            </div>
          </template>

          <el-form :model="form" label-width="100px">
            <el-form-item label="TTS提供商">
              <el-select v-model="form.provider" placeholder="选择语音合成提供商">
                <el-option label="Azure TTS" value="azure_tts" />
                <el-option label="阿里云TTS" value="aliyun_tts" />
                <el-option label="腾讯云TTS" value="tencent_tts" />
                <el-option label="OpenAI TTS" value="openai_tts" />
                <el-option label="百度TTS" value="baidu_tts" />
              </el-select>
            </el-form-item>

            <el-form-item label="合成文本">
              <el-input
                v-model="form.text"
                type="textarea"
                :rows="8"
                placeholder="请输入需要转换为语音的文本内容..."
                maxlength="5000"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="语音选择">
              <el-select
                v-model="form.voice"
                placeholder="选择语音风格"
                filterable
              >
                <el-option
                  v-for="voice in voiceOptions"
                  :key="voice.value"
                  :label="voice.label"
                  :value="voice.value"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="语速调节">
              <el-slider
                v-model="form.speed"
                :min="0.25"
                :max="4.0"
                :step="0.25"
                show-input
              />
              <span class="hint">{{ form.speed }}倍速</span>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="generateAudio"
                :loading="loading"
                style="width: 100%"
              >
                <el-icon><Tools /></el-icon>
                合成语音
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="player-card">
          <template #header>
            <div class="card-header">
              <span>语音播放</span>
              <div class="header-actions">
                <el-button size="small" @click="downloadAudio" v-if="result">
                  <el-icon><Download /></el-icon>
                  下载
                </el-button>
                <el-button size="small" @click="clearResult" v-if="result">
                  <el-icon><Delete /></el-icon>
                  清空
                </el-button>
              </div>
            </div>
          </template>

          <div v-if="loading" class="loading-container">
            <el-skeleton :rows="4" animated />
            <p class="loading-text">AI正在合成中...</p>
          </div>

          <div v-else-if="result" class="player-container">
            <div class="audio-player">
              <audio
                ref="audioPlayer"
                controls
                style="width: 100%"
                @timeupdate="onTimeUpdate"
                @ended="onPlayEnd"
              >
                <source :src="result.audio_path" type="audio/mpeg">
                您的浏览器不支持音频播放
              </audio>
            </div>

            <div class="waveform" v-if="waveformData.length > 0">
              <div class="waveform-container">
                <div
                  v-for="(bar, index) in waveformData"
                  :key="index"
                  class="waveform-bar"
                  :style="{ height: bar + '%' }"
                ></div>
              </div>
            </div>

            <div class="audio-info">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="音频时长">
                  {{ formatDuration(result.duration) }}
                </el-descriptions-item>
                <el-descriptions-item label="文件大小">
                  {{ formatFileSize(result.file_size) }}
                </el-descriptions-item>
                <el-descriptions-item label="生成时间">
                  {{ result.generation_time }}秒
                </el-descriptions-item>
                <el-descriptions-item label="文本长度">
                  {{ form.text.length }}字符
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <div class="action-buttons">
              <el-button @click="playPause">
                <el-icon><VideoPlay v-if="!isPlaying" /><VideoPause v-else /></el-icon>
                {{ isPlaying ? '暂停' : '播放' }}
              </el-button>
              <el-button @click="useAudioForVideo">
                <el-icon><Connection /></el-icon>
                用于视频配音
              </el-button>
            </div>
          </div>

          <el-empty v-else description="设置参数并点击合成语音开始创作" />
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="history-card">
          <template #header>
            <div class="card-header">
              <el-icon><Clock /></el-icon>
              <span>合成历史</span>
            </div>
          </template>

          <el-table
            :data="audioHistory"
            stripe
            style="max-height: 500px; overflow-y: auto;"
          >
            <el-table-column prop="text" label="文本内容" show-overflow-tooltip />
            <el-table-column prop="provider" label="提供商" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ row.provider }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="duration" label="时长" width="80">
              <template #default="{ row }">
                {{ formatDuration(row.duration) }}
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="120" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button size="small" @click="playAudio(row)">播放</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 批量合成 -->
    <el-card class="batch-card">
      <template #header>
        <div class="card-header">
          <el-icon><List /></el-icon>
          <span>批量合成</span>
        </div>
      </template>

      <el-form :model="batchForm" inline>
        <el-form-item label="批量文本">
          <el-input
            v-model="batchForm.texts"
            type="textarea"
            :rows="4"
            placeholder="每行一个文本，将批量合成"
            style="width: 300px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="batchGenerate" :loading="batchLoading">
            <el-icon><Tools /></el-icon>
            批量合成
          </el-button>
        </el-form-item>
      </el-form>

      <div v-if="batchResults.length > 0" class="batch-results">
        <h4>合成结果</h4>
        <el-table :data="batchResults" stripe>
          <el-table-column prop="index" label="序号" width="80" />
          <el-table-column prop="text" label="文本" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
                {{ row.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" @click="downloadBatchAudio(row)" v-if="row.status === 'success'">
                下载
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Microphone, Tools, Download, Delete, Clock, VideoPlay, VideoPause, Connection, List } from '@element-plus/icons-vue'
import axios from 'axios'

const loading = ref(false)
const result = ref(null)
const isPlaying = ref(false)
const audioPlayer = ref(null)
const waveformData = ref([])
const audioHistory = ref([])
const batchLoading = ref(false)
const batchResults = ref([])

const form = reactive({
  provider: 'azure_tts',
  text: '',
  voice: 'zh-CN-XiaoxiaoNeural',
  speed: 1.0
})

const batchForm = reactive({
  texts: ''
})

const voiceOptions = [
  { label: '晓晓（女声）', value: 'zh-CN-XiaoxiaoNeural' },
  { label: '云希（男声）', value: 'zh-CN-YunxiNeural' },
  { label: '云阳（男声）', value: 'zh-CN-YunyangNeural' },
  { label: '云健（男声）', value: 'zh-CN-YunjianNeural' },
  { label: '小美（女声）', value: 'zh-CN-XiaomeiNeural' },
  { label: '小云（女声）', value: 'zh-CN-XiaoyunNeural' }
]

const generateAudio = async () => {
  if (!form.text.trim()) {
    ElMessage.warning('请输入需要合成的文本')
    return
  }

  loading.value = true
  try {
    const response = await axios.post('http://localhost:9001/api/v1/tts/synthesize', {
      provider: form.provider,
      text: form.text,
      voice: form.voice,
      speed: form.speed
    })

    result.value = response.data
    audioHistory.value.unshift({
      ...response.data,
      text: form.text,
      provider: form.provider,
      created_at: new Date().toLocaleString()
    })

    // 生成模拟波形数据
    generateWaveform()

    ElMessage.success('语音合成完成')
  } catch (error) {
    console.error('合成失败:', error)
    ElMessage.error('合成失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const generateWaveform = () => {
  // 生成模拟波形数据
  const bars = 50
  const waveform = []
  for (let i = 0; i < bars; i++) {
    waveform.push(Math.random() * 80 + 20)
  }
  waveformData.value = waveform
}

const playPause = () => {
  if (!audioPlayer.value) return

  if (isPlaying.value) {
    audioPlayer.value.pause()
  } else {
    audioPlayer.value.play()
  }
}

const onTimeUpdate = () => {
  if (audioPlayer.value) {
    isPlaying.value = !audioPlayer.value.paused
  }
}

const onPlayEnd = () => {
  isPlaying.value = false
}

const downloadAudio = () => {
  if (result.value?.audio_path) {
    const a = document.createElement('a')
    a.href = result.value.audio_path
    a.download = `ai_audio_${Date.now()}.mp3`
    a.click()
    ElMessage.success('音频下载已开始')
  }
}

const clearResult = () => {
  result.value = null
  waveformData.value = []
  if (audioPlayer.value) {
    audioPlayer.value.pause()
    audioPlayer.value.currentTime = 0
  }
}

const useAudioForVideo = () => {
  if (result.value) {
    // 可以将音频用于视频配音
    ElMessage.info('正在准备用于视频配音...')
    // 这里可以实现与视频生成模块的集成
  }
}

const playAudio = (audio) => {
  result.value = audio
  // 等待DOM更新后播放
  setTimeout(() => {
    if (audioPlayer.value) {
      audioPlayer.value.play()
    }
  }, 100)
}

const batchGenerate = async () => {
  if (!batchForm.texts.trim()) {
    ElMessage.warning('请输入批量文本')
    return
  }

  const texts = batchForm.texts.trim().split('\n').filter(text => text.trim())
  if (texts.length === 0) {
    ElMessage.warning('请输入有效的文本内容')
    return
  }

  batchLoading.value = true
  batchResults.value = []

  for (let i = 0; i < texts.length; i++) {
    const text = texts[i].trim()
    try {
      const response = await axios.post('http://localhost:9001/api/v1/tts/synthesize', {
        provider: form.provider,
        text: text,
        voice: form.voice,
        speed: form.speed
      })

      batchResults.value.push({
        index: i + 1,
        text: text,
        status: 'success',
        data: response.data
      })
    } catch (error) {
      batchResults.value.push({
        index: i + 1,
        text: text,
        status: 'error',
        error: error.message
      })
    }
  }

  batchLoading.value = false
  ElMessage.success(`批量合成完成，成功 ${batchResults.value.filter(r => r.status === 'success').length} 个`)
}

const downloadBatchAudio = (row) => {
  if (row.data?.audio_path) {
    const a = document.createElement('a')
    a.href = row.data.audio_path
    a.download = `batch_audio_${row.index}.mp3`
    a.click()
    ElMessage.success('音频下载已开始')
  }
}

const formatDuration = (seconds) => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatFileSize = (bytes) => {
  if (!bytes) return '未知'
  const sizes = ['Bytes', 'KB', 'MB']
  if (bytes === 0) return '0 Bytes'
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

onMounted(() => {
  // 加载历史记录
  const savedHistory = localStorage.getItem('audio-generate-history')
  if (savedHistory) {
    audioHistory.value = JSON.parse(savedHistory)
  }
})

// 保存历史记录
const saveHistory = () => {
  localStorage.setItem('audio-generate-history', JSON.stringify(audioHistory.value.slice(0, 20)))
}

import { watch } from 'vue'
watch(audioHistory, saveHistory, { deep: true })
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.audio-generate {
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

    .input-card, .player-card, .history-card {
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
        text-align: center;

        .loading-text {
          margin-top: 1rem;
          color: #666;
        }
      }

      .player-container {
        .audio-player {
          margin-bottom: 1rem;
        }

        .waveform {
          margin-bottom: 1rem;

          .waveform-container {
            display: flex;
            align-items: center;
            height: 60px;
            gap: 2px;
            background: #f5f5f5;
            padding: 10px;
            border-radius: 4px;

            .waveform-bar {
              flex: 1;
              background: #409eff;
              border-radius: 2px;
              min-height: 4px;
            }
          }
        }

        .action-buttons {
          display: flex;
          gap: 0.5rem;
          margin-top: 1rem;
        }
      }
    }
  }

  .batch-card {
    .card-header {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-weight: bold;
    }

    .batch-results {
      margin-top: 1rem;
    }
  }
}
</style>