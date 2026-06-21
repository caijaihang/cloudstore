<template>
  <div id="app">
    <el-container>
      <el-header style="display: flex; align-items: center; gap: 20px; background: #f5f7fa;">
        <h2 style="margin: 0;">云文件存储</h2>
        <el-menu mode="horizontal" :router="true" style="flex: 1;">
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/upload">上传</el-menu-item>
          <el-menu-item index="/manage">管理</el-menu-item>
          <el-menu-item index="/help">帮助</el-menu-item>
        </el-menu>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
</script>

<style>
body { margin: 0; font-family: Arial, sans-serif; }
.el-header { padding: 0 20px; }
</style>
