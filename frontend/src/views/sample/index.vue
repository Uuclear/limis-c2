<template>
  <div class="sample-page">
    <div class="page-header">
      <h2>样品管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>登记样品
      </el-button>
    </div>

    <el-card class="filter-card">
      <el-form inline>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="样品编号/名称" clearable @clear="loadList" @keyup.enter="loadList" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable @change="loadList">
            <el-option label="待接收" value="pending" />
            <el-option label="已接收" value="received" />
            <el-option label="检测中" value="testing" />
            <el-option label="已检测" value="tested" />
            <el-option label="留样中" value="retained" />
            <el-option label="已处置" value="disposed" />
          </el-select>
        </el-form-item>
        <el-form-item label="材料类型">
          <el-input v-model="filters.material_type" placeholder="如：混凝土" clearable @clear="loadList" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadList">搜索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="sample_no" label="样品编号" width="160" />
        <el-table-column prop="name" label="样品名称" min-width="160" />
        <el-table-column prop="material_type" label="材料类型" width="100" />
        <el-table-column prop="specification" label="规格型号" width="120" show-overflow-tooltip />
        <el-table-column prop="quantity" label="数量" width="80" align="center">
          <template #default="{ row }">{{ row.quantity }} {{ row.quantity_unit }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="登记时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="goToDetail(row.id)">查看</el-button>
            <el-button v-if="row.status === 'pending'" size="small" type="success" @click="handleReceive(row)">接收</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          :page-sizes="[10, 20, 50]"
          @size-change="loadList"
          @current-change="loadList"
        />
      </div>
    </el-card>

    <!-- Create dialog -->
    <el-dialog v-model="showCreateDialog" title="登记样品" width="600px" @close="resetForm">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="委托单" prop="commission_id">
          <el-select v-model="form.commission_id" placeholder="选择已审核委托单" filterable>
            <el-option v-for="c in approvedCommissions" :key="c.id" :label="`${c.commission_no} - ${c.client_name}`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="样品名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="材料类型">
          <el-input v-model="form.material_type" placeholder="如：混凝土、钢筋" />
        </el-form-item>
        <el-form-item label="规格型号">
          <el-input v-model="form.specification" />
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="form.quantity" :min="1" />
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="form.quantity_unit" style="width:120px" />
        </el-form-item>
        <el-form-item label="取样日期">
          <el-date-picker v-model="form.sampling_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="取样部位">
          <el-input v-model="form.sampling_location" />
        </el-form-item>
        <el-form-item label="取样人">
          <el-input v-model="form.sampler" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCreate">登记</el-button>
      </template>
    </el-dialog>

    <!-- Receive dialog -->
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
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { listSamples, createSample, receiveSample } from '@/api/sample'
import { listCommissions } from '@/api/commission'

const route = useRoute()
const router = useRouter()

const list = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showReceiveDialog = ref(false)
const submitting = ref(false)
const formRef = ref(null)
const approvedCommissions = ref([])
const receiveLocation = ref('')
const receiveSampleId = ref(null)

const filters = reactive({ keyword: '', status: '', material_type: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const form = reactive({
  commission_id: null,
  name: '',
  material_type: '',
  specification: '',
  quantity: 1,
  quantity_unit: '组',
  sampling_date: null,
  sampling_location: '',
  sampler: '',
  notes: '',
})

const formRules = {
  commission_id: [{ required: true, message: '请选择委托单', trigger: 'change' }],
  name: [{ required: true, message: '请输入样品名称', trigger: 'blur' }],
}

const statusType = (s) => ({ pending: 'info', received: '', testing: 'warning', tested: 'success', retained: '', disposed: 'info' })[s] || ''
const statusLabel = (s) => ({ pending: '待接收', received: '已接收', testing: '检测中', tested: '已检测', retained: '留样中', disposed: '已处置' })[s] || s

function formatDate(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleString('zh-CN')
}

async function loadList() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword,
      status: filters.status,
      material_type: filters.material_type,
    }
    // Support commission_id from query params (linked from commission detail)
    if (route.query.commission_id) {
      params.commission_id = route.query.commission_id
    }
    list.value = await listSamples(params)
  } finally {
    loading.value = false
  }
}

async function loadApprovedCommissions() {
  approvedCommissions.value = await listCommissions({ status: 'approved', page_size: 100 })
}

function goToDetail(id) {
  router.push(`/samples/${id}`)
}

async function handleCreate() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    await createSample(form)
    ElMessage.success('样品登记成功')
    showCreateDialog.value = false
    loadList()
  } finally {
    submitting.value = false
  }
}

function handleReceive(row) {
  receiveSampleId.value = row.id
  receiveLocation.value = ''
  showReceiveDialog.value = true
}

async function confirmReceive() {
  if (!receiveLocation.value) { ElMessage.warning('请输入存放位置'); return }
  await receiveSample(receiveSampleId.value, { storage_location: receiveLocation.value })
  ElMessage.success('样品已接收')
  showReceiveDialog.value = false
  loadList()
}

function resetForm() {
  Object.assign(form, {
    commission_id: null, name: '', material_type: '', specification: '',
    quantity: 1, quantity_unit: '组', sampling_date: null,
    sampling_location: '', sampler: '', notes: '',
  })
}

onMounted(() => { loadList(); loadApprovedCommissions() })
</script>

<style scoped>
.sample-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 18px; }
.filter-card { margin-bottom: 16px; }
.pagination-wrapper { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
