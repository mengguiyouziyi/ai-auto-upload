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

    <div class="main-content">
      <!-- 上排：生成设置 + 生成进度 -->
      <div class="main-row">
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
              <el-input
                v-model="form.prompt"
                type="textarea"
                :rows="6"
                placeholder="请详细描述您想要生成的视频内容，例如：\n\n• 场景：在海边日落的沙滩上\n• 人物：一个穿着白色连衣裙的女孩\n• 动作：正在散步，海风吹过头发\n• 风格：温暖、治愈系、电影感\n• 其他细节：海鸥飞过，波浪轻拍海岸"
                show-word-limit
                maxlength="2000"
              />
            </el-form-item>

            <el-form-item label="视频时长">
              <el-slider
                v-model="form.duration"
                :min="2"
                :max="currentProvider?.max_duration || 10"
                :step="1"
                show-stops
                show-input
                :format-tooltip="val => `${val}秒`"
              />
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

            <div class="video-info" v-if="result">
              <el-descriptions :column="2" size="small" border>
                <el-descriptions-item label="提供商">
                  <el-tag size="small">{{ result.provider }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="质量">
                  <el-tag size="small" :type="getQualityTagType(result.quality)">{{ result.quality }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="分辨率" span="2">
                  {{ result.width || 0 }} × {{ result.height || 0 }}
                </el-descriptions-item>
                <el-descriptions-item label="文件大小" span="2">
                  {{ formatFileSize(result.file_size) }}
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <div class="action-buttons">
              <el-button type="primary" @click="useVideoForSocial">
                <el-icon><Share /></el-icon>
                发布到社交平台
              </el-button>
              <el-button @click="useVideoForSocial">
                <el-icon><Share /></el-icon>
                发布到社交平台
              </el-button>
            </div>
          </div>

          <el-empty v-else description="设置参数并点击生成视频开始创作" />
        </el-card>
      </div>

      <!-- 下排：生成历史 -->
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
          style="width: 100%"
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
          <el-table-column prop="duration" label="时长" width="80">
            <template #default="{ row }">
              {{ row.duration || 0 }}s
            </template>
          </el-table-column>
          <el-table-column prop="quality" label="质量" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="getQualityTagType(row.quality)">{{ row.quality }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="width" label="分辨率" width="100">
            <template #default="{ row }">
              {{ row.width || 0 }}×{{ row.height || 0 }}
            </template>
          </el-table-column>
          <el-table-column prop="file_size" label="大小" width="80">
            <template #default="{ row }">
              {{ formatFileSize(row.file_size, true) }}
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
    </div>
  </div>
</template>