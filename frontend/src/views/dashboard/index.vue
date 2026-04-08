<template>
  <div class="dashboard">
    <el-row :gutter="16">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">待检测任务</div>
          <div class="stat-value" style="color: #409eff">0</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">待审核报告</div>
          <div class="stat-value" style="color: #e6a23c">0</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">本月已签发</div>
          <div class="stat-value" style="color: #67c23a">0</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-label">设备到期提醒</div>
          <div class="stat-value" style="color: #f56c6c">0</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="todo-card" shadow="hover">
      <template #header>
        <span style="font-weight: bold">我的待办</span>
      </template>
      <el-empty description="暂无待办事项" />
    </el-card>
  </div>
</template>

<script setup>
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
}

.stat-card {
  text-align: center;
}

.stat-label {
  font-size: 13px;
  color: #909399;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  margin-top: 8px;
}

.todo-card {
  margin-top: 16px;
}
</style>
