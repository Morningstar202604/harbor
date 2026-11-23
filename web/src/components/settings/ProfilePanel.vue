<template>
  <div class="profile-panel">
    <div class="pp-head">
      <div>
        <h3>内容档案</h3>
        <div class="dim small">档案决定 AI 的选题主线、写作风格、互动额度与每个平台的 SOP；只存本机。</div>
      </div>
      <span class="spacer" />
      <el-select v-if="overview.profiles.length" v-model="activeName" size="small"
                 style="width:180px" @change="activate">
        <el-option v-for="p in overview.profiles" :key="p.name" :label="p.name" :value="p.name">
          <span>{{ p.name }}</span>
          <span v-if="p.active" class="opt-active">当前</span>
        </el-option>
      </el-select>
      <el-button size="small" type="primary" @click="newOpen = true">新建档案</el-button>
    </div>

    <el-empty v-if="!overview.profiles.length"
              description="还没有档案，先在「开始使用」建一个" />

    <template v-else-if="detail">
      <div class="pp-summary">
        <div class="sum-main">
          <b>{{ detail.name }}</b>
          <el-tag v-if="detail.active" size="small" type="success" effect="dark">当前档案</el-tag>
          <el-tag v-else size="small" type="info" effect="plain">未激活</el-tag>
          <span class="dim small mono">{{ detail.profile }}</span>
        </div>
        <div class="sum-meta small">
          <span>{{ detail.platforms.length }} 个平台</span>
          <span>{{ detail.playbooks.length }} 份个人 SOP</span>
          <span v-if="detail.check.ok" class="ok">自检通过</span>
          <span v-else class="warn">{{ detail.check.problems.length }} 项待处理</span>
        </div>
        <el-button v-if="!detail.active" size="small" type="primary" plain
                   @click="activate(detail.name)">设为当前档案</el-button>
      </div>

      <div v-if="detail.check.problems.length" class="check-box">
        <div v-for="p in detail.check.problems" :key="p">· {{ p }}</div>
        <el-button size="small" text type="primary" :loading="rerendering"
                   @click="rerenderAll">按当前档案重新生成全部 SOP</el-button>
      </div>

      <div class="pp-grid">
        <section class="pp-card">
          <div class="card-head">
            <b>档案与策略</b>
            <span class="spacer" />
            <el-button size="small" type="primary" :loading="saving" @click="saveFields">保存</el-button>
          </div>
          <div class="dim small card-sub">表单保存会重写 profile.yaml，首次重写前留一份 .bak；想保留注释用高级 YAML。</div>
          <el-form label-width="100px" class="pp-form">
            <el-form-item label="内容主线">
              <el-input v-model="form.mainline" type="textarea" :rows="2" maxlength="500"
                        placeholder="AI 工程、Agent 落地、开发者工具、独立开发" />
            </el-form-item>
            <el-form-item label="写作口吻">
              <el-input v-model="form.voice" maxlength="500"
                        placeholder="短句、第一人称、具体事实；不写客服腔" />
            </el-form-item>
            <el-form-item label="避免写法">
              <el-input v-model="form.avoidText" type="textarea" :rows="3"
                        placeholder="每行一条，例如：首先/其次/最后" />
            </el-form-item>
            <div class="form-row">
              <el-form-item label="最少配图">
                <el-input-number v-model="form.min_images" :min="0" :max="99" size="small" />
              </el-form-item>
              <el-form-item label="最少代码块">
                <el-input-number v-model="form.min_code_blocks" :min="0" :max="99" size="small" />
              </el-form-item>
            </div>
            <el-form-item label="活跃时间窗">
              <el-input v-model="form.windowActive" placeholder="12:30-13:00" />
            </el-form-item>
            <el-form-item label="时区">
              <el-input v-model="form.timezone" placeholder="Asia/Shanghai" />
            </el-form-item>
          </el-form>

          <div class="sub-title">每日互动额度</div>
          <div class="form-row four">
            <el-form-item label="主动评论">
              <el-input-number v-model="form.proactive_comments" :min="0" :max="99" size="small" />
            </el-form-item>
            <el-form-item label="只回消息阈值">
              <el-input-number v-model="form.reply_only_after" :min="0" :max="99" size="small" />
            </el-form-item>
            <el-form-item label="单作者上限">
              <el-input-number v-model="form.max_per_author" :min="0" :max="99" size="small" />
            </el-form-item>
            <el-form-item label="回关上限">
              <el-input-number v-model="form.max_follow_back" :min="0" :max="99" size="small" />
            </el-form-item>
          </div>
          <div class="dim small">
            额度只约束 AI 的日常互动；发布文章不受影响。账号标识与栏目计划在「高级 YAML」里改。
          </div>

          <el-collapse class="adv">
            <el-collapse-item title="高级 YAML（完整档案，含 accounts / content_plan）" name="yaml">
              <div class="dim small" style="margin-bottom:6px">
                直接改原文件；保存前会校验 YAML 与 name，不会把半截文件写进去。
              </div>
              <el-input v-model="yamlText" type="textarea" :rows="14" class="mono yaml-box" />
              <div class="adv-ops">
                <el-button size="small" @click="yamlText = detail.yaml">还原</el-button>
                <el-button size="small" type="primary" :loading="savingYaml" @click="saveYaml">保存 YAML</el-button>
              </div>
            </el-collapse-item>
          </el-collapse>
        </section>

        <section class="pp-card">
          <div class="card-head">
            <b>平台与个人 SOP</b>
            <span class="spacer" />
            <el-button size="small" :loading="adding" :disabled="!availablePlatforms.length"
                       @click="addOpen = true">接入平台</el-button>
            <el-button size="small" :loading="rerendering" @click="rerenderAll">重生成 SOP</el-button>
          </div>
          <div class="dim small card-sub">点平台行看完整 SOP；可以按自己的习惯改，改过会标「自定义」，重生成前会提示覆盖。</div>
          <div class="plat-list">
            <div v-for="p in detail.platforms" :key="p.id" class="plat-row">
              <div class="pr-main">
                <b>{{ p.name }}</b>
                <span class="dim small">{{ p.needs_browser ? '浏览器登录' : 'API 凭据' }}</span>
              </div>
              <div class="pr-tags">
                <el-tag v-if="!sopOf(p.id)?.exists" size="small" type="info" effect="plain">无 SOP</el-tag>
                <el-tag v-else-if="sopOf(p.id)?.customized" size="small" type="warning" effect="plain">自定义</el-tag>
                <el-tag v-else-if="sopOf(p.id)?.drifted" size="small" type="danger" effect="plain">待重生成</el-tag>
                <el-tag v-else size="small" type="success" effect="plain">模板一致</el-tag>
              </div>
              <div class="pr-ops">
                <el-button size="small" text type="primary" @click="openSop(p)">
                  {{ sopOf(p.id)?.exists ? '查看/编辑' : '生成' }}
                </el-button>
                <el-button size="small" text type="danger" @click="removePlatform(p)">移除</el-button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </template>

    <el-dialog v-model="sopOpen" :title="`个人 SOP · ${sopPlatform?.name || ''}`"
               width="min(820px, 96vw)" top="4vh">
      <div class="sop-meta dim small">
        <span v-if="sopMeta?.customized" class="warn">已自定义：重生成会覆盖这里的改动</span>
        <span v-else-if="sopMeta?.drifted" class="warn">与模板不一致，可点「恢复模板」</span>
        <span v-else class="ok">与模板一致</span>
        <span v-if="sopMeta?.size">{{ Math.round(sopMeta.size / 1024) }} KB</span>
      </div>
      <el-input v-model="sopText" type="textarea" :rows="22" class="mono sop-box" />
      <template #footer>
        <el-button size="small" @click="sopOpen = false">关闭</el-button>
        <el-button size="small" :loading="sopSaving" @click="resetSop">恢复模板</el-button>
        <el-button size="small" type="primary" :loading="sopSaving" @click="saveSop">保存为自定义</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="addOpen" title="接入更多平台" width="min(680px, 96vw)">
      <p class="dim small">只追加平台与 SOP，不改已有账号、主线和进度。</p>
      <el-checkbox-group v-model="addSelected" class="new-grid">
        <el-checkbox v-for="p in availablePlatforms" :key="p.id" :value="p.id" border>
          {{ p.name }}
        </el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <el-button size="small" @click="addOpen = false">取消</el-button>
        <el-button size="small" type="primary" :loading="adding"
                   :disabled="!addSelected.length" @click="addPlatforms">添加并生成 SOP</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="newOpen" title="新建档案" width="min(680px, 96vw)">
      <p class="dim small">
        一台机器可以有多份档案（例如「技术号」「生活号」），切换后 AI 读到的 SOP 也跟着切。
        账号登录态与发布记录是所有档案共用的。
      </p>
      <el-form label-width="80px">
        <el-form-item label="档案名">
          <el-input v-model="newName" maxlength="32" placeholder="例如 tech" />
        </el-form-item>
        <el-form-item label="平台">
          <el-checkbox-group v-model="newPlatforms" class="new-grid">
            <el-checkbox v-for="p in catalog" :key="p.id" :value="p.id" border>
              {{ p.name }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="newOpen = false">取消</el-button>
        <el-button size="small" type="primary" :loading="creating"
                   :disabled="!newNameOk || !newPlatforms.length" @click="createProfile">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

const overview = ref({ active: '', profiles: [] })
const activeName = ref('')
const detail = ref(null)
const catalog = ref([])
const sopOpen = ref(false)
const sopPlatform = ref(null)
const sopText = ref('')
const sopMeta = ref(null)
const addOpen = ref(false)
const addSelected = ref([])
const newOpen = ref(false)
const newName = ref('')
const newPlatforms = ref([])
const saving = ref(false)
const savingYaml = ref(false)
const rerendering = ref(false)
const adding = ref(false)
const creating = ref(false)
const sopSaving = ref(false)
const yamlText = ref('')

const form = reactive({
  mainline: '', voice: '', avoidText: '', min_images: 0, min_code_blocks: 0,
  windowActive: '', timezone: '',
  proactive_comments: 0, reply_only_after: 0, max_per_author: 0, max_follow_back: 0,
})

const newNameOk = computed(() => /^[a-z0-9][a-z0-9_-]{0,31}$/.test(newName.value))
const availablePlatforms = computed(() => catalog.value.filter(
  p => !(detail.value?.platforms || []).some(x => x.id === p.id)))

function sopOf(id) {
  return (detail.value?.playbooks || []).find(x => x.platform === id)
}

function fillForm(data) {
  form.mainline = data.mainline || ''
  form.voice = data.voice || ''
  form.avoidText = (data.avoid || []).join('\n')
  form.min_images = Number(data.min_images || 0)
  form.min_code_blocks = Number(data.min_code_blocks || 0)
  form.windowActive = data.windows?.active || ''
  form.timezone = data.timezone || ''
  for (const k of ['proactive_comments', 'reply_only_after', 'max_per_author', 'max_follow_back']) {
    form[k] = Number(data.engagement?.[k] || 0)
  }
}

async function loadOverview() {
  overview.value = await api.workspace()
  if (!activeName.value || !overview.value.profiles.some(p => p.name === activeName.value)) {
    activeName.value = overview.value.active || overview.value.profiles[0]?.name || ''
  }
  if (activeName.value) await loadDetail()
}

async function loadDetail() {
  if (!activeName.value) { detail.value = null; return }
  detail.value = await api.workspaceProfile(activeName.value)
  yamlText.value = detail.value.yaml
  fillForm(detail.value.fields)
}

async function activate(name) {
  try {
    await api.workspaceActive(name)
    activeName.value = name
    await loadOverview()
    ElMessage.success(`已切换到档案 ${name}`)
  } catch { /* 拦截器已提示 */ }
}

async function saveFields() {
  if (!detail.value) return
  saving.value = true
  try {
    detail.value = await api.workspaceProfileSave(detail.value.name, {
      fields: {
        mainline: form.mainline,
        timezone: form.timezone,
        style: {
          voice: form.voice,
          avoid: form.avoidText.split('\n').map(s => s.trim()).filter(Boolean),
          min_images: Number(form.min_images),
          min_code_blocks: Number(form.min_code_blocks),
        },
        engagement: {
          proactive_comments: Number(form.proactive_comments),
          reply_only_after: Number(form.reply_only_after),
          max_per_author: Number(form.max_per_author),
          max_follow_back: Number(form.max_follow_back),
        },
        windows: { active: form.windowActive },
      },
    })
    yamlText.value = detail.value.yaml
    fillForm(detail.value.fields)
    if (detail.value.check.ok) ElMessage.success('档案已保存')
    else ElMessage.warning('档案已保存；主线/口吻变了，个人 SOP 需要重新生成才一致')
  } catch { /* 拦截器已提示 */ } finally { saving.value = false }
}

async function saveYaml() {
  if (!detail.value) return
  savingYaml.value = true
  try {
    detail.value = await api.workspaceProfileSave(detail.value.name, { yaml: yamlText.value })
    yamlText.value = detail.value.yaml
    fillForm(detail.value.fields)
    ElMessage.success('YAML 已保存并通过校验')
  } catch { /* 拦截器已提示 */ } finally { savingYaml.value = false }
}

async function rerenderAll() {
  if (!detail.value) return
  try {
    await ElMessageBox.confirm(
      '会用当前档案重新生成全部个人 SOP，手动改过的 SOP 会被覆盖。继续？',
      '重生成 SOP', { type: 'warning', confirmButtonText: '覆盖重生成', cancelButtonText: '取消' })
  } catch { return }
  rerendering.value = true
  try {
    await api.onboardingRerender(detail.value.name)
    await loadDetail()
    ElMessage.success('个人 SOP 已按当前档案重新生成')
  } catch { /* 拦截器已提示 */ } finally { rerendering.value = false }
}

async function openSop(p) {
  sopPlatform.value = p
  sopMeta.value = null
  sopText.value = ''
  try {
    sopMeta.value = await api.workspacePlaybook(detail.value.name, p.id)
    sopText.value = sopMeta.value.markdown
    sopOpen.value = true
  } catch { /* 拦截器已提示 */ }
}

async function saveSop() {
  if (!detail.value || !sopPlatform.value) return
  sopSaving.value = true
  try {
    sopMeta.value = await api.workspacePlaybookSave(
      detail.value.name, sopPlatform.value.id, sopText.value)
    sopText.value = sopMeta.value.markdown
    sopOpen.value = false
    await loadDetail()
    ElMessage.success('SOP 已保存为自定义；自检不再把它当模板漂移')
  } catch { /* 拦截器已提示 */ } finally { sopSaving.value = false }
}

async function resetSop() {
  if (!detail.value || !sopPlatform.value) return
  try {
    await ElMessageBox.confirm('恢复成仓库模板？你手改的内容会被覆盖。', '恢复模板',
                               { type: 'warning', confirmButtonText: '恢复', cancelButtonText: '取消' })
  } catch { return }
  sopSaving.value = true
  try {
    sopMeta.value = await api.workspacePlaybookReset(detail.value.name, sopPlatform.value.id)
    sopText.value = sopMeta.value.markdown
    sopOpen.value = false
    await loadDetail()
    ElMessage.success('已恢复模板')
  } catch { /* 拦截器已提示 */ } finally { sopSaving.value = false }
}

async function removePlatform(p) {
  if (!detail.value) return
  try {
    await ElMessageBox.confirm(
      `从档案移除「${p.name}」？会同时删掉它的个人 SOP；已登录的账号与历史发布记录不动。`,
      '移除平台', { type: 'warning', confirmButtonText: '移除', cancelButtonText: '取消' })
  } catch { return }
  try {
    detail.value = await api.workspaceRemovePlatform(detail.value.name, p.id)
    yamlText.value = detail.value.yaml
    fillForm(detail.value.fields)
    await loadOverview()
    ElMessage.success(`已移除 ${p.name}`)
  } catch { /* 拦截器已提示 */ }
}

async function addPlatforms() {
  if (!detail.value) return
  adding.value = true
  try {
    await api.onboardingAddPlatforms(detail.value.name, addSelected.value)
    addSelected.value = []
    addOpen.value = false
    await loadDetail()
    await loadOverview()
    ElMessage.success('平台已接入并补上个人 SOP')
  } catch { /* 拦截器已提示 */ } finally { adding.value = false }
}

async function createProfile() {
  if (!newNameOk.value || !newPlatforms.value.length) return
  creating.value = true
  try {
    await api.onboardingInit({ name: newName.value, platforms: newPlatforms.value })
    const name = newName.value
    newOpen.value = false
    newName.value = ''
    newPlatforms.value = []
    await api.workspaceActive(name)
    activeName.value = name
    await loadOverview()
    ElMessage.success(`档案 ${name} 已创建并设为当前`)
  } catch { /* 拦截器已提示 */ } finally { creating.value = false }
}

onMounted(async () => {
  try {
    const state = await api.onboardingState()
    catalog.value = state.platforms || []
    newPlatforms.value = (state.platforms || []).filter(p => p.recommended).map(p => p.id)
  } catch { /* 向导状态失败不阻断档案读取 */ }
  try { await loadOverview() } catch { /* 拦截器已提示 */ }
})

defineExpose({ overview, activeName, detail, form, yamlText, loadOverview, loadDetail,
               activate, saveFields, saveYaml, rerenderAll, openSop, saveSop, resetSop,
               removePlatform, addPlatforms, createProfile, newName, newPlatforms,
               newNameOk, addSelected, availablePlatforms, sopOf })
</script>

<style scoped lang="scss">
.profile-panel { display: flex; flex-direction: column; gap: 14px; padding-top: 8px; }
.pp-head { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.pp-head h3 { margin: 0 0 4px; font-size: var(--fs-lg); color: var(--tx-1); }
.opt-active { float: right; color: var(--el-color-success); font-size: var(--fs-xs); }
.spacer { flex: 1; }
.dim { color: var(--tx-3); }
.small { font-size: var(--fs-xs); }
.mono { font-family: var(--font-mono, ui-monospace, SFMono-Regular, Menlo, monospace); }
.pp-summary {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
  border: 1px solid var(--line); background: var(--surface); border-radius: 12px;
  padding: 12px 16px;
}
.sum-main { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.sum-meta { display: flex; gap: 12px; align-items: center; }
.sum-meta .ok { color: var(--el-color-success); }
.sum-meta .warn { color: var(--el-color-warning); }
.check-box {
  border: 1px solid color-mix(in srgb, var(--el-color-warning) 40%, var(--line));
  background: color-mix(in srgb, var(--el-color-warning) 8%, transparent);
  border-radius: 10px; padding: 10px 14px; font-size: var(--fs-xs);
  color: var(--tx-2); display: flex; flex-direction: column; gap: 3px;
}
.pp-grid { display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(0, .95fr); gap: 14px; }
.pp-card {
  border: 1px solid var(--line); background: var(--surface); border-radius: 12px;
  padding: 14px 16px; display: flex; flex-direction: column; gap: 10px;
  min-width: 0;
}
.card-head { display: flex; align-items: center; gap: 8px; }
.card-sub { line-height: 1.6; }
.pp-form :deep(.el-form-item) { margin-bottom: 10px; }
.form-row { display: flex; gap: 8px; flex-wrap: wrap; }
.form-row.four :deep(.el-form-item) { margin-bottom: 8px; flex: 1 1 120px; }
.form-row.four :deep(.el-form-item__label) { width: auto !important; padding-right: 6px; font-size: var(--fs-xs); }
.sub-title { font-weight: 600; color: var(--tx-1); margin-top: 2px; font-size: var(--fs-sm); }
.adv { margin-top: 4px; }
.yaml-box :deep(textarea) { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; }
.adv-ops { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; }
.plat-list { display: flex; flex-direction: column; gap: 8px; }
.plat-row {
  display: flex; align-items: center; gap: 10px; border: 1px solid var(--line);
  border-radius: 10px; padding: 9px 12px; background: var(--bg-soft, transparent);
}
.pr-main { display: flex; flex-direction: column; gap: 2px; min-width: 120px; }
.pr-tags { flex: 1; }
.pr-ops { display: flex; gap: 2px; }
.sop-meta { display: flex; gap: 12px; margin-bottom: 8px; }
.sop-meta .ok { color: var(--el-color-success); }
.sop-meta .warn { color: var(--el-color-warning); }
.sop-box :deep(textarea) { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; }
.new-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 8px; }
@media (max-width: 1100px) {
  .pp-grid { grid-template-columns: 1fr; }
}
</style>
