<template>
  <div class="setup-wrap">
    <div class="pane setup-pane">
      <div class="pane-head">
        <span class="title">开始使用</span>
        <span class="spacer" />
        <span class="dim small setup-hint">三步把这台 Harbor 变成你的发布台：档案 → 登录 → 接入 AI</span>
      </div>

      <div class="pane-body setup-body">
        <el-steps :active="step" finish-status="success" align-center class="setup-steps">
          <el-step title="建档案" description="账号与 SOP 只留本机" />
          <el-step title="登录平台" description="在这台机器上完成登录" />
          <el-step title="接入 AI" description="MCP 配置复制即用" />
        </el-steps>

        <el-alert v-if="loadError" type="error" :closable="false" show-icon
                  title="读取初始化状态失败" :description="loadError" />

        <!-- 第 1 步：档案 -->
        <section v-if="step === 0" class="step-panel">
          <div class="lead">
            <h3>先给这台 Harbor 起个档案名</h3>
            <p class="dim">
              档案包含账号标识、内容主线、报告位置与进度目录，放在
              <code>profiles/&lt;name&gt;/</code>，已被 gitignore，不会进仓库。
              仓库里的 playbooks 只是模板。
            </p>
          </div>

          <el-form label-width="88px" class="setup-form" @submit.prevent="create">
            <el-form-item label="档案名">
              <el-input v-model="name" maxlength="32" placeholder="例如 default"
                        @keyup.enter="create" />
              <div class="field-tip dim small">只能用小写字母、数字、短横或下划线；一台机器一个人。</div>
            </el-form-item>

            <el-form-item label="接入平台">
              <el-checkbox-group v-model="selected" class="tpl-grid">
                <el-checkbox v-for="p in platformOptions" :key="p.id" :value="p.id" border
                             class="tpl-item">
                  <span class="tpl-name">{{ p.name }}</span>
                  <span class="tpl-meta dim">
                    {{ p.has_template ? (p.template?.schedule || '有 SOP 模板') : '仅登录 / 发布' }}
                  </span>
                </el-checkbox>
              </el-checkbox-group>
              <div class="tpl-tools">
                <el-button text size="small" @click="selectAll">
                  全选 {{ platformOptions.length }} 个平台
                </el-button>
                <el-button text size="small" @click="selectTemplates">只选有 SOP 的</el-button>
                <span class="dim small">已选 {{ selected.length }} 个</span>
              </div>
              <div class="field-tip dim small">
                勾选要登录、发布的平台；有 SOP 模板的生成个人 SOP，其余平台登录后直接发布。
              </div>
            </el-form-item>

            <el-form-item v-if="exists" label="已有档案">
              <el-checkbox v-model="force">覆盖 {{ name }}（旧档案会被重写）</el-checkbox>
            </el-form-item>
          </el-form>

          <div class="actions">
            <el-button type="primary" size="large" :loading="creating"
                       :disabled="!nameOk || !selected.length" @click="create">
              生成档案与 SOP
            </el-button>
            <span class="dim small">约 1 秒，不联网、不写仓库</span>
          </div>
        </section>

        <!-- 第 2 步：登录 -->
        <section v-else-if="step === 1" class="step-panel">
          <div class="result-card">
            <div class="result-icon"><el-icon><Check /></el-icon></div>
            <div class="result-main">
              <b>档案已生成</b>
              <div class="mono small">{{ result?.profile }}</div>
              <div class="dim small">
                {{ playbookCount }} 份个人 SOP · 进度目录 <span class="mono">{{ result?.progress }}</span>
              </div>
              <div v-if="check && !check.ok" class="check-bad small">
                <span>自检未通过：{{ check.problems.join('；') }}</span>
                <el-button link type="primary" size="small" :loading="rerendering"
                           @click="rerender">只重新生成 SOP</el-button>
              </div>
            </div>
          </div>

          <div class="lead">
            <h3>登录要在 Harbor 这台机器上完成</h3>
            <p class="dim">
              点「去登录」会在这台机器弹出 Harbor 自己的浏览器窗口，扫码或输密码后 cookie
              留在本地 profile。AI 客户端只查状态，不接触账号密码。
            </p>
          </div>

          <div class="login-grid">
            <div v-for="p in loginRows" :key="p.id" class="login-card">
              <div class="login-top">
                <b>{{ p.name }}</b>
                <el-tag size="small" effect="dark"
                        :type="p.state === 'online' ? 'success' : (p.state === 'waiting' ? 'warning' : 'info')">
                  {{ p.state === 'online' ? '在线' : (p.state === 'waiting' ? '等待扫码…' : '未登录') }}
                </el-tag>
              </div>
              <div class="dim small login-desc">{{ p.hint }}</div>
              <template v-if="p.browser">
                <el-button v-if="p.state !== 'online'" size="small" type="primary"
                           :loading="p.state === 'waiting'" @click="login(p.id)">
                  去登录
                </el-button>
                <el-button v-else size="small" @click="login(p.id)">重新登录</el-button>
              </template>
              <el-button v-else size="small" @click="openAccounts">去设置填凭据</el-button>
            </div>
          </div>

          <div class="actions">
            <el-button type="primary" size="large" @click="step = 2">下一步：接入 AI</el-button>
            <el-button size="large" @click="step = 2">稍后登录，先看接入</el-button>
            <el-button text @click="resetForm">重新建一个档案</el-button>
          </div>
        </section>

        <!-- 第 3 步：MCP -->
        <section v-else class="step-panel">
          <div class="lead">
            <h3>把 Harbor 接到你的 AI 客户端</h3>
            <p class="dim">
              Harbor 自带 MCP Server。下面是本机 stdio 配置，粘贴到豆包工作、Claude Code、Cursor
              等客户端的 MCP 配置里即可；路径按当前安装生成，换机器要改。
            </p>
          </div>

          <div class="mcp-card">
            <div class="mcp-head">
              <span class="mono small">mcpServers.harbor</span>
              <el-button size="small" :icon="CopyDocument" @click="copyConfig">复制配置</el-button>
            </div>
            <pre class="mcp-code">{{ mcpJson }}</pre>
          </div>

          <el-alert type="warning" :closable="false" show-icon
                    title="登录不在这里"
                    description="MCP 只调用 Harbor 的工具。登录仍在这台机器上用 Harbor 前端或 CLI 完成；未登录时任务会停在 waiting_human，等人接管后 resume。" />

          <div class="lead small-lead">
            <h3>接上之后可以做什么</h3>
            <p class="dim">
              建文章、AI 写/改/译、发布到已登录平台、原地更新、查任务状态；32 个工具以客户端列出的为准。
              先调 <code>list_articles</code> 验证连通，再发第一篇。
            </p>
          </div>

          <div class="actions">
            <el-button type="primary" size="large" @click="finish">进入写作台</el-button>
            <el-button size="large" @click="step = 1">回上一步看登录</el-button>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, CopyDocument } from '@element-plus/icons-vue'
