# 智能信息分析与报告自动化平台

一个轻量级的、面向个人的信息自动化工具。它能帮助用户自动监控指定网站，根据关键词筛选信息，并能利用大语言模型（LLM）进行深入研究，最终生成定制化的分析报告，推送到企业微信或金山协作等办公软件中。

## ✨ 核心功能

### 🕷️ 智能爬虫系统
- **网站监控**: 自动监控指定网站的信息更新
- **内容提取**: 基于Crawl4AI的智能内容提取
- **正则匹配**: 支持AI辅助生成URL匹配规则
- **定时执行**: 可配置的定时抓取任务

### 📊 智能分析报告
- **简单报告**: 新闻摘要和信息汇总
- **深度研究**: 基于LLM的深度分析和研究
- **关键词过滤**: 根据关键词智能筛选相关内容
- **自定义模板**: 可配置的报告格式和侧重点

### 📱 多平台推送
- **企业微信**: 支持企业微信机器人推送
- **金山协作**: 支持金山协作平台通知
- **实时推送**: 报告生成后自动推送到指定平台

## 🛠️ 技术架构

- **后端框架**: Flask
- **前端技术**: HTML + Tailwind CSS + Alpine.js
- **数据库**: SQLite (轻量级，无需独立安装)
- **任务调度**: APScheduler
- **爬虫引擎**: Crawl4AI
- **LLM集成**: 支持通义千问、OpenRouter等多种服务商

## 🚀 快速开始

### 环境要求

- Python 3.8+
- macOS/Linux/Windows

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <项目地址>
   cd 智能信息分析平台
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **安装Crawl4AI**
   ```bash
   # 安装Crawl4AI
   pip install -U crawl4ai
   
   # 运行安装后设置
   crawl4ai-setup
   
   # 验证安装
   crawl4ai-doctor
   ```

4. **启动应用**
   ```bash
   python3.11 run.py
   ```

5. **访问系统**
   - 打开浏览器访问: http://localhost:5000
   - 默认账户: admin / admin123

## 📖 使用指南

### 1. 全局设置

首次使用需要配置：
- **SERP API密钥**: 用于网络搜索功能（可选）
- **LLM配置**: 
  - 服务商选择（通义千问、OpenRouter等）
  - API密钥和模型名称
  - Base URL配置

### 2. 创建爬虫配置

1. 进入"爬虫配置"页面
2. 点击"新建爬虫"
3. 填写基本信息：
   - 爬虫名称
   - 监控网站URL
   - 执行频率
4. 测试连接并配置URL提取规则：
   - 点击"测试连接"获取页面内容
   - 手动输入正则表达式或使用"AI推测正则"
   - 预览匹配的URL列表
5. 保存配置

### 3. 创建报告配置

1. 进入"报告配置"页面
2. 点击"新建报告"
3. 配置报告参数：
   - 报告名称和目的
   - 选择数据源（已创建的爬虫）
   - 设置过滤关键词
   - 选择时间范围
4. 智能分析设置：
   - 是否开启深度研究
   - 配置研究侧重点
5. 推送配置：
   - 选择机器人类型
   - 配置Webhook URL
   - 测试推送功能
6. 保存配置

### 4. 使用场景示例

#### 场景A：行业新闻日报
```
1. 创建爬虫监控科技新闻网站
2. 设置关键词："人工智能,大模型,AGI"
3. 不开启深度研究
4. 配置企业微信推送
5. 每日自动推送新闻摘要
```

#### 场景B：深度研究报告
```
1. 创建多个爬虫监控相关网站
2. 开启深度研究功能
3. 设置研究侧重点：
   "请深入研究XX技术的发展趋势、
   市场竞争格局、技术优势对比等"
4. 生成综合分析报告
```

## 🔧 配置说明

### LLM服务商配置

#### 通义千问
```
服务商: qwen
Base URL: https://dashscope.aliyuncs.com/compatible-mode/v1
模型名称: qwen-plus
API Key: 您的API密钥
```

#### OpenRouter
```
服务商: openrouter
Base URL: https://openrouter.ai/api/v1
模型名称: anthropic/claude-3-sonnet
API Key: 您的API密钥
```

### Webhook配置

#### 企业微信机器人
1. 在企业微信群中添加机器人
2. 获取Webhook URL
3. 在系统中配置URL并测试

#### 金山协作
1. 在金山协作中创建机器人
2. 获取Webhook URL
3. 在系统中配置URL并测试

## 📁 项目结构

```
智能信息分析平台/
├── app.py                 # Flask主应用
├── run.py                 # 启动脚本
├── models.py              # 数据库模型
├── requirements.txt       # 依赖包
├── services/              # 服务层
│   ├── crawler_service.py # 爬虫服务
│   ├── llm_service.py     # LLM服务
│   └── notification_service.py # 通知服务
├── templates/             # HTML模板
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   └── ...
├── static/                # 静态文件
│   ├── css/
│   └── js/
└── README.md
```

## 🔍 故障排除

### 常见问题

1. **Crawl4AI安装失败**
   ```bash
   # 手动安装浏览器
   python -m playwright install --with-deps chromium
   ```

2. **数据库错误**
   ```bash
   # 删除数据库文件重新初始化
   rm app.db
   python3.11 run.py
   ```

3. **LLM调用失败**
   - 检查API密钥是否正确
   - 确认网络连接正常
   - 验证Base URL配置

4. **爬虫无法访问网站**
   - 检查目标网站是否可访问
   - 确认网络防火墙设置
   - 尝试更换User-Agent

## 📝 开发说明

### 添加新的LLM服务商

1. 在`services/llm_service.py`中添加新的服务商支持
2. 更新前端配置选项
3. 测试API调用功能

### 添加新的通知平台

1. 在`services/notification_service.py`中实现新平台
2. 更新前端配置界面
3. 添加测试功能

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📞 支持

如有问题，请通过以下方式联系：
- 提交Issue
- 发送邮件

---

**注意**: 本系统仅供学习和个人使用，请遵守相关网站的robots.txt协议和使用条款。
