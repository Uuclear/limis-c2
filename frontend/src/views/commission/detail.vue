<template>
  <div class="commission-detail" v-loading="loading">
    <div class="page-header">
      <h2>委托单详情</h2>
      <div>
        <el-button @click="$router.back()">返回</el-button>
        <el-button v-if="commission.status === 'draft'" type="primary" @click="handleSubmit">提交审核</el-button>
        <el-button v-if="commission.status === 'draft' || commission.status === 'rejected'" @click="showEditDialog = true">编辑</el-button>
      </div>
    </div>

    <el-card class="info-card">
      <template #header><span>委托信息</span></template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="委托编号">{{ commission.commission_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(commission.status)">{{ statusLabel(commission.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="委托方">{{ commission.client_name }}</el-descriptions-item>
        <el-descriptions-item label="联系人">{{ commission.client_contact }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ commission.client_phone }}</el-descriptions-item>
        <el-descriptions-item label="预计样品数">{{ commission.sample_count }}</el-descriptions-item>
        <el-descriptions-item label="委托内容" :span="2">{{ commission.description }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(commission.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="审核时间">{{ formatDate(commission.reviewed_at) }}</el-descriptions-item>
        <el-descriptions-item v-if="commission.review_comment" label="审核意见" :span="2">{{ commission.review_comment }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Review section -->
    <el-card v-if="commission.status === 'submitted'" class="review-card">
      <template #header><span>审核操作</span></template>
      <el-form label-width="80px">
        <el-form-item label="审核意见">
          <el-input v-model="reviewComment" type="textarea" :rows="3" placeholder="请输入审核意见" />
        </el-form-item>
        <el-form-item>
          <el-button type="success" @click="handleReview(true)">审核通过</el-button>
          <el-button type="danger" @click="handleReview(false)">退回修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Associated samples -->
    <el-card class="samples-card">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>关联样品</span>
          <el-button v-if="commission.status === 'approved'" size="small" type="primary" @click="$router.push(`/samples?commission_id=${commission.id}`)">
            登记样品
          </el-button>
        </div>
      </template>
      <el-table :data="samples" stripe>
        <el-table-column prop="sample_no" label="样品编号" width="160" />
        <el-table-column prop="name" label="样品名称" min-width="150" />
        <el-table-column prop="material_type" label="材料类型" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="sampleStatusType(row.status)" size="small">{{ sampleStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" @click="$router.push(`/samples/${row.id}`)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Edit dialog -->
    <el-dialog v-model="showEditDialog" title="编辑委托单" width="600px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
        <el-form-item label="委托方" prop="client_name">
          <el-input v-model="editForm.client_name" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="editForm.client_contact" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="editForm.client_phone" />
        </el-form-item>
        <el-form-item label="检测内容">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="预计样品数">
          <el-input-number v-model="editForm.sample_count" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCommission, updateCommission, submitCommission, reviewCommission } from '@/api/commission'
import { listSamples } from '@/api/sample'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const commission = ref({})
const samples = ref([])
const reviewComment = ref('')
const showEditDialog = ref(false)
const editFormRef = ref(null)

const editForm = reactive({
  client_name: '', client_contact: '', client_phone: '', description: '', sample_count: 0,
})
const editRules = { client_name: [{ required: true, message: '请输入委托方', trigger: 'blur' }] }

const statusType = (s) => ({ draft: 'info', submitted: 'warning', approved: 'success', rejected: 'danger' })[s] || ''
const statusLabel = (s) => ({ draft: '草稿', submitted: '待审核', approved: '已审核', rejected: '已退回' })[s] || s
const sampleStatusType = (s) => ({ pending: 'info', received: '', testing: 'warning', tested: 'success', retained: '', disposed: 'info' })[s] || ''
const sampleStatusLabel = (s) => ({ pending: '待接收', received: '已接收', testing: '检测中', tested: '已检测', retained: '留样中', disposed: '已处置' })[s] || s

function formatDate(dt) {
  if (!dt) return '-'
  return new Date(dt).toLocaleString('zh-CN')
}

async function loadData() {
  loading.value = true
  try {
    const id = route.params.id
    commission.value = await getCommission(id)
    Object.assign(editForm, {
      client_name: commission.value.client_name,
      client_contact: commission.value.client_contact,
      client_phone: commission.value.client_phone,
      description: commission.value.description,
      sample_count: commission.value.sample_count,
    })
    samples.value = await listSamples({ commission_id: id, page_size: 100 })
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  await ElMessageBox.confirm('确定提交此委托单进行审核？', '提交确认')
  await submitCommission(commission.value.id)
  ElMessage.success('已提交审核')
  loadData()
}

async function handleReview(approved) {
  const action = approved ? '通过' : '退回'
  await ElMessageBox.confirm(`确定${action}此委托单？`, '审核确认')
  await reviewCommission(commission.value.id, { approved, comment: reviewComment.value })
  ElMessage.success(`已${action}`)
  reviewComment.value = ''
  loadData()
}

async function handleEdit() {
  const valid = await editFormRef.value.validate().catch(() => false)
  if (!valid) return
  await updateCommission(commission.value.id, editForm)
  ElMessage.success('更新成功')
  showEditDialog.value = false
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.commission-detail { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 18px; }
.info-card { margin-bottom: 16px; }
.review-card { margin-bottom: 16px; }
.samples-card { margin-bottom: 16px; }
</style>
