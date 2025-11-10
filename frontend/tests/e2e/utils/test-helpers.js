/**
 * 测试辅助工具函数
 */

// 生成随机用户名
export function generateRandomUsername(prefix = 'testuser') {
  const timestamp = Date.now()
  const random = Math.floor(Math.random() * 1000)
  return `${prefix}_${timestamp}_${random}`
}

// 生成随机邮箱
export function generateRandomEmail(prefix = 'test') {
  const timestamp = Date.now()
  const random = Math.floor(Math.random() * 1000)
  return `${prefix}_${timestamp}_${random}@example.com`
}

// 等待元素可见
export async function waitForElement(page, selector, timeout = 5000) {
  await page.waitForSelector(selector, { state: 'visible', timeout })
}

// 安全点击元素
export async function safeClick(page, selector) {
  await waitForElement(page, selector)
  await page.click(selector)
}

// 安全填写表单
export async function safeFill(page, selector, value) {
  await waitForElement(page, selector)
  await page.fill(selector, value)
}

// 等待网络请求完成
export async function waitForNetworkIdle(page, timeout = 5000) {
  await page.waitForLoadState('networkidle', { timeout })
}

// 获取测试用户数据
export function getTestUsers() {
  if (!process.env.TEST_USERS) {
    throw new Error('Test users not configured')
  }
  return JSON.parse(process.env.TEST_USERS)
}

// 创建测试用户令牌（模拟）
export function createTestToken(user) {
  return `mock-jwt-token-${user.username}-${Date.now()}`
}

// 验证API响应
export function validateApiResponse(response, expectedStatus = 200) {
  expect(response.status()).toBe(expectedStatus)
  return response.json()
}

// 检查控制台错误
export async function checkConsoleErrors(page) {
  const logs = []
  page.on('console', msg => {
    if (msg.type() === 'error') {
      logs.push(msg.text())
    }
  })
  return logs
}

// 模拟用户登录
export async function loginUser(page, user) {
  await page.goto('/login')

  await safeFill(page, 'input[placeholder="请输入用户名"]', user.username)
  await safeFill(page, 'input[placeholder="请输入密码"]', user.password)
  await safeClick(page, 'button:has-text("登录")')

  // 等待登录完成 - 检查是否跳转到dashboard或redirect URL
  await page.waitForURL(/dashboard|/)
}

// 模拟用户注册
export async function registerUser(page, user) {
  await page.goto('/register')

  await safeFill(page, 'input[placeholder="请输入用户名"]', user.username)
  await safeFill(page, 'input[placeholder="请输入邮箱"]', user.email)
  await safeFill(page, 'input[placeholder="请输入密码"]', user.password)
  await safeFill(page, 'input[placeholder="请确认密码"]', user.password)
  await safeClick(page, 'button:has-text("注册")')

  // 等待注册完成
  await page.waitForURL('/login')
}

// 截图对比
export async function takeScreenshot(page, name) {
  await page.screenshot({
    path: `test-results/screenshots/${name}.png`,
    fullPage: true
  })
}

// 响应式测试辅助
export const viewports = {
  desktop: { width: 1280, height: 720 },
  tablet: { width: 768, height: 1024 },
  mobile: { width: 375, height: 667 }
}

// 设置视口大小
export async function setViewport(page, device) {
  const viewport = viewports[device]
  if (viewport) {
    await page.setViewportSize(viewport)
  }
}