import { api } from '@/api'
import { useHubStore } from '@/stores/hub'

const hub = useHubStore()

const state = ref({ profiles: [], templates: [], platforms: [], mcp: { json: '' } })
const step = ref(0)
const name = ref('default')
const selected = ref([])
const force = ref(false)
const creating = ref(false)
const result = ref(null)
const activeProfile = ref(null)
const check = ref(null)
const rerendering = ref(false)
const loadError = ref('')

const platformOptions = computed(() => {
  if (state.value.platforms?.length) return state.value.platforms
  // 兼容旧后端/旧测试：只有 templates 时，把模板当成平台清单。
  return (state.value.templates || []).map(t => ({
    ...t, name: t.title, has_template: true, template: t,
  }))
})
const nameOk = computed(() => /^[a-z0-9][a-z0-9_-]{0,31}$/.test(name.value))
const exists = computed(() => state.value.profiles.some(p => p.name === name.value))
const playbookCount = computed(() =>
  result.value?.playbooks?.length || activeProfile.value?.playbooks || 0)
const mcpJson = computed(() => state.value.mcp?.json || '')
const loginRows = computed(() => (result.value?.platforms || []).map(id => {
  const info = hub.platforms.find(p => p.id === id) || { id, name: id, needs_browser: true }
  const task = hub.loginTasks[id]
  const state = task?.status === 'running' || task?.status === 'pending'
    ? 'waiting'
    : (hub.accounts.some(a => a.platform === id && a.status === 'logined') ? 'online' : 'offline')
  return {
    id,
    name: info.name || id,
    browser: info.needs_browser !== false,
    hint: info.needs_browser === false ? '到设置里填凭据或抠令牌' : '浏览器扫码一次，长期复用',
    state,
  }
}))

