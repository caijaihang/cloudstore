<template>
  <div class="home" style="max-width: 800px; margin: 0 auto; padding: 20px;">
    <el-card style="margin-bottom: 20px;">
      <template #header><h3>上传文件</h3></template>
      <p>支持任意格式文件，分块上传，可断点续传。</p>
      <el-button type="primary" size="large" @click="$router.push('/upload')">
        前往上传
      </el-button>
    </el-card>

    <el-card style="margin-bottom: 20px;">
      <template #header><h3>文件管理</h3></template>
      <p>查看已上传的文件，复制下载链接或删除文件。</p>
      <el-button size="large" @click="$router.push('/manage')">
        查看已上传文件
      </el-button>
    </el-card>

    <el-card>
      <template #header><h3>使用说明</h3></template>
      <ul>
        <li>支持任意格式文件上传</li>
        <li>支持超大文件（自动分块）</li>
        <li>支持断点续传（localStorage 保存上传进度）</li>
        <li>下载无速度限制</li>
      </ul>
    </el-card>
  </div>
</template>

<script setup>
</script>
