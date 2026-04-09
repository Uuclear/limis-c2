<template>
  <div class="sample-detail" v-loading="loading">
    <div class="page-header">
      <h2>样品详情</h2>
      <el-button @click="$router.back()">返回</el-button>
    </div>

    <el-card class="info-card">
      <template #header><span>样品信息</span></template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="样品编号">{{ sample.sample_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(sample.status)">{{ statusLabel(sample.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="样品名称">{{ sample.name }}</el-descriptions-item>
        <el-descriptions-item label="材料类型">{{ sample.material_type }}</el-descriptions-item>
        <el-descriptions-item label="规格型号">{{ sample.specification }}</el-descriptions-item>
        <el-descriptions-item label="数量">{{ sample.quantity }} {{ sample.quantity_unit }}</el-descriptions-item>
        <el-descriptions-item label="取样日期">{{ sample.sampling_date }}</el-descriptions-item>
        <el-descriptions-item label="取样部位">{{ sample.sampling_location }}</el-descriptions-item>
        <el-descriptions-item label="取样人">{{ sample.sampler }}</el-descriptions-item>
        <el-descriptions-item label="存放位置">{{ sample.storage_location || '-' }}</el-descriptions-item>
        <el-descriptions-item label="接收时间">{{ formatDate(sample.received_at) }}</el-descriptions-item>
        <el-descriptions-item label="留样到期">{{ sample.retention_deadline || '-' }}</el-descriptions-item>
        <el-descriptions-item label="处置时间">{{ formatDate(sample.disposed_at) }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ sample.notes || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Status flow timeline -->
    <el-card class="flow-card">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>状态流转</span>
          <el-button v-if="nextStatus" type="primary" size="small" @click="handleNextStatus">
            {{ nextStatusAction }}
          </el-button>
        </div>
      </template>
      <el-steps :active="statusIndex" finish-status="success" align-center>
        <el-step v-for="s in allStatuses" :key="s.value" :title="s.label" />
      </el-steps>
    </el-card>

    <!-- Receive dialog (for pending status) -->
    <el-dialog v-model="showReceiveDialog" title="接收样品" width="400px">
      <el-form label-width="80px">
        <el-form-item label="存放位置">
          <el-input v-model="receiveLocation" placeholder="如：A区-3号架" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReceiveDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmReceive">确认接收</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSample, receiveSample, updateSampleStatus } from '@/api/sample'

const route = useRoute()

const loading = ref(false)
const sample = ref({})
const showReceiveDialog = ref(false)
const receiveLocation = ref('')

const allStatuses = [
  { value: 'pending', label: '待接收' },
  { value: 'received', label: '已接收' },
  { value: 'testing', label: '检测中' },
  { value: 'tested', label: '已检测' },
  { value: 'retained', label: '留样中' },
  { value: 'disposed', label: '已处置' },
]

const statusIndex = computed(() => {
  const idx = allStatuses.findIndex(s => s.value === sample.value.status)
  return idx >= 0 ? idx : 0
})

const nextStatus = computed(() => {
  const idx = statusIndex.value
  if (idx < allStatuses.length - 1) return allStatuses[idx + 1]
  return null
})

const nextStatusAction = computed(() => {
  if (!nextStatus.value) return ''
  if (nextStatus.value.value === 'received') return '接收样品'
  return `流转至: ${nextStatus.value.label}`
})

const statusType = (s) => ({ pending: 'info', received: '', testing: 'warning', tested: 'success', retained: '', disposed: 'info' })[s] || ''
const statusLabel = (s) => allStatuses.find(x => x.value === s)?.label || s

function formatDate(dt) {
  if (!dt) return '-'
  return new Date(dt).toLocaleString('zh-CN')
}

async function loadData() {
  loading.value = true
  try {
    sample.value = await getSample(route.params.id)
  } finally {
    loading.value = false
  }
}

async function handleNextStatus() {
  if (!nextStatus.value) return
  if (nextStatus.value.value === 'received') {
    receiveLocation.value = ''
    showReceiveDialog.value = true
    return
  }
  await ElMessageBox.confirm(`确定将样品状态流转至「${nextStatus.value.label}」？`, '状态变更')
  await updateSampleStatus(sample.value.id, { status: nextStatus.value.value })
  ElMessage.success('状态已更新')
  loadData()
}

async function confirmReceive() {
  if (!receiveLocation.value) { ElMessage.warning('请输入存放位置'); return }
  await receiveSample(sample.value.id, { storage_location: receiveLocation.value })
  ElMessage.success('样品已接收')
  showReceiveDialog.value = false
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.sample-detail { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 18px; }
.info-card { margin-bottom: 16px; }
.flow-card { margin-bottom: 16px; }
</style>
