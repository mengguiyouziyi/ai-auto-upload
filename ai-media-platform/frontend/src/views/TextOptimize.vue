<template>
  <div class="text-optimize">
    <el-card class="page-header">
      <template #header>
        <div class="card-header">
          <el-icon><EditPen /></el-icon>
          <span>AI文本优化</span>
        </div>
      </template>
      <p>使用大语言模型优化文案，使其更适合视频创作</p>
    </el-card>

    <el-row :gutter="20" class="main-content">
      <el-col :span="12">
        <el-card class="input-card">
          <template #header>
            <div class="card-header">
              <span>原始文案</span>
              <el-button type="primary" size="small" @click="optimizeText" :loading="loading">
                <el-icon><Tools /></el-icon>
                AI优化
              </el-button>
            </div>
          </template>

          <el-form :model="form" label-width="100px">
            <el-form-item label="LLM提供商">
              <el-select v-model="form.provider" placeholder="选择AI提供商">
                <el-option label="GLM-4.6 (推荐)" value="glm" />
                <el-option label="Kimi" value="kimi" />
                <el-option label="豆包" value="doubao" />
                <el-option label="百度文心" value="wenxin" />
                <el-option label="OpenAI" value="openai" />
                <el-option label="阿里通义千问" value="qwen" />
              </el-select>
            </el-form-item>

            <el-form-item label="快速导入">
              <el-button type="info" size="small" @click="importSpiderContent" :disabled="!hasSpiderContent">
                <el-icon><Download /></el-icon>
                导入爬虫内容
              </el-button>
              <span v-if="hasSpiderContent" class="spider-content-hint">
                发现来自爬虫的内容
              </span>
            </el-form-item>

            <el-form-item label="原始文本">
              <el-input
                v-model="form.text"
                type="textarea"
                :rows="8"
                placeholder="请输入需要优化的文本内容..."
                maxlength="2000"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="AI优化提示词">
              <div class="prompt-editor">
                <div class="prompt-header">
                  <span class="prompt-label">自定义GLM模型优化提示词（可修改默认提示词）</span>
                  <div class="prompt-actions">
                    <el-button size="small" @click="showPromptTemplates = !showPromptTemplates">
                      <el-icon><Collection /></el-icon>
                      {{ showPromptTemplates ? '隐藏' : '显示' }}模板
                    </el-button>
                    <el-button size="small" @click="resetPrompt" v-if="aiOptimizePrompt">
                      <el-icon><RefreshRight /></el-icon>
                      重置
                    </el-button>
                    <el-button size="small" @click="clearPrompt" v-if="aiOptimizePrompt">
                      <el-icon><Delete /></el-icon>
                      清空
                    </el-button>
                  </div>
                </div>

                <el-input
                  v-model="aiOptimizePrompt"
                  type="textarea"
                  :rows="8"
                  placeholder="请输入用于指导GLM模型优化文本的提示词..."
                  maxlength="2000"
                  show-word-limit
                  class="prompt-textarea"
                />

                <!-- Prompt模板选择 -->
                <div v-if="showPromptTemplates" class="prompt-templates">
                  <div class="templates-header">
                    <span>快速选择提示词模板：</span>
                  </div>
                  <div class="templates-grid">
                    <el-button
                      v-for="template in aiPromptTemplates"
                      :key="template.name"
                      size="small"
                      type="info"
                      plain
                      @click="applyAiTemplate(template)"
                      class="template-btn"
                    >
                      {{ template.name }}
                    </el-button>
                  </div>
                </div>
              </div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="output-card">
          <template #header>
            <div class="card-header">
              <span>优化结果</span>
              <div class="header-actions">
                <el-button size="small" @click="copyResult" v-if="result">
                  <el-icon><CopyDocument /></el-icon>
                  复制
                </el-button>
                <el-button size="small" @click="clearResult" v-if="result">
                  <el-icon><Delete /></el-icon>
                  清空
                </el-button>
                <el-button type="primary" size="small" @click="useForVideo" v-if="result">
                  <el-icon><VideoPlay /></el-icon>
                  生成视频
                </el-button>
              </div>
            </div>
          </template>

          <div v-if="loading" class="loading-container">
            <el-skeleton :rows="6" animated />
            <p class="loading-text">AI正在优化中...</p>
          </div>

          <div v-else-if="result" class="result-container">
            <div class="result-text">{{ result.optimized_text }}</div>
            <div class="result-meta">
              <el-tag size="small">{{ result.provider }}</el-tag>
              <span class="response-time">响应时间: {{ result.response_time }}s</span>
            </div>
          </div>

          <el-empty v-else description="点击AI优化按钮开始生成" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 历史记录 -->
    <el-card class="history-card">
      <template #header>
        <div class="card-header">
          <el-icon><Clock /></el-icon>
          <span>优化历史</span>
        </div>
      </template>

      <el-table :data="history" stripe>
        <el-table-column prop="original_text" label="原始文本" show-overflow-tooltip />
        <el-table-column prop="optimized_text" label="优化结果" show-overflow-tooltip />
        <el-table-column prop="provider" label="提供商" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.provider }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="180" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" @click="useHistory(row)">使用</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { EditPen, Tools, CopyDocument, Delete, Clock, Download, VideoPlay, Collection, RefreshRight } from '@element-plus/icons-vue'
