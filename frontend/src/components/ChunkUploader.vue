<template>
  <div class="chunk-uploader">
    <el-card>
      <template #header>
        <h2>上传文件</h2>
      </template>

      <!-- Resume dialog -->
      <el-dialog
        v-model="resumeDialogVisible"
        title="发现未完成的上传"
        width="500px"
      >
        <p>检测到有未完成的上传任务：</p>
        <ul>
          <li v-for="session in storedSessions" :key="session.upload_id">
            <strong>{{ session.filename }}</strong> (已上传 {{ session.uploaded_chunks ? session.uploaded_chunks.length : 0 }} / {{ session.total_chunks }} 块)
          </li>
        </ul>
        <p>是否继续上传？</p>
        <template #footer>
          <el-button @click="cancelResume">重新开始</el-button>
          <el-button type="primary" @click="confirmResume">继续上传</el-button>
        </template>
      </el-dialog>

      <!-- File selection area -->
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :show-file-list="false"
        :on-change="handleFileChange"
        drag
      >
        <el-icon style="font-size: 48px; color: #409eff;"><upload-filled /></el-icon>
        <div style="margin-top: 10px;">
          将文件拖拽到此处，或<em style="color: #409eff;">点击选择</em>
        </div>
      </el-upload>

      <!-- File info -->
      <div v-if="file && !uploading && !completed" style="margin: 20px 0; padding: 15px; background: #f5f7fa; border-radius: 4px;">
        <p><strong>文件名:</strong> {{ file.name }}</p>
        <p><strong>大小:</strong> {{ formatSize(file.size) }}</p>
        <p><strong>分块大小:</strong> {{ formatSize(chunkSize) }}</p>
        <p><strong>总块数:</strong> {{ totalChunks }}</p>
        <el-button type="primary" size="large" @click="startUpload" style="margin-top: 10px;">
          开始上传
        </el-button>
      </div>

      <!-- Upload progress -->
      <div v-if="uploading" style="margin: 20px 0;">
        <h3>{{ file ? file.name : '' }}</h3>
        <el-progress :percentage="progressPercent" :status="uploadError ? 'exception' : null" />
        <p style="margin: 10px 0;">
          已上传: {{ uploadedChunks.length }} / {{ totalChunks }} 块
          | 速度: {{ formatSize(speed) }}/s
          | 剩余时间: {{ remainingTimeText }}
        </p>
        <el-button-group>
          <el-button @click="togglePause">{{ paused ? '继续' : '暂停' }}</el-button>
          <el-button type="danger" @click="cancelUpload">取消上传</el-button>
        </el-button-group>
      </div>

      <!-- Completed state -->
      <div v-if="completed" style="margin: 20px 0; text-align: center;">
        <el-result icon="success" title="上传完成" :sub-title="'文件ID: ' + fileId">
          <template #extra>
            <el-button type="primary" @click="copyDownloadLink">复制下载链接</el-button>
            <el-button @click="resetAll">上传新文件</el-button>
          </template>
        </el-result>
      </div>

      <!-- Error state -->
      <el-alert
        v-if="uploadError"
        :title="uploadError"
        type="error"
        :closable="false"
        style="margin-top: 15px;"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { initUpload, uploadChunk, completeUpload, getUploadStatus, getDownloadUrl } from '../api/files'

const STORAGE_KEY = 'upload_sessions'
const CHUNK_CONCURRENCY = 3

// File state
const file = ref(null)
const chunkSize = ref(0)
const totalChunks = ref(0)
const uploadId = ref(null)
const uploadedChunks = ref([])
const uploading = ref(false)
const paused = ref(false)
const completed = ref(false)
const fileId = ref(null)
const uploadError = ref(null)

// Resume state
const resumeDialogVisible = ref(false)
const storedSessions = ref([])
const pendingResume = ref(null)

// Speed tracking
const speed = ref(0)
let startTime = null
let speedTimer = null

// Active upload workers
let activeUploads = 0
let shouldStop = false

function formatSize (bytes) {
  if (!bytes || bytes <= 0) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(2) + ' MB'
  return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB'
}

function calculateChunkSize (fileSize) {
  if (fileSize < 100 * 1024 * 1024) return 5 * 1024 * 1024
  if (fileSize < 1024 * 1024 * 1024) return 10 * 1024 * 1024
  return 20 * 1024 * 1024
}

function getStoredSessions () {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch (e) {
    return []
  }
}

