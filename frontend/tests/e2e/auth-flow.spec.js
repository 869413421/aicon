import { test, expect } from '@playwright/test'
import { takeScreenshot } from './utils/test-helpers.js'

test.describe('用户认证流程测试', () => {
  test.beforeEach(async ({ page }) => {
    // 清除cookies
    await page.context().clearCookies()
    // 清除本地存储（在about:blank页面避免权限问题）
    await page.goto('about:blank')
    await page.evaluate(() => {
      try {
        localStorage.clear()
      } catch (e) {
        // 忽略localStorage错误
      }
    })
  })

  test('用户登出流程测试', async ({ page }) => {
    // 使用测试用户登录
    await page.goto('/login')
    await page.fill('input[placeholder="请输入用户名"]', 'testuser1')
    await page.fill('input[placeholder="请输入密码"]', 'TestPassword123!')
    await page.click('button:has-text("登录")')

    // 等待跳转到dashboard
    await page.waitForURL(/\/dashboard/)

    // 验证已登录 - 检查dashboard内容
    await expect(page.locator('text=内容创作工作台')).toBeVisible()
    await expect(page.locator('.user-avatar')).toBeVisible()

    // 截图：已登录的dashboard
    await takeScreenshot(page, 'dashboard-logged-in')

    // 点击用户下拉菜单
    await page.click('.user-info')

    // 验证下拉菜单选项
    await expect(page.locator('text=个人资料')).toBeVisible()
    await expect(page.locator('text=系统设置')).toBeVisible()
    await expect(page.locator('text=退出登录')).toBeVisible()

    // 截图：用户下拉菜单
    await takeScreenshot(page, 'user-dropdown-menu')

    // 点击退出登录
    await page.click('text=退出登录')

    // 验证退出确认对话框
    await expect(page.locator('.el-message-box')).toBeVisible()
    await expect(page.locator('text=确定要退出登录吗？')).toBeVisible()
    await expect(page.locator('button:has-text("确定退出")')).toBeVisible()
    await expect(page.locator('button:has-text("取消")')).toBeVisible()

    // 截图：退出确认对话框
    await takeScreenshot(page, 'logout-confirm-dialog')

    // 确认退出
    await page.click('button:has-text("确定退出")')

    // 验证跳转到登录页面
    await page.waitForURL('/login')
    await expect(page.locator('text=登录')).toBeVisible()

    // 验证无法直接访问需要认证的页面
    await page.goto('/dashboard')
    await page.waitForURL('/login') // 应该被重定向到登录页

    // 截图：退出后重定向到登录页
    await takeScreenshot(page, 'logout-redirect-to-login')
  })

  test('系统设置页面功能测试', async ({ page }) => {
    // 登录
    await page.goto('/login')
    await page.fill('input[placeholder="请输入用户名"]', 'testuser1')
    await page.fill('input[placeholder="请输入密码"]', 'TestPassword123!')
    await page.click('button:has-text("登录")')
    await page.waitForURL(/\/dashboard/)

    // 通过下拉菜单进入设置页面
    await page.click('.user-info')
    await page.click('text=系统设置')
    await page.waitForURL('/settings')

    // 验证设置页面标题和菜单
    await expect(page.locator('h1')).toContainText('系统设置')
    await expect(page.locator('text=个人资料')).toBeVisible()
    await expect(page.locator('text=账户安全')).toBeVisible()
    await expect(page.locator('text=偏好设置')).toBeVisible()

    // 测试个人资料标签
    await expect(page.locator('.el-menu-item.is-active')).toContainText('个人资料')
    await expect(page.locator('input[placeholder="请输入显示名称"]')).toBeVisible()
    await expect(page.locator('input[placeholder="请输入头像URL"]')).toBeVisible()
    await expect(page.locator('textarea[placeholder="请输入个人简介"]')).toBeVisible()

    // 截图：个人资料设置
    await takeScreenshot(page, 'settings-profile-tab')

    // 测试账户安全标签
    await page.click('text=账户安全')
    await expect(page.locator('text=修改密码')).toBeVisible()
    await expect(page.locator('button:has-text("修改密码")')).toBeVisible()

    // 点击修改密码按钮
    await page.click('button:has-text("修改密码")')

    // 验证密码修改对话框
    await expect(page.locator('.el-dialog')).toBeVisible()
    await expect(page.locator('text=修改密码')).toBeVisible()
    await expect(page.locator('input[placeholder="请输入当前密码"]')).toBeVisible()
    await expect(page.locator('input[placeholder="请输入新密码"]')).toBeVisible()
    await expect(page.locator('input[placeholder="请再次输入新密码"]')).toBeVisible()

    // 截图：密码修改对话框
    await takeScreenshot(page, 'password-change-dialog')

    // 关闭对话框
    await page.keyboard.press('Escape')

    // 测试偏好设置标签
    await page.click('text=偏好设置')
    await expect(page.locator('text=主题模式')).toBeVisible()
    await expect(page.locator('text=语言')).toBeVisible()
    await expect(page.locator('text=时区')).toBeVisible()

    // 截图：偏好设置
    await takeScreenshot(page, 'settings-preferences-tab')
  })

  test('用户资料更新测试', async ({ page }) => {
    // 登录
    await page.goto('/login')
    await page.fill('input[placeholder="请输入用户名"]', 'testuser1')
    await page.fill('input[placeholder="请输入密码"]', 'TestPassword123!')
    await page.click('button:has-text("登录")')
    await page.waitForURL(/\/dashboard/)

    // 进入设置页面
    await page.goto('/settings')

    // 确保在个人资料标签
    await page.click('text=个人资料')

    // 填写更新信息
    const newDisplayName = '更新后的显示名称'
    const newBio = '这是更新后的个人简介'

    await page.fill('input[placeholder="请输入显示名称"]', newDisplayName)
    await page.fill('textarea[placeholder="请输入个人简介"]', newBio)

    // 截图：填写后的表单
    await takeScreenshot(page, 'profile-form-filled')

    // 验证输入成功
    await expect(page.locator('input[placeholder="请输入显示名称"]')).toHaveValue(newDisplayName)
    await expect(page.locator('textarea[placeholder="请输入个人简介"]')).toHaveValue(newBio)

    // 点击保存按钮（如果存在）
    const saveButton = page.locator('button:has-text("保存")')
    if (await saveButton.isVisible()) {
      await saveButton.click()

      // 等待保存完成（可能有成功消息）
      await page.waitForTimeout(1000)

      // 截图：保存后状态
      await takeScreenshot(page, 'profile-form-saved')
    }
  })

  test('响应式导航测试', async ({ page }) => {
    // 测试桌面端导航
    await page.setViewportSize({ width: 1280, height: 720 })
    await page.goto('/login')

    await expect(page.locator('h2')).toContainText('登录')
    await expect(page.locator('input[placeholder="请输入用户名"]')).toBeVisible()

    // 截图：桌面端登录页
    await takeScreenshot(page, 'login-desktop')

    // 测试移动端导航
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/login')

    await expect(page.locator('h2')).toContainText('登录')
    await expect(page.locator('input[placeholder="请输入用户名"]')).toBeVisible()

    // 截图：移动端登录页
    await takeScreenshot(page, 'login-mobile')
  })
})