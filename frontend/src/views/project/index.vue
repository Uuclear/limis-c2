<template>
  <div class="project-page">
    <div class="page-header">
      <h2>项目管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>新建工程
      </el-button>
    </div>

    <!-- Search bar -->
    <el-card class="filter-card">
      <el-form inline>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="工程名称/编号" clearable @clear="loadProjects" @keyup.enter="loadProjects" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable @change="loadProjects">
            <el-option label="进行中" value="active" />
            <el-option label="已完成" value="completed" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadProjects">搜索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Project list table -->
    <el-card>
      <el-table :data="projects" v-loading="loading" stripe>
        <el-table-column prop="code" label="工程编号" width="150" />
        <el-table-column prop="name" label="工程名称" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" @click="goToDetail(row.id)">{{ row.name }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="client_name" label="委托单位" width="150" />
        <el-table-column prop="location" label="工程地点" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="switchProject(row)">切换</el-button>
            <el-button size="small" type="primary" @click="goToDetail(row.id)">管理</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
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
          @size-change="loadProjects"
          @current-change="loadProjects"
        />
      </div>
    </el-card>

    <!-- Create project dialog -->
    <el-dialog v-model="showCreateDialog" title="新建工程" width="600px" @close="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="工程名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入工程名称" />
        </el-form-item>
        <el-form-item label="工程编号" prop="code">
          <el-input v-model="form.code" placeholder="请输入唯一编号" />
        </el-form-item>
        <el-form-item label="委托单位" prop="client_name">
          <el-input v-model="form.client_name" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact_person" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.contact_phone" />
        </el-form-item>
        <el-form-item label="工程地点">
          <el-input v-model="form.location" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
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
import { useAppStore } from '@/stores/app'
import { listProjects, createProject, deleteProject } from '@/api/project'

const router = useRouter()
const appStore = useAppStore()

const projects = ref([])
const loading = ref(false)
const showCreateDialog = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const filters = reactive({ keyword: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

const form = reactive({
  name: '', code: '', description: '', location: '',
  client_name: '', contact_person: '', contact_phone: '',
})

const rules = {
  name: [{ required: true, message: '请输入工程名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入工程编号', trigger: 'blur' }],
}

const statusType = (s) => ({ active: '', completed: 'success', archived: 'info' })[s] || ''
const statusLabel = (s) => ({ active: '进行中', completed: '已完成', archived: '已归档' })[s] || s

function formatDate(dt) {
  if (!dt) return ''
  return new Date(dt).toLocaleString('zh-CN')
}

async function loadProjects() {
  loading.value = true
  try {
    const data = await listProjects({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword,
      status: filters.status,
    })
    projects.value = data
  } finally {
    loading.value = false
  }
}

function goToDetail(id) {
  router.push(`/projects/${id}`)
}

function switchProject(row) {
  appStore.setCurrentProject(row.id, row.name)
  ElMessage.success(`已切换到: ${row.name}`)
}

async function handleCreate() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    await createProject(form)
    ElMessage.success('工程创建成功')
    showCreateDialog.value = false
    loadProjects()
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除工程「${row.name}」？此操作不可恢复。`, '确认删除', { type: 'warning' })
  await deleteProject(row.id)
  ElMessage.success('删除成功')
  loadProjects()
}

function resetForm() {
  Object.assign(form, { name: '', code: '', description: '', location: '', client_name: '', contact_person: '', contact_phone: '' })
}

onMounted(loadProjects)
</script>

<style scoped>
.project-page { padding: 0; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-header h2 { margin: 0; font-size: 18px; }
.filter-card { margin-bottom: 16px; }
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