function saveToStorage () {
  const sessions = getStoredSessions()
  const idx = sessions.findIndex(s => s.upload_id === uploadId.value)
  const session = {
    upload_id: uploadId.value,
    filename: file.value ? file.value.name : sessions[idx]?.filename,
    chunk_size: chunkSize.value,
    total_chunks: totalChunks.value,
    uploaded_chunks: [...uploadedChunks.value],
    file_size: file.value ? file.value.size : sessions[idx]?.file_size,
  }
  if (idx >= 0) {
    sessions[idx] = session
  } else {
    sessions.push(session)
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions))
}

function removeFromStorage (targetUploadId) {
  const sessions = getStoredSessions().filter(s => s.upload_id !== targetUploadId)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions))
}

function handleFileChange (uploadFile) {
  if (uploading.value) {
    ElMessage.warning('当前正在上传，请先取消当前上传')
    return
  }

  file.value = uploadFile.raw
  completed.value = false
  uploadError.value = null

  // Check if a resume is pending - if the file size matches, start from resume
  if (pendingResume.value) {
    if (file.value.size !== pendingResume.value.file_size) {
      ElMessage.warning('文件大小与上次不一致，作为新上传处理')
      pendingResume.value = null
      initNewUpload()
      return
    }
    startFromResume()
    return
  }

  initNewUpload()
}

function initNewUpload () {
  chunkSize.value = calculateChunkSize(file.value.size)
  totalChunks.value = Math.ceil(file.value.size / chunkSize.value)
  uploadedChunks.value = []
  uploadId.value = null
}

async function startUpload () {
  if (!file.value) return

  uploadError.value = null

  try {
    const res = await initUpload({
      filename: file.value.name,
      total_chunks: totalChunks.value,
      file_size: file.value.size,
      content_type: file.value.type || 'application/octet-stream',
    })

    uploadId.value = res.data.upload_id
    chunkSize.value = res.data.chunk_size
    totalChunks.value = Math.ceil(file.value.size / chunkSize.value)

    uploading.value = true
    paused.value = false
    shouldStop = false

    startSpeedTimer()
    runUploadLoop()
  } catch (e) {
    uploadError.value = e?.response?.data?.error || e?.message || '初始化上传失败'
    ElMessage.error(uploadError.value)
  }
}

function startFromResume () {
  const pending = pendingResume.value
  if (!pending) return

  uploadId.value = pending.upload_id
  chunkSize.value = pending.chunk_size
  totalChunks.value = pending.total_chunks
  uploadedChunks.value = [...pending.uploaded_chunks]

  pendingResume.value = null

  uploading.value = true
  paused.value = false
  shouldStop = false

  ElMessage.success(`从断点继续上传，已有 ${uploadedChunks.value.length} / ${totalChunks.value} 块`)

  startSpeedTimer()
  runUploadLoop()
}

function togglePause () {
  paused.value = !paused.value
  if (!paused.value) {
    runUploadLoop()
  }
}

function cancelUpload () {
  shouldStop = true
  uploading.value = false
  paused.value = false
  ElMessage.info('上传已取消，进度已保存，可稍后继续')
  if (uploadId.value) {
    saveToStorage()
  }
  stopSpeedTimer()
}

function runUploadLoop () {
  if (shouldStop || paused.value) return

  for (let i = 0; i < totalChunks.value; i++) {
    if (activeUploads >= CHUNK_CONCURRENCY) break
    if (uploadedChunks.value.includes(i)) continue
    if (paused.value || shouldStop) break

    uploadOneChunk(i)
  }

  if (uploadedChunks.value.length >= totalChunks.value && activeUploads === 0 && !shouldStop) {
    finishUpload()
  } else if (activeUploads < CHUNK_CONCURRENCY && uploadedChunks.value.length < totalChunks.value && !paused.value && !shouldStop) {
    setTimeout(runUploadLoop, 100)
  }
}

function uploadOneChunk (chunkIndex) {
  activeUploads++

  const start = chunkIndex * chunkSize.value
  const end = Math.min(start + chunkSize.value, file.value.size)
  const chunk = file.value.slice(start, end)

  uploadChunk(uploadId.value, chunkIndex, chunk)
    .then(() => {
      if (!uploadedChunks.value.includes(chunkIndex)) {
        uploadedChunks.value.push(chunkIndex)
        saveToStorage()
      }
    })
    .catch((e) => {
      ElMessage.error(`分块 ${chunkIndex} 上传失败，将重试`)
      uploadError.value = e?.response?.data?.error || e?.message || '分块上传失败'
    })
    .finally(() => {
      activeUploads--
      if (!paused.value && !shouldStop) {
        runUploadLoop()
      }
    })
}

