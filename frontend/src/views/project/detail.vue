<template>
  <div class="project-detail" v-loading="loading">
    <!-- Project info header -->
    <el-card class="info-card">
      <template #header>
        <div class="card-header">
          <span>{{ project.name || '工程详情' }}</span>
          <div>
            <el-button size="small" @click="showEditDialog = true">编辑信息</el-button>
            <el-button size="small" @click="$router.push('/projects')">返回列表</el-button>
          </div>
        </div>
      </template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="工程编号">{{ project.code }}</el-descriptions-item>
        <el-descriptions-item label="委托单位">{{ project.client_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(project.status)">{{ statusLabel(project.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="工程地点">{{ project.location || '-' }}</el-descriptions-item>
        <el-descriptions-item label="联系人">{{ project.contact_person || '-' }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ project.contact_phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="3">{{ project.description || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Hierarchy tree -->
    <el-card class="tree-card">
      <template #header>
        <div class="card-header">
          <span>工程层级结构</span>
          <el-button size="small" type="primary" @click="openNodeDialog('unit', null)">
            <el-icon><Plus /></el-icon>添加单位工程
          </el-button>
        </div>
      </template>

      <el-tree
        :data="treeData"
        :props="{ label: 'label', children: 'children' }"
        node-key="key"
        default-expand-all
        :expand-on-click-node="false"
      >
        <template #default="{ node, data }">
          <div class="tree-node">
            <span class="node-label">
              <el-tag size="small" :type="levelTagType(data.level)" class="level-tag">{{ data.levelName }}</el-tag>
              {{ data.label }}
              <span class="node-code">（{{ data.code }}）</span>
            </span>
            <span class="node-actions">
              <el-button v-if="data.level < 4" size="small" link type="primary" @click.stop="openNodeDialog(nextLevel(data.level), data)">
                添加{{ nextLevelName(data.level) }}
              </el-button>
              <el-button size="small" link type="primary" @click.stop="openEditNodeDialog(data)">编辑</el-button>
              <el-button size="small" link type="danger" @click.stop="handleDeleteNode(data)">删除</el-button>
            </span>
          </div>
        </template>
      </el-tree>

      <el-empty v-if="treeData.length === 0" description="暂无层级数据，请添加单位工程" />
    </el-card>

    <!-- Add/Edit node dialog -->
    <el-dialog v-model="showNodeDialog" :title="nodeDialogTitle" width="500px" @close="resetNodeForm">
      <el-form ref="nodeFormRef" :model="nodeForm" :rules="nodeRules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="nodeForm.name" />
        </el-form-item>
        <el-form-item label="编号" prop="code">
          <el-input v-model="nodeForm.code" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="nodeForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showNodeDialog = false">取消</el-button>
        <el-button type="primary" :loading="nodeSubmitting" @click="handleNodeSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- Edit project dialog -->
    <el-dialog v-model="showEditDialog" title="编辑工程信息" width="600px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
        <el-form-item label="工程名称" prop="name">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="工程编号" prop="code">
          <el-input v-model="editForm.code" />
        </el-form-item>
        <el-form-item label="委托单位"><el-input v-model="editForm.client_name" /></el-form-item>
        <el-form-item label="联系人"><el-input v-model="editForm.contact_person" /></el-form-item>
        <el-form-item label="联系电话"><el-input v-model="editForm.contact_phone" /></el-form-item>
        <el-form-item label="工程地点"><el-input v-model="editForm.location" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status">
            <el-option label="进行中" value="active" />
            <el-option label="已完成" value="completed" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="editForm.description" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="editSubmitting" @click="handleEditProject">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getProject, updateProject,
  createUnitProject, updateUnitProject, deleteUnitProject,
  createDivision, updateDivision, deleteDivision,
  createSubItem, updateSubItem, deleteSubItem,
} from '@/api/project'

const route = useRoute()
const projectId = Number(route.params.id)

const project = ref({})
const loading = ref(false)

// --- Project info edit ---
const showEditDialog = ref(false)
const editSubmitting = ref(false)
const editFormRef = ref(null)
const editForm = reactive({ name: '', code: '', description: '', location: '', client_name: '', contact_person: '', contact_phone: '', status: 'active' })
const editRules = {
  name: [{ required: true, message: '请输入工程名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入工程编号', trigger: 'blur' }],
}

const statusType = (s) => ({ active: '', completed: 'success', archived: 'info' })[s] || ''
const statusLabel = (s) => ({ active: '进行中', completed: '已完成', archived: '已归档' })[s] || s

// --- Tree data ---
const treeData = computed(() => {
  if (!project.value.unit_projects) return []
  return project.value.unit_projects.map(unit => ({
    key: `unit-${unit.id}`,
    label: unit.name,
    code: unit.code,
    level: 2,
    levelName: '单位工程',
    id: unit.id,
    type: 'unit',
    raw: unit,
    children: (unit.divisions || []).map(div => ({
      key: `div-${div.id}`,
      label: div.name,
      code: div.code,
      level: 3,
      levelName: '分部工程',
      id: div.id,
      type: 'division',
      parentId: unit.id,
      raw: div,
      children: (div.sub_items || []).map(sub => ({
        key: `sub-${sub.id}`,
        label: sub.name,
        code: sub.code,
        level: 4,
        levelName: '分项工程',
        id: sub.id,
        type: 'sub_item',
        parentId: div.id,
        raw: sub,
        children: [],
      })),
    })),
  }))
})

const levelTagType = (l) => ({ 2: '', 3: 'success', 4: 'warning' })[l] || 'info'
const nextLevel = (l) => ({ 2: 'division', 3: 'sub_item' })[l]
const nextLevelName = (l) => ({ 2: '分部工程', 3: '分项工程' })[l]

// --- Node add/edit dialog ---
const showNodeDialog = ref(false)
const nodeSubmitting = ref(false)
const nodeFormRef = ref(null)
const nodeForm = reactive({ name: '', code: '', description: '' })
const nodeRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入编号', trigger: 'blur' }],
}
const nodeDialogMode = ref('create')
const nodeDialogType = ref('')
const nodeDialogParent = ref(null)
const nodeDialogEditData = ref(null)

const nodeDialogTitle = computed(() => {
  const names = { unit: '单位工程', division: '分部工程', sub_item: '分项工程' }
  const action = nodeDialogMode.value === 'create' ? '添加' : '编辑'
  return `${action}${names[nodeDialogType.value] || ''}`
})

function openNodeDialog(type, parentData) {
  nodeDialogMode.value = 'create'
  nodeDialogType.value = type
  nodeDialogParent.value = parentData
  showNodeDialog.value = true
}

function openEditNodeDialog(data) {
  nodeDialogMode.value = 'edit'
  nodeDialogType.value = data.type
  nodeDialogEditData.value = data
  Object.assign(nodeForm, { name: data.raw.name, code: data.raw.code, description: data.raw.description || '' })
  showNodeDialog.value = true
}

function resetNodeForm() {
  Object.assign(nodeForm, { name: '', code: '', description: '' })
  nodeDialogEditData.value = null
}

async function handleNodeSubmit() {
  const valid = await nodeFormRef.value.validate().catch(() => false)
  if (!valid) return
  nodeSubmitting.value = true
  try {
    if (nodeDialogMode.value === 'edit') {
      const d = nodeDialogEditData.value
      const fns = { unit: updateUnitProject, division: updateDivision, sub_item: updateSubItem }
      await fns[d.type](d.id, nodeForm)
    } else {
      const type = nodeDialogType.value
      if (type === 'unit') {
        await createUnitProject({ ...nodeForm, project_id: projectId })
      } else if (type === 'division') {
        await createDivision({ ...nodeForm, unit_project_id: nodeDialogParent.value.id })
      } else if (type === 'sub_item') {
        await createSubItem({ ...nodeForm, division_id: nodeDialogParent.value.id })
      }
    }
    ElMessage.success('操作成功')
    showNodeDialog.value = false
    await loadProject()
  } finally {
    nodeSubmitting.value = false
  }
}

async function handleDeleteNode(data) {
  const names = { unit: '单位工程', division: '分部工程', sub_item: '分项工程' }
  await ElMessageBox.confirm(`确定删除${names[data.type]}「${data.label}」？子级数据也将被删除。`, '确认删除', { type: 'warning' })
  const fns = { unit: deleteUnitProject, division: deleteDivision, sub_item: deleteSubItem }
  await fns[data.type](data.id)
  ElMessage.success('删除成功')
  await loadProject()
}

// --- Load & edit project ---
async function loadProject() {
  loading.value = true
  try {
    project.value = await getProject(projectId)
    Object.assign(editForm, {
      name: project.value.name, code: project.value.code,
      description: project.value.description || '', location: project.value.location || '',
      client_name: project.value.client_name || '', contact_person: project.value.contact_person || '',
      contact_phone: project.value.contact_phone || '', status: project.value.status,
    })
  } finally {
    loading.value = false
  }
}

async function handleEditProject() {
  const valid = await editFormRef.value.validate().catch(() => false)
  if (!valid) return
  editSubmitting.value = true
  try {
    await updateProject(projectId, editForm)
    ElMessage.success('工程信息已更新')
    showEditDialog.value = false
    await loadProject()
  } finally {
    editSubmitting.value = false
  }
}

onMounted(loadProject)
</script>

<style scoped>
.info-card { margin-bottom: 16px; }
.tree-card { margin-bottom: 16px; }
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-right: 8px;
}
.node-label { display: flex; align-items: center; gap: 8px; }
.node-code { color: #999; font-size: 12px; }
.level-tag { margin-right: 4px; }
.node-actions { flex-shrink: 0; }
</style>