onMounted(load)

async function load() {
  try {
    state.value = await api.onboardingState()
    if (state.value.profiles?.length) {
      const existing = state.value.profiles[0]
      adopt(existing)
      step.value = 1
      // 重开向导也自检一次：模板更新或副本被手改后要能看见漂移。
      check.value = await api.onboardingCheck(existing.name).catch(() => null)
    } else {
      selected.value = platformOptions.value
        .filter(p => p.has_template || p.template)
        .map(p => p.id)
    }
    if (!hub.platforms.length) await hub.loadPlatforms()
    await hub.loadStatus()
  } catch (e) {
    loadError.value = e?.response?.data?.message || String(e)
  }
}

function adopt(p) {
  activeProfile.value = p
  selected.value = p.platforms || []
  result.value = {
    name: p.name,
    profile: p.profile,
    platforms: p.platforms || [],
    playbooks: [],
    progress: `profiles/${p.name}/progress`,
  }
}

async function create() {
  if (!nameOk.value) { ElMessage.warning('档案名只能用小写字母、数字、- 或 _，最长 32 个字符'); return }
  if (!selected.value.length) { ElMessage.warning('至少选一个平台'); return }
  creating.value = true
  try {
    result.value = await api.onboardingInit({
      name: name.value,
      platforms: selected.value,
      force: force.value,
    })
    state.value = await api.onboardingState()
    activeProfile.value = state.value.profiles.find(p => p.name === name.value) || null
    check.value = await api.onboardingCheck(name.value).catch(() => null)
    step.value = 1
    ElMessage.success('档案与个人 SOP 已生成')
  } catch { /* 拦截器已提示；停留本步可改 */ } finally {
    creating.value = false
  }
}

function selectAll() {
  selected.value = platformOptions.value.map(p => p.id)
}

function selectTemplates() {
  selected.value = platformOptions.value
    .filter(p => p.has_template || p.template)
    .map(p => p.id)
}

function openAccounts() {
  hub.settingsTab = 'accounts'
  hub.switchView('settings')
}

async function login(platform) {
  try {
    await hub.startLogin(platform)
    ElMessage.info('已在这台机器弹出 Harbor 登录窗口，完成后会自动刷新状态')
  } catch { /* 拦截器已提示 */ }
}

async function rerender() {
  const target = activeProfile.value?.name || result.value?.name
  if (!target) return
  rerendering.value = true
  try {
    const next = await api.onboardingRerender(target)
    result.value = { ...result.value, ...next, playbooks: next.playbooks || [] }
    check.value = next.check || await api.onboardingCheck(target)
    if (activeProfile.value) {
      activeProfile.value = {
        ...activeProfile.value,
        platforms: next.platforms || activeProfile.value.platforms,
        playbooks: (next.playbooks || []).length,
      }
    }
    ElMessage.success('个人 SOP 已按当前档案重新生成')
  } catch { /* 拦截器已提示 */ } finally {
    rerendering.value = false
  }
}

function resetForm() {
  result.value = null
  activeProfile.value = null
  check.value = null
  force.value = false
  step.value = 0
  if (state.value.profiles.some(p => p.name === name.value)) {
    name.value = ''
  }
}

