<template>
  <div class="help" style="max-width: 800px; margin: 0 auto; padding: 20px;">
    <el-card style="margin-bottom: 20px;">
      <template #header><h3>功能特点</h3></template>
      <ul>
        <li><strong>大文件支持</strong>：采用分块上传技术，支持超过100GB的超大文件</li>
        <li><strong>断点续传</strong>：上传中断后可从断点继续，无需重新开始</li>
        <li><strong>永久存储</strong>：文件永久保存，下载无限制</li>
        <li><strong>全格式支持</strong>：支持任意文件格式上传</li>
      </ul>
    </el-card>

    <el-card style="margin-bottom: 20px;">
      <template #header><h3>断点续传说明</h3></template>
      <p>如果上传过程中网络中断或浏览器关闭，系统会自动检测未完成的上传任务。</p>
      <p>下次进入上传页面时，会提示是否继续未完成的上传。</p>
      <el-alert type="warning" :closable="false" style="margin-top: 10px;">
        请勿清除浏览器缓存，否则将丢失未完成上传的记录
      </el-alert>
    </el-card>

    <el-card>
      <template #header><h3>常见问题</h3></template>
      <p><strong>Q: 支持多大的文件？</strong></p>
      <p>A: 单个文件最大支持 100GB，系统自动分块上传。</p>
      <p><strong>Q: 文件保存多久？</strong></p>
      <p>A: 文件永久保存。</p>
      <p><strong>Q: 下载速度有限制吗？</strong></p>
      <p>A: 完全无限制。</p>
    </el-card>
  </div>
</template>

<script setup>
</script>
