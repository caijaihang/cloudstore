<template>
  <div class="download" style="max-width: 600px; margin: 0 auto; padding: 20px;">
    <el-loading v-if="loading" text="正在加载..."/>

    <el-card v-else-if="file" style="text-align: center;">
      <h2>{{ file.filename }}</h2>
      <p>大小: {{ formatSize(file.file_size) }}</p>
      <p>下载次数: {{ file.download_count }}</p>
      <p>文件 ID: {{ file.file_id }}</p>
      <el-button type="primary" size="large" @click="downloadFile">
        下载文件
      </el-button>
      <el-button size="large" @click="copyLink">复制下载链接</el-button>
    </el-card>

    <el-card v-else style="text-align: center;">
      <el-empty description="文件不存在或已被删除" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getFileDetail, getDownloadUrl } from '../api/files'

const route = useRoute()
const file = ref(null)
const loading = ref(true)

async function loadFile () {
  try {
    const res = await getFileDetail(route.params.fileId)
    file.value = res.data
  } catch (e) {
    ElMessage.error('文件不存在或已被删除')
    file.value = null
  } finally {
    loading.value = false
  }
}

function downloadFile () {
  window.location.href = getDownloadUrl(route.params.fileId)
}

function copyLink () {
  const url = window.location.origin + getDownloadUrl(route.params.fileId)
  navigator.clipboard.writeText(url).then(() => {
    ElMessage.success('链接已复制')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

function formatSize (bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(2) + ' MB'
  return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB'
}

onMounted(loadFile)
</script>
