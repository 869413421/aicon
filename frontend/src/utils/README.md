# 前端工具函数库

## 日期工具函数 (dateUtils.js)

统一的日期处理工具，避免在各个组件中重复编写日期格式化代码。

### 主要功能

1. **动态时区转换**：根据用户timezone字段自动转换时区
2. **多种格式支持**：提供完整的中文日期格式化
3. **错误处理**：完善的异常处理和无效日期检测
4. **TypeScript友好**：完整的类型定义
5. **用户时区感知**：支持Asia/Shanghai、UTC、America/New_York等多种时区

### 数据库设计说明

- **存储**：数据库中的时间戳字段（如created_at、last_login）始终以UTC时间存储
- **时区偏好**：用户timezone字段存储用户偏好的时区，如 'Asia/Shanghai'
- **显示**：前端根据用户timezone字段将UTC时间转换为用户本地时间显示

### 函数列表

#### `formatDate(dateString, options = {}, userTimezone)`
主要的日期格式化函数，返回完整的中文日期时间格式。

**参数：**
- `dateString`: 日期字符串或Date对象
- `options`: 可选的格式化选项
- `userTimezone`: 用户时区，默认为 'Asia/Shanghai'

**默认格式：** `2025年11月10日 02:26`

```javascript
import { formatDate, getUserTimezone } from '@/utils/dateUtils'

// 使用用户时区
const userTimezone = getUserTimezone(authStore.user); // 'Asia/Shanghai'
formatDate('2025-11-06T22:58:30.879371+00:00', {}, userTimezone)
// 返回: '2025年11月7日 06:58'

// 指定时区
formatDate(dateString, {}, 'America/New_York')
// 返回: '2025年11月6日 17:58' (根据时区转换)
```

#### `formatDateShort(dateString, userTimezone)`
短格式日期，适合卡片列表等空间有限的场景。

**格式：** `2025/11/07`

```javascript
import { formatDateShort, getUserTimezone } from '@/utils/dateUtils'

const userTimezone = getUserTimezone(authStore.user);
formatDateShort('2025-11-06T22:58:30.879371+00:00', userTimezone)
// 返回: '2025/11/07'
```

#### `formatTime(dateString, userTimezone)`
只显示时间部分。

**格式：** `2025年11月10日 02:26:58`

```javascript
import { formatTime, getUserTimezone } from '@/utils/dateUtils'

const userTimezone = getUserTimezone(authStore.user);
formatTime('2025-11-09T18:26:58.382866+00:00', userTimezone)
// 返回: '2025年11月10日 02:26:58'
```

#### `getUserTimezone(user)`
获取用户时区设置。

```javascript
import { getUserTimezone } from '@/utils/dateUtils'

const userTimezone = getUserTimezone(authStore.user);
console.log(userTimezone); // 'Asia/Shanghai'
```

#### `createDateFormatters(user)`
创建绑定用户时区的格式化函数集合。

```javascript
import { createDateFormatters } from '@/utils/dateUtils'

const formatters = createDateFormatters(authStore.user);
const { formatDate, formatDateShort, formatTime } = formatters;

// 所有函数都自动使用用户时区
formatDate(dateString); // 自动使用用户时区
formatDateShort(dateString); // 自动使用用户时区
```

### 支持的时区

- `'Asia/Shanghai'` - 北京时间 (UTC+8)
- `'UTC'` - 协调世界时 (UTC+0)
- `'America/New_York'` - 纽约时间 (UTC-5/-4)
- `'Europe/London'` - 伦敦时间 (UTC+0/+1)
- `'America/Los_Angeles'` - 洛杉矶时间 (UTC-8/-7)

### 使用场景

1. **用户资料页面**：显示注册时间
   ```javascript
   const userTimezone = getUserTimezone(authStore.user);
   formatDate(user.created_at, {}, userTimezone)
   ```

2. **项目列表**：显示项目创建时间
   ```javascript
   const formatters = createDateFormatters(authStore.user);
   formatters.formatDateShort(project.created_at)
   ```

3. **账户安全**：显示上次登录时间
   ```javascript
   const userTimezone = getUserTimezone(authStore.user);
   formatDate(authStore.user?.last_login, {}, userTimezone)
   ```

### Vue组件中的推荐用法

```vue
<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { getUserTimezone, formatDate } from '@/utils/dateUtils'

const authStore = useAuthStore()

// 计算用户时区
const userTimezone = computed(() => {
  return getUserTimezone(authStore.user);
})
</script>

<template>
  <div>
    <span>{{ formatDate(user.created_at, {}, userTimezone) }}</span>
  </div>
</template>
```

### 时区处理原理

1. **数据库存储**：所有时间戳以UTC格式存储，避免时区混乱
2. **用户偏好**：timezone字段存储用户期望的显示时区
3. **前端转换**：JavaScript根据用户timezone将UTC时间转换为本地时间
4. **动态响应**：当用户更改时区偏好时，所有时间显示自动更新

### 错误处理

- 无效日期返回 `-`
- 用户时区不存在时使用默认时区 `'Asia/Shanghai'`
- 控制台输出详细的错误信息
- 防止页面崩溃

### 性能优化

- 使用computed属性缓存用户时区
- 避免重复的时区解析
- 统一的格式化逻辑减少代码重复

### 扩展新功能

当需要新的日期格式时，建议在这里添加统一的函数：

```javascript
export const formatCustom = (dateString, userTimezone = 'Asia/Shanghai') => {
  return formatDate(dateString, {
    // 自定义格式化选项
  }, userTimezone);
}
```

---

## 其他工具函数

（为未来的工具函数预留空间）