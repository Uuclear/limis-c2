<template>
  <el-container class="app-layout">
    <Sidebar />
    <el-container direction="vertical">
      <Header />
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
}

.app-main {
  background: #f0f2f5;
  padding: 16px;
}
</style>