import { http } from '@/utils/request'

const router = useRouter()
const loading = ref(false)
const result = ref(null)
const history = ref([])
const videoPrompt = ref('')
const aiOptimizePrompt = ref('')
const showPromptTemplates = ref(false)

const form = reactive({
  provider: 'glm',
  text: ''
})

// AI优化提示词模板
const aiPromptTemplates = ref([
  {
    name: '通用文案优化',
    prompt: '你是一个专业的文案优化师。请将以下原始文案进行优化，使其更加生动、吸引人且适合视频创作。要求：\n1. 保持原意不变\n2. 增强表现力和感染力\n3. 适合口头表达和视频展示\n4. 控制在合适的长度\n\n原始文案：{original_text}\n\n请提供优化后的文案：'
  },
  {
    name: '短视频优化',
    prompt: '你是一个专业的短视频内容创作者。请将以下文案优化为适合短视频平台的版本：\n1. 开头要有吸引力\n2. 语言简洁有力\n3. 容易理解和记忆\n4. 具有一定的传播性\n\n原始文案：{original_text}\n\n请提供短视频优化版本：'
  },
  {
    name: '故事化表达',
    prompt: '你是一个擅长故事化表达的文案专家。请将以下内容转化为生动的故事形式：\n1. 增加故事性和画面感\n2. 用具体的场景和细节\n3. 创造情感共鸣\n4. 使内容更具感染力\n\n原始内容：{original_text}\n\n请提供故事化版本：'
  },
  {
    name: '营销文案',
    prompt: '你是一个营销文案专家。请将以下内容优化为具有营销吸引力的文案：\n1. 突出核心卖点\n2. 增加紧迫感和吸引力\n3. 使用有说服力的语言\n4. 引导用户行动\n\n原始内容：{original_text}\n\n请提供营销文案版本：'
  },
  {
    name: '知识分享',
    prompt: '你是一个知识分享领域的文案专家。请将以下内容优化为易于理解和传播的知识分享文案：\n1. 简化复杂概念\n2. 增加实用性\n3. 结构清晰\n4. 便于记忆和分享\n\n原始内容：{original_text}\n\n请提供知识分享版本：'
  }
])

// Prompt模板（视频生成用）
const promptTemplates = ref([
  {
    name: '科技开场',
    prompt: '【场景1：科技感视频开场】屏幕上出现动态的代码行，背景是抽象的数字网格，代码行随着节奏逐渐构建出炫酷的界面，最后形成完整的科技logo，电影级视觉效果'
  },
  {
    name: '自然风光',
    prompt: '【场景1：自然风光展示】山水相连，云雾缭绕过渡，阳光穿透云层洒在山间，湖水波光粼粼，唯美意境，4K超高清画质'
  },
  {
    name: '城市夜景',
    prompt: '【场景1：城市夜景展示】建筑群相连，灯光渐变展示，车流如织形成光带，霓虹灯光变化，现代都市繁华景象，高清画质'
  },
  {
    name: '动物世界',
    prompt: '【场景1：动物世界展示】雄鹰翱翔雪山之巅，镜头跟随飞行轨迹，展现壮美自然，动物动作流畅，场景自然过渡'
  },
  {
    name: '抽象艺术',
    prompt: '【场景1：抽象艺术展示】色彩斑斓几何图形舞动，形状变化融合，色彩过渡自然，视觉冲击力强，动态流畅'
  }
])

// 检查是否有爬虫内容
const hasSpiderContent = computed(() => {
  return localStorage.getItem('spider-content-for-ai') !== null
})

// 导入爬虫内容
const importSpiderContent = () => {
  const spiderContent = localStorage.getItem('spider-content-for-ai')
  if (spiderContent) {
    try {
      const content = JSON.parse(spiderContent)
      form.text = content.content
      ElMessage.success(`已导入内容: ${content.title}`)
    } catch (error) {
      ElMessage.error('导入内容失败')
    }
  } else {
    ElMessage.warning('没有找到爬虫内容')
  }
}

