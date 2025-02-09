/**
 * 格式化时间戳为可读字符串
 * @param timestamp ISO格式的时间字符串或时间戳
 * @returns 格式化后的时间字符串
 */
export const formatTime = (timestamp: string | number): string => {
  if (!timestamp) return '-'
  
  const date = new Date(timestamp)
  if (isNaN(date.getTime())) return '-'

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

/**
 * 计算相对时间
 * @param timestamp ISO格式的时间字符串或时间戳
 * @returns 相对时间字符串
 */
export const getRelativeTime = (timestamp: string | number): string => {
  if (!timestamp) return '-'
  
  const date = new Date(timestamp)
  if (isNaN(date.getTime())) return '-'

  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) {
    return `${days}天前`
  } else if (hours > 0) {
    return `${hours}小时前`
  } else if (minutes > 0) {
    return `${minutes}分钟前`
  } else {
    return '刚刚'
  }
}

/**
 * 格式化持续时间
 * @param seconds 秒数
 * @returns 格式化后的持续时间字符串
 */
export const formatDuration = (seconds: number): string => {
  if (!seconds || seconds < 0) return '0秒'

  const days = Math.floor(seconds / (24 * 60 * 60))
  const hours = Math.floor((seconds % (24 * 60 * 60)) / (60 * 60))
  const minutes = Math.floor((seconds % (60 * 60)) / 60)
  const remainingSeconds = Math.floor(seconds % 60)

  const parts = []
  if (days > 0) parts.push(`${days}天`)
  if (hours > 0) parts.push(`${hours}小时`)
  if (minutes > 0) parts.push(`${minutes}分钟`)
  if (remainingSeconds > 0) parts.push(`${remainingSeconds}秒`)

  return parts.join(' ')
}

/**
 * 格式化日期范围
 * @param startTime 开始时间
 * @param endTime 结束时间
 * @returns 格式化后的日期范围字符串
 */
export const formatDateRange = (startTime: string | number, endTime: string | number): string => {
  if (!startTime || !endTime) return '-'
  
  const start = new Date(startTime)
  const end = new Date(endTime)
  
  if (isNaN(start.getTime()) || isNaN(end.getTime())) return '-'

  return `${formatTime(startTime)} 至 ${formatTime(endTime)}`
} 