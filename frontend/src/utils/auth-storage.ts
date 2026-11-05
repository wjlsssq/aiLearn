// 登录凭据只在当前标签页的会话存储中保存。
const TOKEN_KEY = 'shopmind-token' // 使用统一键，避免 API 和 UI 各自定义。
export const readToken = () => sessionStorage.getItem(TOKEN_KEY) || '' // 读取当前登录状态。
export const saveToken = (token: string) => sessionStorage.setItem(TOKEN_KEY, token) // 登录成功后保存。
export const clearToken = () => sessionStorage.removeItem(TOKEN_KEY) // 退出或过期后删除。
