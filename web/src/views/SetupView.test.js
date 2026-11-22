import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api', () => ({
  api: {
    onboardingState: vi.fn().mockResolvedValue({
      profiles: [],
      templates: [
        { id: 'cnblogs', title: '博客园每日运营', platform: 'cnblogs', schedule: '每天 1 次' },
        { id: 'juejin', title: '掘金每日运营', platform: 'juejin', schedule: '每天 1 次' },
      ],
      mcp: { json: '{"mcpServers":{"harbor":{}}}' },
    }),
    onboardingInit: vi.fn().mockResolvedValue({
      name: 'demo',
      profile: 'profiles/demo/profile.yaml',
      platforms: ['cnblogs'],
      playbooks: ['profiles/demo/playbooks/cnblogs.md'],
      progress: 'profiles/demo/progress',
    }),
    onboardingCheck: vi.fn().mockResolvedValue({ ok: true, problems: [] }),
    platforms: vi.fn().mockResolvedValue([
      { id: 'cnblogs', name: '博客园', needs_browser: false },
      { id: 'juejin', name: '掘金', needs_browser: true },
    ]),
    status: vi.fn().mockResolvedValue({ accounts: [] }),
    pendingHuman: vi.fn().mockResolvedValue([]),
    tasks: vi.fn().mockResolvedValue([]),
    startLogin: vi.fn().mockResolvedValue({ task_id: 'tk-login' }),
    task: vi.fn().mockResolvedValue({ status: 'ok' }),
  },
  default: {},
}))

import { api } from '@/api'
import SetupView from '@/views/SetupView.vue'
import { useHubStore } from '@/stores/hub'

const stubs = {
  'el-steps': { template: '<div class="steps"><slot /></div>' },
  'el-step': { props: ['title'], template: '<div>{{ title }}</div>' },
  'el-form': { template: '<form><slot /></form>' },
  'el-form-item': { template: '<div><slot /></div>' },
  'el-checkbox-group': { template: '<div><slot /></div>' },
  'el-checkbox': { template: '<label><slot /></label>' },
  'el-alert': { props: ['title'], template: '<div class="alert">{{ title }}</div>' },
  'el-icon': { template: '<i><slot /></i>' },
}

const mountView = () => mount(SetupView, { global: { stubs } })

describe('SetupView 首次使用向导', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('空档案时进入第 1 步，默认勾选全部模板', async () => {
    const w = mountView()
    await flushPromises()
    expect(w.vm.step).toBe(0)
    expect(w.vm.selected).toEqual(['cnblogs', 'juejin'])
    expect(w.vm.result).toBe(null)
  })

  it('创建档案后进入登录步，平台与档案信息可见', async () => {
    api.onboardingInit.mockResolvedValue({
      name: 'demo',
      profile: 'profiles/demo/profile.yaml',
      platforms: ['cnblogs', 'juejin'],
      playbooks: ['profiles/demo/playbooks/cnblogs.md', 'profiles/demo/playbooks/juejin.md'],
      progress: 'profiles/demo/progress',
    })
    const w = mountView()
    await flushPromises()
    w.vm.name = 'demo'
    await w.vm.create()
    await flushPromises()

    expect(api.onboardingInit).toHaveBeenCalledWith({
      name: 'demo', platforms: ['cnblogs', 'juejin'], force: false,
    })
    expect(w.vm.step).toBe(1)
    expect(w.vm.result.profile).toBe('profiles/demo/profile.yaml')
    expect(w.findAll('.login-card').length).toBe(2)
  })

  it('登录按钮走 Harbor 自己的 startLogin，而不是模型浏览器', async () => {
    const w = mountView()
    await flushPromises()
    const hub = useHubStore()
    const spy = vi.spyOn(hub, 'startLogin').mockResolvedValue()
    w.vm.step = 1
    w.vm.result = {
      name: 'demo', profile: 'profiles/demo/profile.yaml',
      platforms: ['juejin'], playbooks: [], progress: 'profiles/demo/progress',
    }
    await flushPromises()

    const btn = w.findAll('button').find(b => b.text() === '去登录')
    expect(btn).toBeTruthy()
    await btn.trigger('click')
    expect(spy).toHaveBeenCalledWith('juejin')
  })

  it('已有档案直接进登录步，不强迫重新建', async () => {
    api.onboardingState.mockResolvedValue({
      profiles: [{ name: 'me', profile: 'profiles/me/profile.yaml',
                   platforms: ['cnblogs'], playbooks: 1 }],
      templates: [],
      mcp: { json: '{}' },
    })
    const w = mountView()
    await flushPromises()
    expect(w.vm.step).toBe(1)
    expect(w.vm.result.profile).toBe('profiles/me/profile.yaml')
  })
})
