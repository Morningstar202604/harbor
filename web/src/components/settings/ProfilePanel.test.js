import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

vi.mock('@/api', () => {
  const profile = {
    name: 'demo', active: true, profile: 'profiles/demo/profile.yaml',
    yaml: 'name: demo\nplatforms: [cnblogs]\n',
    fields: {
      mainline: 'AI 工程', voice: '短句', avoid: ['首先/其次'], min_images: 2,
      min_code_blocks: 1, timezone: 'Asia/Shanghai',
      engagement: { proactive_comments: 4, reply_only_after: 4, max_per_author: 1, max_follow_back: 3 },
      windows: { active: '12:30-13:00' }, accounts: {},
    },
    platforms: [{ id: 'cnblogs', name: '博客园', needs_browser: false }],
    playbooks: [{ platform: 'cnblogs', exists: true, customized: false, drifted: false, size: 100, title: '博客园 SOP' }],
    check: { ok: true, problems: [] }, backup: false,
  }
  return {
    api: {
      onboardingState: vi.fn().mockResolvedValue({
        platforms: [{ id: 'cnblogs', name: '博客园', recommended: true }],
        profiles: [],
      }),
      workspace: vi.fn().mockResolvedValue({
        active: 'demo', profiles: [{ name: 'demo', active: true }],
      }),
      workspaceProfile: vi.fn().mockResolvedValue(profile),
      workspaceProfileSave: vi.fn().mockImplementation(async (name, body) => ({
        ...profile,
        fields: body.yaml ? profile.fields : {
          ...profile.fields,
          mainline: body.fields?.mainline ?? profile.fields.mainline,
        },
      })),
      workspaceActive: vi.fn().mockResolvedValue({ active: 'demo' }),
      workspacePlaybook: vi.fn().mockResolvedValue({
        platform: 'cnblogs', markdown: '# SOP', customized: false, size: 5,
      }),
      workspacePlaybookSave: vi.fn().mockResolvedValue({
        platform: 'cnblogs', markdown: '# SOP 自定义', customized: true, size: 9,
      }),
      workspacePlaybookReset: vi.fn().mockResolvedValue({
        platform: 'cnblogs', markdown: '# SOP', customized: false, size: 5,
      }),
      workspaceRemovePlatform: vi.fn().mockResolvedValue(profile),
      onboardingAddPlatforms: vi.fn().mockResolvedValue({ platforms: ['cnblogs'] }),
      onboardingRerender: vi.fn().mockResolvedValue({}),
      onboardingInit: vi.fn().mockResolvedValue({}),
    },
  }
})

import ProfilePanel from '@/components/settings/ProfilePanel.vue'

describe('ProfilePanel 档案与 SOP 管理', () => {
  let w
  beforeEach(() => { w = null })
  afterEach(() => { w?.unmount(); vi.clearAllMocks() })

  const mountPanel = async () => {
    w = mount(ProfilePanel)
    await flushPromises()
    return w
  }

  it('载入当前档案并回填主线/风格/额度', async () => {
    w = await mountPanel()
    expect(w.vm.detail.name).toBe('demo')
    expect(w.vm.form.mainline).toBe('AI 工程')
    expect(w.vm.form.proactive_comments).toBe(4)
    expect(w.vm.yamlText).toContain('name: demo')
  })

  it('表单保存按后端嵌套字段提交，不是一坨扁平键', async () => {
    const { api } = await import('@/api')
    w = await mountPanel()
    w.vm.form.mainline = '只写实测'
    w.vm.form.avoidText = '首先/其次\n综上'
    await w.vm.saveFields()
    const [, body] = api.workspaceProfileSave.mock.calls.at(-1)
    expect(body.fields.mainline).toBe('只写实测')
    expect(body.fields.style.avoid).toEqual(['首先/其次', '综上'])
    expect(body.fields.engagement.proactive_comments).toBe(4)
    expect(body.fields.windows.active).toBe('12:30-13:00')
  })

  it('SOP 可以查看、保存自定义；保存后刷新档案状态', async () => {
    const { api } = await import('@/api')
    w = await mountPanel()
    await w.vm.openSop(w.vm.detail.platforms[0])
    expect(w.vm.sopText).toBe('# SOP')
    await w.vm.saveSop()
    expect(api.workspacePlaybookSave).toHaveBeenCalledWith('demo', 'cnblogs', '# SOP')
    expect(w.vm.sopOpen).toBe(false)
    expect(api.workspaceProfile).toHaveBeenCalled()
  })

  it('移除平台走确认并刷新清单', async () => {
    const { api } = await import('@/api')
    w = await mountPanel()
    await w.vm.removePlatform(w.vm.detail.platforms[0])
    expect(api.workspaceRemovePlatform).toHaveBeenCalledWith('demo', 'cnblogs')
  })
})
