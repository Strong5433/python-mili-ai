/**
 * 环境变量配置说明
 *
 * 在项目根目录创建 .env.local 或 .env.development 文件，并添加以下配置：
 *
 * # 应用部署域名
 * # 可选；不配置时默认使用 ${VITE_API_BASE_URL}/static
 * VITE_DEPLOY_DOMAIN=http://localhost:8123/api/static
 *
 * # API 基础地址
 * VITE_API_BASE_URL=http://localhost:8123/api
 *
 * 生产环境可以创建 .env.production 文件：
 *
 * # 生产环境配置示例
 * VITE_DEPLOY_DOMAIN=https://your-domain.com
 * VITE_API_BASE_URL=https://api.your-domain.com
 */

export {}
