<template>
  <div class="manage" style="max-width: 1000px; margin: 0 auto; padding: 20px;">
    <h2>文件管理</h2>

    <div v-if="loading" style="text-align: center; padding: 40px;">
      <el-icon :size="48"><loading /></el-icon>
    </div>

    <el-empty v-else-if="!files.length" description="暂无文件，请先上传" />

    <div v-else>
      <el-table :data="files" style="width: 100%;">
        <el-table-column prop="filename" label="文件名" min-width="200" />
        <el-table-column label="大小" width="120">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column label="上传时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="download_count" label="下载次数" width="100" />
        <el-table-column label="操作" width="240">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="copyLink(row.file_id)">复制链接</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row.file_id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > pageSize"
        style="margin-top: 20px; justify-content: center;"
        layout="prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { getFileList, deleteFile, getDownloadUrl } from '../api/files'

const files = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = 20

async function loadFiles () {
  loading.value = true
  try {
    const res = await getFileList(page.value, pageSize)
    files.value = res.data.files
    total.value = res.data.total
  } catch (e) {
    ElMessage.error('加载文件列表失败')
  } finally {
    loading.value = false
  }
}

function formatSize (bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(2) + ' MB'
  return (bytes / 1024 / 1024 / 1024).toFixed(2) + ' GB'
}

function copyLink (fileId) {
  const url = window.location.origin + getDownloadUrl(fileId)
  navigator.clipboard.writeText(url).then(() => {
    ElMessage.success('链接已复制')
  }).catch(() => {
    ElMessage.error('复制失败，请手动复制：' + url)
  })
}

async function handleDelete (fileId) {
  try {
    await deleteFile(fileId)
    ElMessage.success('删除成功')
    loadFiles()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

function handlePageChange (newPage) {
  page.value = newPage
  loadFiles()
}

onMounted(loadFiles)
</script>