const optimizeText = async () => {
  if (!form.text.trim()) {
    ElMessage.warning('请输入需要优化的文本')
    return
  }

  loading.value = true
  try {
    const requestData = {
      text: form.text,
      provider: form.provider
    }

    // 如果有自定义提示词，添加到请求中
    if (aiOptimizePrompt.value.trim()) {
      requestData.custom_prompt = aiOptimizePrompt.value
    }

    const response = await http.post('/api/v1/llm/optimize-text', requestData)

    result.value = response.data || response
    history.value.unshift({
      ...(response.data || response),
      original_text: form.text,
      created_at: new Date().toLocaleString()
    })

    // 自动填充到视频Prompt编辑框
    videoPrompt.value = (response.data || response).optimized_text

    ElMessage.success('文本优化完成，已填充到视频Prompt编辑框')
  } catch (error) {
    console.error('优化失败:', error)
    ElMessage.error('优化失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// 应用AI优化提示词模板
const applyAiTemplate = (template) => {
  aiOptimizePrompt.value = template.prompt
  ElMessage.success(`已应用模板: ${template.name}`)
}

// 应用视频Prompt模板
const applyTemplate = (template) => {
  videoPrompt.value = template.prompt
  ElMessage.success(`已应用模板: ${template.name}`)
}

// 重置AI优化提示词
const resetPrompt = () => {
  aiOptimizePrompt.value = getDefaultAiPrompt()
  ElMessage.success('已重置为默认提示词')
}

// 清空Prompt
const clearPrompt = () => {
  aiOptimizePrompt.value = ''
  ElMessage.success('已清空AI优化提示词')
}

// 获取默认AI优化提示词
const getDefaultAiPrompt = () => {
  return '你是一个专业的文案优化师。请将以下原始文案进行优化，使其更加生动、吸引人且适合视频创作。\n\n要求：\n1. 保持原意不变\n2. 增强表现力和感染力\n3. 使语言更加流畅自然\n4. 适合口头表达和视频展示\n5. 控制在合适的长度\n\n原始文案：{original_text}\n\n请提供优化后的文案：'
}

const copyResult = () => {
  if (result.value) {
    navigator.clipboard.writeText(result.value.optimized_text || result.value)
    ElMessage.success('已复制到剪贴板')
  }
}

const clearResult = () => {
  result.value = null
}

const useForVideo = () => {
  const promptToUse = videoPrompt.value || result.value?.optimized_text || result.value

  if (promptToUse) {
    // 将视频Prompt存储到localStorage，供视频生成使用
    localStorage.setItem('optimized-text-for-video', JSON.stringify({
      text: promptToUse,
      provider: result.value?.provider || form.provider,
      original_text: form.text,
      timestamp: new Date().toISOString()
    }))

    ElMessage.success('视频Prompt已准备用于视频生成')

    // 跳转到视频生成页面
    setTimeout(() => {
      router.push('/video-generate')
    }, 1000)
  } else {
    ElMessage.warning('请先进行文本优化或编辑视频Prompt')
  }
}

const useHistory = (item) => {
  // 确保所有字段都有值
  form.text = item.original_text || item.text || ''
  form.provider = item.provider || 'doubao'

  if (item.optimized_text) {
    result.value = {
      optimized_text: item.optimized_text,
      provider: item.provider || form.provider,
      response_time: item.response_time || 0
    }
    ElMessage.success('已加载历史优化结果')
  } else {
    ElMessage.warning('该历史记录缺少优化结果')
  }
}

onMounted(() => {
  // 可以从localStorage加载历史记录
  const savedHistory = localStorage.getItem('text-optimize-history')
  if (savedHistory) {
    history.value = JSON.parse(savedHistory)
  }

  // 初始化默认AI优化提示词
  if (!aiOptimizePrompt.value) {
    aiOptimizePrompt.value = getDefaultAiPrompt()
  }
})

// 保存历史记录到localStorage
const saveHistory = () => {
  localStorage.setItem('text-optimize-history', JSON.stringify(history.value.slice(0, 20))) // 只保存最近20条
}

// 监听历史变化
import { watch } from 'vue'
watch(history, saveHistory, { deep: true })
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.text-optimize {
  .page-header {
    margin-bottom: 20px;

    .card-header {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-weight: bold;
    }
  }

  .spider-content-hint {
    margin-left: 0.5rem;
    font-size: 0.9rem;
    color: #67c23a;
  }

  .prompt-editor {
    border: 1px solid #e4e7ed;
    border-radius: 6px;
    padding: 1rem;
    background: #fafafa;

    .prompt-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.5rem;

      .prompt-label {
        font-weight: 500;
        color: #303133;
      }

      .prompt-actions {
        display: flex;
        gap: 0.5rem;
      }
    }

    .prompt-textarea {
      margin-bottom: 1rem;
    }

    .prompt-templates {
      border-top: 1px solid #e4e7ed;
      padding-top: 1rem;
      margin-top: 1rem;

      .templates-header {
        font-size: 0.9rem;
        color: #606266;
        margin-bottom: 0.5rem;
      }

      .templates-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;

        .template-btn {
          margin: 0;
        }
      }
    }
  }

  .main-content {
    margin-bottom: 20px;

    .input-card, .output-card {
      min-height: 400px;

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .header-actions {
          display: flex;
          gap: 0.5rem;
        }
      }

      .loading-container {
        text-align: center;

        .loading-text {
          margin-top: 1rem;
          color: #666;
        }
      }

      .result-container {
        .result-text {
          background: #f8f9fa;
          padding: 1rem;
          border-radius: 6px;
          line-height: 1.6;
          margin-bottom: 1rem;
          min-height: 150px;
        }

        .result-meta {
          display: flex;
          justify-content: space-between;
          align-items: center;
          color: #666;
          font-size: 0.9rem;
        }
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
  }
}
</style>