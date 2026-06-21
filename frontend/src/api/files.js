import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000, // 5 minutes
})

// Upload init
export function initUpload (data) {
  return api.post('/upload/init/', data)
}

// Upload a single chunk
export function uploadChunk (uploadId, chunkIndex, chunk) {
  const formData = new FormData()
  formData.append('upload_id', uploadId)
  formData.append('chunk_index', chunkIndex)
  formData.append('chunk', chunk)
  return api.post('/upload/chunk/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000 // 10 minutes for large chunks
  })
}

// Complete upload (merge chunks)
export function completeUpload (uploadId) {
  return api.post('/upload/complete/', { upload_id: uploadId })
}

// Get upload status (for resume)
export function getUploadStatus (uploadId) {
  return api.get(`/upload/status/${uploadId}/`)
}

// Get file list
export function getFileList (page = 1, pageSize = 20) {
  return api.get('/files/', {
    params: { page, page_size: pageSize }
  })
}

// Get file detail
export function getFileDetail (fileId) {
  return api.get(`/files/${fileId}/`)
}

// Delete file
export function deleteFile (fileId) {
  return api.delete(`/files/${fileId}/`)
}

// Get download URL (relative, used by browser)
export function getDownloadUrl (fileId) {
  return `/api/download/${fileId}/`
}

export default api
