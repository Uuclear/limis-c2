<template>
  <div class="commission-page">
    <div class="page-header">
      <h2>委托管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>新建委托单
      </el-button>
    </div>

    <el-card class="filter-card">
      <el-form inline>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="委托编号/委托方/内容" clearable @clear="loadList" @keyup.enter="loadList" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable @change="loadList">
            <el-option label="草稿" value="draft" />
            <el-option label="已提交" value="submitted" />
            <el-option label="已审核" value="approved" />
            <el-option label="已退回" value="rejected" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadList">搜索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="commission_no" label="委托编号" width="160" />
        <el-table-column prop="description" label="委托内容" min-width="200" show-overflow-tooltip />
        <el-table-column prop="client_name" label="委托方" width="160" />
        <el-table-column prop="sample_count" label="样品数" width="80" align="center" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="goToDetail(row.id)">查看</el-button>
            <el-button v-if="row.status === 'draft'" size="small" @click="handleSubmit(row)">提交</el-button>
            <el-button v-if="row.status === 'draft'" size="small" type="danger" @click="handleDelete(row)">删除</el-button>
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
    <el-dialog v-model="showCreateDialog" title="新建委托单" width="650px" @close="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="关联工程" prop="project_id">
          <el-select v-model="form.project_id" placeholder="选择���程" filterable @change="onProjectChange">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="分项工程" prop="sub_item_id">
          <el-cascader
            v-model="subItemPath"
            :options="hierarchyOptions"
            :props="{ value: 'id', label: 'name', children: 'children' }"
            placeholder="选择分项工程"
            @change="onSubItemChange"
          />
        </el-form-item>
        <el-form-item label="委托方" prop="client_name">
          <el-input v-model="form.client_name" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.client_contact" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.client_phone" />
        </el-form-item>
        <el-form-item label="检测内容">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="预计样品数">
          <el-input-number v-model="form.sample_count" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { listCommissions, createCommission, submitCommission, deleteCommission } from '@/api/commission'
import { listProjects, getProject } from '@/api/project'

const router = useRouter()

const list = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const submitting = ref(false)
const formRef = ref(null)
const projects = ref([])
const hierarchyOptions = ref([])
const subItemPath = ref([])

const filters = reactive({ keyword: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const form = reactive({
  project_id: null,
  sub_item_id: null,
  client_name: '',
  client_contact: '',
  client_phone: '',
  description: '',
  sample_count: 0,
})

const rules = {
  project_id: [{ required: true, message: '请选择工程', trigger: 'change' }],
  sub_item_id: [{ required: true, message: '请选择分项工程', trigger: 'change' }],
  client_name: [{ required: true, message: '请输入委托方', trigger: 'blur' }],
}

const statusType = (s) => ({ draft: 'info', submitted: 'warning', approved: 'success', rejected: 'danger' })[s] || ''
const statusLabel = (s) => ({ draft: '草稿', submitted: '已提交', approved: '已审核', rejected: '已退回' })[s] || s

function formatDate(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleString('zh-CN')
}

async function loadList() {
  loading.value = true
  try {
    const data = await listCommissions({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword,
      status: filters.status,
    })
    list.value = data
  } finally {
    loading.value = false
  }
}

async function loadProjects() {
  projects.value = await listProjects({ page_size: 100 })
}

async function onProjectChange(projectId) {
  if (!projectId) { hierarchyOptions.value = []; return }
  const detail = await getProject(projectId)
  hierarchyOptions.value = (detail.unit_projects || []).map(u => ({
    id: u.id, name: u.name,
    children: (u.divisions || []).map(d => ({
      id: d.id, name: d.name,
      children: (d.sub_items || []).map(s => ({ id: s.id, name: s.name })),
    })),
  }))
}

function onSubItemChange(val) {
  form.sub_item_id = val ? val[val.length - 1] : null
}

function goToDetail(id) {
  router.push(`/commissions/${id}`)
}

async function handleCreate() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    await createCommission(form)
    ElMessage.success('委托单创建成功')
    showCreateDialog.value = false
    loadList()
  } finally {
    submitting.value = false
  }
}

async function handleSubmit(row) {
  await ElMessageBox.confirm('确定提交此委托单进行审核？', '提交确认')
  await submitCommission(row.id)
  ElMessage.success('已提交审核')
  loadList()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除委托单「${row.commission_no}」？`, '确认删除', { type: 'warning' })
  await deleteCommission(row.id)
  ElMessage.success('删除成功')
  loadList()
}

function resetForm() {
  Object.assign(form, { project_id: null, sub_item_id: null, client_name: '', client_contact: '', client_phone: '', description: '', sample_count: 0 })
  subItemPath.value = []
}

onMounted(() => { loadList(); loadProjects() })
</script>

<style scoped>
.commission-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 18px; }
.filter-card { margin-bottom: 16px; }
.pagination-wrapper { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
