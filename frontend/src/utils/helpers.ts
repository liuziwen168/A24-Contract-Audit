 /**
  * Generates a simple UUID v4-like string for idempotency keys
  */
 export function generateIdempotencyKey(): string {
   return 'req_' + Date.now().toString(36) + '_' + Math.random().toString(36).substring(2, 10)
 }

 /**
  * Formats a file size in bytes to a human-readable string
  */
 export function formatFileSize(bytes: number): string {
   if (bytes === 0) return '0 B'
   const k = 1024
   const sizes = ['B', 'KB', 'MB', 'GB']
   const i = Math.floor(Math.log(bytes) / Math.log(k))
   return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
 }

 /**
  * Returns the color for a risk level
  */
 export function getRiskColor(level: string): string {
   const map: Record<string, string> = { high: '#F56C6C', medium: '#E6A23C', low: '#909399' }
   return map[level] || '#909399'
 }

 /**
  * Gets the risk level label in Chinese
  */
 export function getRiskLevelLabel(level: string): string {
   const map: Record<string, string> = { high: '高风险', medium: '中风险', low: '低风险' }
   return map[level] || level
 }
