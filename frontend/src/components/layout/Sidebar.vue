<template>
  <el-aside :width="appStore.sidebarCollapsed ? '64px' : '200px'" class="sidebar">
    <div class="sidebar-logo">
      <span v-if="!appStore.sidebarCollapsed" class="logo-text">LIMIS</span>
      <span v-else class="logo-text-mini">L</span>
    </div>
    <el-menu
      :default-active="route.path"
      :collapse="appStore.sidebarCollapsed"
      background-color="#263238"
      text-color="#b0bec5"
      active-text-color="#409eff"
      router
    >
      <el-menu-item index="/dashboard">
        <el-icon><Odometer /></el-icon>
        <template #title>工作台</template>
      </el-menu-item>

      <el-menu-item index="/projects">
        <el-icon><OfficeBuilding /></el-icon>
        <template #title>项目管理</template>
      </el-menu-item>

      <el-menu-item index="/commissions">
        <el-icon><Document /></el-icon>
        <template #title>委托管理</template>
      </el-menu-item>

      <el-menu-item index="/samples">
        <el-icon><Box /></el-icon>
        <template #title>样品管理</template>
      </el-menu-item>

      <el-sub-menu index="test">
        <template #title>
          <el-icon><DataAnalysis /></el-icon>
          <span>检测管理</span>
        </template>
        <el-menu-item index="/test/tasks">任务分配</el-menu-item>
        <el-menu-item index="/test/records">原始记录</el-menu-item>
        <el-menu-item index="/test/results">结果判定</el-menu-item>
      </el-sub-menu>

      <el-menu-item index="/reports">
        <el-icon><Printer /></el-icon>
        <template #title>报告管理</template>
      </el-menu-item>

      <el-menu-item index="/equipment">
        <el-icon><SetUp /></el-icon>
        <template #title>设备管理</template>
      </el-menu-item>

      <el-menu-item index="/quality">
        <el-icon><Medal /></el-icon>
        <template #title>质量管理</template>
      </el-menu-item>

      <el-sub-menu index="system">
        <template #title>
          <el-icon><Setting /></el-icon>
          <span>系统管理</span>
        </template>
        <el-menu-item index="/system/users">用户管理</el-menu-item>
        <el-menu-item index="/system/roles">角色权限</el-menu-item>
        <el-menu-item index="/system/standards">标准库</el-menu-item>
        <el-menu-item index="/system/dict">数据字典</el-menu-item>
        <el-menu-item index="/system/logs">操作日志</el-menu-item>
      </el-sub-menu>
    </el-menu>
  </el-aside>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/app'
import {
  Odometer,
  OfficeBuilding,
  Document,
  Box,
  DataAnalysis,
  Printer,
  SetUp,
  Medal,
  Setting,
} from '@element-plus/icons-vue'

const route = useRoute()
const appStore = useAppStore()
</script>

<style scoped>
.sidebar {
  background: #263238;
  transition: width 0.3s;
  overflow: hidden;
}

.sidebar-logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #1a2226;
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
}

.logo-text-mini {
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
}

.el-menu {
  border-right: none;
}
</style>