async function copyConfig() {
  const text = mcpJson.value
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('MCP 配置已复制')
  } catch {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    try {
      document.execCommand('copy')
      ElMessage.success('MCP 配置已复制')
    } finally {
      ta.remove()
    }
  }
}

function finish() {
  hub.needsSetup = false
  hub.switchView('write')
}

defineExpose({ step, name, selected, force, create, login, copyConfig, rerender,
               state, result, check, rerendering, platformOptions, selectAll,
               selectTemplates })
</script>

<style scoped lang="scss">
.setup-wrap { flex: 1; min-height: 0; display: flex; padding: 14px 16px; }
.setup-pane { flex: 1; }
.setup-body { overflow-y: auto; display: flex; flex-direction: column; gap: 20px; padding-top: 10px; }
.setup-hint { white-space: nowrap; }
.setup-steps { max-width: 920px; width: 100%; align-self: center; padding: 8px 0 4px; }
.step-panel { display: flex; flex-direction: column; gap: 16px; max-width: 920px; width: 100%; align-self: center; }
.lead h3 { margin: 0 0 6px; font-size: 16px; color: var(--tx-1); }
.lead p { margin: 0; line-height: 1.75; }
.lead code, .mono { font-family: var(--font-mono, ui-monospace, SFMono-Regular, Menlo, monospace); }
.lead code { padding: 1px 5px; border-radius: 4px; background: var(--surface-2); color: var(--tx-2); }
.small-lead h3 { font-size: 14px; }
.setup-form { max-width: 760px; }
.field-tip { margin-top: 4px; line-height: 1.6; }
.tpl-tools { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-top: 2px; }
.tpl-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 10px; width: 100%; }
.tpl-item { margin: 0 !important; height: auto; padding: 10px 12px; border-radius: 10px; }
.tpl-item :deep(.el-checkbox__label) { display: flex; flex-direction: column; gap: 3px; white-space: normal; }
.tpl-name { font-weight: 600; color: var(--tx-1); }
.tpl-meta { font-size: 11px; line-height: 1.4; }
.actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; padding-top: 2px; }
.result-card {
  display: flex; gap: 14px; align-items: center; padding: 16px 18px;
  border: 1px solid var(--line); border-radius: 12px; background: var(--surface);
  .result-icon {
    width: 42px; height: 42px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
    background: var(--accent-soft); color: var(--accent); font-size: 20px; flex-shrink: 0;
  }
  .result-main { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
  .result-main b { color: var(--tx-1); }
  .mono { word-break: break-all; color: var(--tx-2); }
  .check-bad {
    color: var(--el-color-danger); margin-top: 4px;
    display: flex; align-items: center; flex-wrap: wrap; gap: 6px;
  }
}
.login-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 12px; }
.login-card {
  border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px; background: var(--surface);
  display: flex; flex-direction: column; gap: 8px; align-items: flex-start;
  .login-top { display: flex; width: 100%; align-items: center; justify-content: space-between; gap: 8px; }
  .login-top b { color: var(--tx-1); }
  .login-desc { line-height: 1.5; }
}
.mcp-card { border: 1px solid var(--line); border-radius: 12px; background: var(--surface); overflow: hidden; }
.mcp-head {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  padding: 10px 14px; border-bottom: 1px solid var(--line-soft); color: var(--tx-3);
}
.mcp-code {
  margin: 0; padding: 14px 16px; max-height: 320px; overflow: auto;
  font-size: 12px; line-height: 1.65; color: var(--tx-2); background: var(--surface-2);
  font-family: var(--font-mono, ui-monospace, SFMono-Regular, Menlo, monospace);
}
.dim { color: var(--tx-3); }
.small { font-size: var(--fs-xs); }

@media (max-width: 767px) {
  .setup-wrap { padding: 8px; }
  .setup-hint { display: none; }
  .setup-steps { display: none; }
  .setup-form { max-width: none; }
  .actions { align-items: stretch; flex-direction: column; }
  .actions .el-button { width: 100%; }
}
</style>
