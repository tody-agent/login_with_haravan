<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'

interface CheckItem {
  id: string
  label: string
  priority: 'P0' | 'P1' | 'P2'
  category: string
  note?: string
}

interface CheckGroup {
  title: string
  icon: string
  description: string
  items: CheckItem[]
}

const props = defineProps<{
  storageKey?: string
  groups: CheckGroup[]
}>()

const key = computed(() => props.storageKey || 'uat-checklist-state')

// State
const checked = ref<Record<string, boolean>>({})
const notes = ref<Record<string, string>>({})
const filterPriority = ref<string>('all')
const filterStatus = ref<string>('all')
const showExport = ref(false)
const exportText = ref('')
const testerName = ref('')
const testDate = ref('')

// Load from localStorage
onMounted(() => {
  if (typeof window === 'undefined') return
  try {
    const saved = localStorage.getItem(key.value)
    if (saved) {
      const parsed = JSON.parse(saved)
      checked.value = parsed.checked || {}
      notes.value = parsed.notes || {}
      testerName.value = parsed.testerName || ''
      testDate.value = parsed.testDate || ''
    }
  } catch (e) {
    console.warn('Failed to load UAT state', e)
  }
})

// Save to localStorage
function save() {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(key.value, JSON.stringify({
      checked: checked.value,
      notes: notes.value,
      testerName: testerName.value,
      testDate: testDate.value,
      lastSaved: new Date().toISOString()
    }))
  } catch (e) {
    console.warn('Failed to save UAT state', e)
  }
}

watch([checked, notes, testerName, testDate], save, { deep: true })

// Computed stats
const allItems = computed(() => props.groups.flatMap(g => g.items))

const totalItems = computed(() => allItems.value.length)
const checkedCount = computed(() => allItems.value.filter(i => checked.value[i.id]).length)
const progressPercent = computed(() => totalItems.value ? Math.round((checkedCount.value / totalItems.value) * 100) : 0)

const statsByPriority = computed(() => {
  const stats: Record<string, { total: number; done: number }> = {}
  for (const item of allItems.value) {
    if (!stats[item.priority]) stats[item.priority] = { total: 0, done: 0 }
    stats[item.priority].total++
    if (checked.value[item.id]) stats[item.priority].done++
  }
  return stats
})

// Filter
function filteredItems(items: CheckItem[]) {
  return items.filter(item => {
    if (filterPriority.value !== 'all' && item.priority !== filterPriority.value) return false
    if (filterStatus.value === 'done' && !checked.value[item.id]) return false
    if (filterStatus.value === 'pending' && checked.value[item.id]) return false
    return true
  })
}

function filteredGroups() {
  return props.groups
    .map(g => ({ ...g, filteredItems: filteredItems(g.items) }))
    .filter(g => g.filteredItems.length > 0)
}

// Actions
function toggleItem(id: string) {
  checked.value[id] = !checked.value[id]
}

function resetAll() {
  if (typeof window !== 'undefined' && !window.confirm('⚠️ Xóa toàn bộ kết quả đã tích? Thao tác này không thể hoàn tác.')) return
  checked.value = {}
  notes.value = {}
}

function checkAllInGroup(group: CheckGroup) {
  for (const item of group.items) {
    checked.value[item.id] = true
  }
}

function uncheckAllInGroup(group: CheckGroup) {
  for (const item of group.items) {
    checked.value[item.id] = false
  }
}

// Export
function generateReport() {
  const lines: string[] = []
  lines.push('# BÁO CÁO NGHIỆM THU UAT — HARAVAN HELPDESK')
  lines.push('')
  lines.push(`- **Ngày kiểm thử:** ${testDate.value || '(chưa nhập)'}`)
  lines.push(`- **Người kiểm thử:** ${testerName.value || '(chưa nhập)'}`)
  lines.push(`- **Tiến độ:** ${checkedCount.value}/${totalItems.value} (${progressPercent.value}%)`)
  lines.push(`- **Thời điểm xuất báo cáo:** ${new Date().toLocaleString('vi-VN')}`)
  lines.push('')

  for (const p of ['P0', 'P1', 'P2']) {
    const s = statsByPriority.value[p]
    if (s) lines.push(`- **${p}:** ${s.done}/${s.total} hoàn thành`)
  }
  lines.push('')
  lines.push('---')
  lines.push('')

  for (const group of props.groups) {
    lines.push(`## ${group.icon} ${group.title}`)
    lines.push('')
    lines.push(`> ${group.description}`)
    lines.push('')
    lines.push('| Trạng thái | Ưu tiên | Hạng mục | Ghi chú |')
    lines.push('|---|---|---|---|')
    for (const item of group.items) {
      const status = checked.value[item.id] ? '✅ Đạt' : '⬜ Chưa test'
      const note = notes.value[item.id] || ''
      lines.push(`| ${status} | ${item.priority} | ${item.label} | ${note} |`)
    }
    lines.push('')
  }

  lines.push('---')
  lines.push('')
  lines.push('## Kết luận')
  lines.push('')
  if (progressPercent.value === 100) {
    lines.push('✅ **Tất cả hạng mục đã được kiểm thử và đạt yêu cầu.**')
  } else {
    const pending = allItems.value.filter(i => !checked.value[i.id])
    lines.push(`⚠️ **Còn ${pending.length} hạng mục chưa hoàn thành:**`)
    lines.push('')
    for (const item of pending) {
      lines.push(`- [${item.priority}] ${item.label}`)
    }
  }

  exportText.value = lines.join('\n')
  showExport.value = true
}

function copyReport() {
  if (typeof navigator !== 'undefined') {
    navigator.clipboard.writeText(exportText.value)
  }
}

