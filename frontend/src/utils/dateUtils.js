/**
 * 日期工具函数
 * 统一处理日期格式化和时区转换
 */

/**
 * 格式化日期为用户时区显示
 * @param {string|Date} dateString - 日期字符串或Date对象
 * @param {Object} options - 格式化选项
 * @param {string} userTimezone - 用户时区，默认为 'Asia/Shanghai'
 * @returns {string} 格式化后的日期字符串
 */
export const formatDate = (dateString, options = {}, userTimezone = 'Asia/Shanghai') => {
  if (!dateString) return '-'

  try {
    // 创建Date对象，JavaScript会自动处理ISO格式和时区
    const date = new Date(dateString);

    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      console.warn('无效的日期格式:', dateString);
      return '-';
    }

    // 默认格式化选项
    const defaultOptions = {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: userTimezone
    };

    // 合并用户选项
    const formatOptions = { ...defaultOptions, ...options };

    // 使用toLocaleString直接转换为用户时区，并格式化输出
    return date.toLocaleString('zh-CN', formatOptions);
  } catch (error) {
    console.error('日期格式化错误:', error, '原始值:', dateString);
    return '-';
  }
};

/**
 * 格式化日期为短格式（年月日）
 * @param {string|Date} dateString - 日期字符串或Date对象
 * @param {string} userTimezone - 用户时区，默认为 'Asia/Shanghai'
 * @returns {string} 格式化后的日期字符串
 */
export const formatDateShort = (dateString, userTimezone = 'Asia/Shanghai') => {
  return formatDate(dateString, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    timeZone: userTimezone
  }, userTimezone);
};

/**
 * 格式化时间（时分）
 * @param {string|Date} dateString - 日期字符串或Date对象
 * @param {string} userTimezone - 用户时区，默认为 'Asia/Shanghai'
 * @returns {string} 格式化后的时间字符串
 */
export const formatTime = (dateString, userTimezone = 'Asia/Shanghai') => {
  return formatDate(dateString, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: userTimezone
  }, userTimezone);
};

/**
 * 格式化为相对时间（如：2小时前）
 * @param {string|Date} dateString - 日期字符串或Date对象
 * @returns {string} 相对时间字符串
 */
export const formatRelativeTime = (dateString) => {
  if (!dateString) return '-'

  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '-';

    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) {
      return '刚刚';
    } else if (diffMins < 60) {
      return `${diffMins}分钟前`;
    } else if (diffHours < 24) {
      return `${diffHours}小时前`;
    } else if (diffDays < 7) {
      return `${diffDays}天前`;
    } else {
      // 超过7天显示完整日期
      return formatDateShort(dateString);
    }
  } catch (error) {
    console.error('相对时间格式化错误:', error, '原始值:', dateString);
    return '-';
  }
};

/**
 * 检查是否为今天
 * @param {string|Date} dateString - 日期字符串或Date对象
 * @returns {boolean} 是否为今天
 */
export const isToday = (dateString) => {
  if (!dateString) return false;

  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return false;

    const today = new Date();
    return date.toDateString() === today.toDateString();
  } catch (error) {
    console.error('日期检查错误:', error);
    return false;
  }
};

/**
 * 获取日期范围的描述
 * @param {string|Date} startDate - 开始日期
 * @param {string|Date} endDate - 结束日期
 * @returns {string} 日期范围描述
 */
export const formatDateRange = (startDate, endDate) => {
  if (!startDate) return '-';

  try {
    const start = new Date(startDate);
    const end = endDate ? new Date(endDate) : null;

    if (isNaN(start.getTime())) return '-';

    if (end && !isNaN(end.getTime())) {
      // 有结束日期
      if (isToday(start) && isToday(end)) {
        return `今天 ${formatTime(start)} - ${formatTime(end)}`;
      } else {
        return `${formatDate(start)} - ${formatDate(end)}`;
      }
    } else {
      // 只有开始日期
      return formatDate(start);
    }
  } catch (error) {
    console.error('日期范围格式化错误:', error);
    return '-';
  }
};

/**
 * 根据用户数据获取用户时区
 * @param {Object} user - 用户对象，包含timezone字段
 * @returns {string} 用户时区
 */
export const getUserTimezone = (user) => {
  if (!user || !user.timezone) {
    return 'Asia/Shanghai'; // 默认时区
  }
  return user.timezone;
};

/**
 * 创建格式化函数，绑定用户时区
 * @param {Object} user - 用户对象
 * @returns {Object} 绑定用户时区的格式化函数集合
 */
export const createDateFormatters = (user) => {
  const userTimezone = getUserTimezone(user);

  return {
    formatDate: (dateString, options = {}) => formatDate(dateString, options, userTimezone),
    formatDateShort: (dateString) => formatDateShort(dateString, userTimezone),
    formatTime: (dateString) => formatTime(dateString, userTimezone),
    formatRelativeTime: (dateString) => formatRelativeTime(dateString),
    formatDateRange: (startDate, endDate) => formatDateRange(startDate, endDate, userTimezone),
    isToday: (dateString) => isToday(dateString),
    userTimezone
  };
};

// 默认导出主函数
export default formatDate;