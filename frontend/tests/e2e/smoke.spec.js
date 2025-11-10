import { test, expect } from '@playwright/test'
import { takeScreenshot } from './utils/test-helpers.js'

test.describe('冒烟测试', () => {
  test('页面加载测试', async ({ page }) => {
    // 测试登录页面加载
    await page.goto('/login')
    await expect(page).toHaveTitle(/AICG/)
    await expect(page.locator('h2')).toContainText('登录')
    await expect(page.locator('input[placeholder="请输入用户名"]')).toBeVisible()
    await expect(page.locator('input[placeholder="请输入密码"]')).toBeVisible()
    await expect(page.locator('button:has-text("登录")')).toBeVisible()

    await takeScreenshot(page, 'login-page-smoke')
  })

  test('注册页面加载测试', async ({ page }) => {
    // 测试注册页面加载
    await page.goto('/register')
    await expect(page.locator('h2')).toContainText('注册')
    await expect(page.locator('input[placeholder="请输入用户名"]')).toBeVisible()
    await expect(page.locator('input[placeholder="请输入邮箱"]')).toBeVisible()
    await expect(page.locator('input[placeholder="请输入密码"]')).toBeVisible()
    await expect(page.locator('input[placeholder="请确认密码"]')).toBeVisible()
    await expect(page.locator('button:has-text("注册")')).toBeVisible()

    await takeScreenshot(page, 'register-page-smoke')
  })

  test('仪表板页面访问测试', async ({ page }) => {
    // 测试未登录时访问dashboard会重定向到登录页
    await page.goto('/dashboard')
    await page.waitForURL(/\/login(\?redirect=.*)?/)
    await expect(page.locator('h2')).toContainText('登录')

    await takeScreenshot(page, 'dashboard-redirect-smoke')
  })

  test('设置页面访问测试', async ({ page }) => {
    // 测试未登录时访问settings会重定向到登录页
    await page.goto('/settings')
    await page.waitForURL(/\/login(\?redirect=.*)?/)
    await expect(page.locator('h2')).toContainText('登录')

    await takeScreenshot(page, 'settings-redirect-smoke')
  })

  test('登录表单交互测试', async ({ page }) => {
    await page.goto('/login')

    // 测试表单输入
    await page.fill('input[placeholder="请输入用户名"]', 'testuser')
    await expect(page.locator('input[placeholder="请输入用户名"]')).toHaveValue('testuser')

    await page.fill('input[placeholder="请输入密码"]', 'password123')
    await expect(page.locator('input[placeholder="请输入密码"]')).toHaveValue('password123')

    await takeScreenshot(page, 'login-form-interaction-smoke')

    // 测试清空表单
    await page.fill('input[placeholder="请输入用户名"]', '')
    await page.fill('input[placeholder="请输入密码"]', '')

    await expect(page.locator('input[placeholder="请输入用户名"]')).toHaveValue('')
    await expect(page.locator('input[placeholder="请输入密码"]')).toHaveValue('')
  })

  test('导航链接测试', async ({ page }) => {
    await page.goto('/login')

    // 测试注册链接
    const registerLink = page.locator('text=立即注册')
    await expect(registerLink).toBeVisible()
    await registerLink.click()
    await page.waitForURL('/register')
    await expect(page.locator('h2')).toContainText('注册')

    // 测试返回登录链接
    const loginLink = page.locator('text=立即登录')
    await expect(loginLink).toBeVisible()
    await loginLink.click()
    await page.waitForURL('/login')
    await expect(page.locator('h2')).toContainText('登录')

    await takeScreenshot(page, 'navigation-links-smoke')
  })

  test('响应式布局测试', async ({ page }) => {
    // 桌面端
    await page.setViewportSize({ width: 1280, height: 720 })
    await page.goto('/login')
    await expect(page.locator('h2')).toContainText('登录')
    await takeScreenshot(page, 'login-desktop-smoke')

    // 平板端
    await page.setViewportSize({ width: 768, height: 1024 })
    await page.goto('/login')
    await expect(page.locator('h2')).toContainText('登录')
    await takeScreenshot(page, 'login-tablet-smoke')

    // 移动端
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/login')
    await expect(page.locator('h2')).toContainText('登录')
    await takeScreenshot(page, 'login-mobile-smoke')
  })
})