function priorityColor(p: string) {
  switch (p) {
    case 'P0': return '#ef4444'
    case 'P1': return '#f59e0b'
    case 'P2': return '#3b82f6'
    default: return '#6b7280'
  }
}

function groupProgress(group: CheckGroup) {
  const total = group.items.length
  const done = group.items.filter(i => checked.value[i.id]).length
  return { total, done, percent: total ? Math.round((done / total) * 100) : 0 }
}
</script>

<template>
  <div class="uat-root">
    <!-- Header info -->
    <div class="uat-header">
      <div class="uat-header-fields">
        <div class="uat-field">
          <label>👤 Người kiểm thử</label>
          <input v-model="testerName" placeholder="Nhập tên..." />
        </div>
        <div class="uat-field">
          <label>📅 Ngày kiểm thử</label>
          <input v-model="testDate" type="date" />
        </div>
      </div>

      <!-- Progress bar -->
      <div class="uat-progress-section">
        <div class="uat-progress-header">
          <span class="uat-progress-label">Tiến độ tổng thể</span>
          <span class="uat-progress-value">{{ checkedCount }} / {{ totalItems }} ({{ progressPercent }}%)</span>
        </div>
        <div class="uat-progress-track">
          <div class="uat-progress-bar" :style="{ width: progressPercent + '%' }" :class="{ complete: progressPercent === 100 }"></div>
        </div>
        <!-- Priority breakdown -->
        <div class="uat-priority-stats">
          <span v-for="(stat, p) in statsByPriority" :key="p" class="uat-priority-badge" :style="{ '--badge-color': priorityColor(String(p)) }">
            {{ p }}: {{ stat.done }}/{{ stat.total }}
          </span>
        </div>
      </div>
    </div>

    <!-- Filters & Actions -->
    <div class="uat-toolbar">
      <div class="uat-filters">
        <select v-model="filterPriority">
          <option value="all">Tất cả ưu tiên</option>
          <option value="P0">🔴 P0 — Bắt buộc</option>
          <option value="P1">🟡 P1 — Quan trọng</option>
          <option value="P2">🔵 P2 — Nên có</option>
        </select>
        <select v-model="filterStatus">
          <option value="all">Tất cả trạng thái</option>
          <option value="done">✅ Đã hoàn thành</option>
          <option value="pending">⬜ Chưa hoàn thành</option>
        </select>
      </div>
      <div class="uat-actions">
        <button class="uat-btn uat-btn-export" @click="generateReport">📋 Xuất báo cáo</button>
        <button class="uat-btn uat-btn-danger" @click="resetAll">🗑️ Xóa tất cả</button>
      </div>
    </div>

    <!-- Groups -->
    <div v-for="group in filteredGroups()" :key="group.title" class="uat-group">
      <div class="uat-group-header">
        <div class="uat-group-title-row">
          <h3>{{ group.icon }} {{ group.title }}</h3>
          <div class="uat-group-actions">
            <button class="uat-btn-sm" @click="checkAllInGroup(group)" title="Tích hết">✅ Tất cả</button>
            <button class="uat-btn-sm uat-btn-sm-outline" @click="uncheckAllInGroup(group)" title="Bỏ tích hết">↩️ Bỏ hết</button>
          </div>
        </div>
        <p class="uat-group-desc">{{ group.description }}</p>
        <div class="uat-group-progress">
          <div class="uat-group-progress-track">
            <div class="uat-group-progress-bar" :style="{ width: groupProgress(group).percent + '%' }" :class="{ complete: groupProgress(group).percent === 100 }"></div>
          </div>
          <span class="uat-group-progress-text">{{ groupProgress(group).done }}/{{ groupProgress(group).total }}</span>
        </div>
      </div>

      <div class="uat-items">
        <div v-for="item in filteredItems(group.items)" :key="item.id" class="uat-item" :class="{ 'uat-item-done': checked[item.id] }">
          <div class="uat-item-main" @click="toggleItem(item.id)">
            <div class="uat-checkbox" :class="{ checked: checked[item.id] }">
              <svg v-if="checked[item.id]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <span class="uat-priority-tag" :style="{ backgroundColor: priorityColor(item.priority) + '20', color: priorityColor(item.priority), borderColor: priorityColor(item.priority) + '40' }">
              {{ item.priority }}
            </span>
            <span class="uat-item-label" :class="{ done: checked[item.id] }">{{ item.label }}</span>
          </div>
          <div class="uat-item-note">
            <input v-model="notes[item.id]" placeholder="Ghi chú..." class="uat-note-input" @click.stop />
          </div>
        </div>
      </div>
    </div>

    <!-- Auto-save notice -->
    <div class="uat-autosave-notice">
      💾 Dữ liệu tự động lưu trên trình duyệt của bạn. Khi đổi máy hoặc xóa cache, dữ liệu sẽ bị mất — hãy xuất báo cáo để lưu lại.
    </div>

    <!-- Export modal -->
    <Teleport to="body">
      <div v-if="showExport" class="uat-modal-overlay" @click.self="showExport = false">
        <div class="uat-modal">
          <div class="uat-modal-header">
            <h3>📋 Báo cáo nghiệm thu UAT</h3>
            <button class="uat-modal-close" @click="showExport = false">✕</button>
          </div>
          <div class="uat-modal-body">
            <textarea v-model="exportText" readonly class="uat-export-textarea" />
          </div>
          <div class="uat-modal-footer">
            <button class="uat-btn uat-btn-export" @click="copyReport">📄 Copy vào clipboard</button>
            <button class="uat-btn" @click="showExport = false">Đóng</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