async function finishUpload () {
  try {
    const res = await completeUpload(uploadId.value)
    fileId.value = res.data.file_id
    completed.value = true
    uploading.value = false

    removeFromStorage(uploadId.value)

    ElMessage.success('上传完成')
  } catch (e) {
    uploadError.value = e?.response?.data?.error || e?.message || '合并失败'
    uploading.value = false
    ElMessage.error(uploadError.value)
  } finally {
    stopSpeedTimer()
  }
}

function copyDownloadLink () {
  const url = window.location.origin + getDownloadUrl(fileId.value)
  navigator.clipboard.writeText(url).then(() => {
    ElMessage.success('链接已复制：' + url)
  }).catch(() => {
    ElMessage.error('复制失败，请手动复制：' + url)
  })
}

function resetAll () {
  file.value = null
  chunkSize.value = 0
  totalChunks.value = 0
  uploadId.value = null
  uploadedChunks.value = []
  uploading.value = false
  paused.value = false
  completed.value = false
  fileId.value = null
  uploadError.value = null
  shouldStop = false
  activeUploads = 0
}

function startSpeedTimer () {
  startTime = Date.now()
  speedTimer = setInterval(() => {
    const elapsed = (Date.now() - startTime) / 1000
    const bytesUploaded = uploadedChunks.value.length * chunkSize.value
    speed.value = bytesUploaded / elapsed
  }, 1000)
}

function stopSpeedTimer () {
  if (speedTimer) {
    clearInterval(speedTimer)
    speedTimer = null
  }
}

const progressPercent = computed(() => {
  if (totalChunks.value === 0) return 0
  return Math.round((uploadedChunks.value.length / totalChunks.value) * 100)
})

const remainingTimeText = computed(() => {
  if (!speed.value || speed.value <= 0) return '计算中...'
  const remainingBytes = (totalChunks.value - uploadedChunks.value.length) * chunkSize.value
  const seconds = Math.round(remainingBytes / speed.value)
  if (seconds < 60) return seconds + '秒'
  if (seconds < 3600) return Math.round(seconds / 60) + '分钟'
  return Math.round(seconds / 3600) + '小时'
})

// ======== BREAKPOINT RESUME LOGIC ========
function checkAndResumeOnMount () {
  const sessions = getStoredSessions()
  if (sessions.length === 0) return

  storedSessions.value = sessions
  resumeDialogVisible.value = true
}

async function confirmResume () {
  resumeDialogVisible.value = false

  const session = storedSessions.value[0]
  if (!session) return

  try {
    const res = await getUploadStatus(session.upload_id)
    const data = res.data

    if (data.completed) {
      ElMessage.info('该文件已完成上传，正在获取下载信息...')
      try {
        const completeRes = await completeUpload(session.upload_id)
        fileId.value = completeRes.data.file_id
        completed.value = true
        removeFromStorage(session.upload_id)
      } catch (e) {
        uploadError.value = '完成上传失败'
      }
      return
    }

    if (data.expired) {
      ElMessage.warning('上传已过期，请重新开始上传')
      removeFromStorage(session.upload_id)
      return
    }

    const serverChunks = data.uploaded_chunks || []
    const serverChunkSize = data.chunk_size || session.chunk_size

    pendingResume.value = {
      upload_id: session.upload_id,
      file_size: session.file_size,
      uploaded_chunks: serverChunks,
      chunk_size: serverChunkSize,
      total_chunks: session.total_chunks,
      filename: session.filename,
    }

    try {
      await ElMessageBox.alert(
        '请选择与未完成上传相同的文件，系统会从断点处继续上传。\n\n请在下一次文件选择对话框中选择同一个文件。',
        '断点续传',
        { confirmButtonText: '我知道了' }
      )
    } catch (e) {}

    ElMessage.info('现在请选择同一个文件继续上传')
  } catch (e) {
    ElMessage.warning('无法从服务器获取上传状态，请重新开始上传')
    removeFromStorage(session.upload_id)
  }
}

function cancelResume () {
  resumeDialogVisible.value = false
  localStorage.removeItem(STORAGE_KEY)
}

onMounted(() => {
  checkAndResumeOnMount()
})

onBeforeUnmount(() => {
  stopSpeedTimer()
  shouldStop = true
})
</script>

<style scoped>
.chunk-uploader {
  max-width: 700px;
  margin: 0 auto;
}
</style>
