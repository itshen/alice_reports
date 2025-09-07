#!/bin/bash
# 智能信息分析与报告自动化平台 - 快速安装脚本

echo "🚀 智能信息分析与报告自动化平台 - 安装脚本"
echo "=================================================="

# 检查Python版本
echo "📋 检查Python环境..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python版本检查通过: $python_version"
else
    echo "❌ 需要Python 3.8或更高版本，当前版本: $python_version"
    exit 1
fi

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3未找到，请先安装pip"
    exit 1
fi

echo "✅ pip检查通过"

# 创建虚拟环境（可选）
read -p "🤔 是否创建Python虚拟环境？(y/N): " create_venv
if [[ $create_venv =~ ^[Yy]$ ]]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ 虚拟环境已创建并激活"
fi

# 安装Python依赖
echo "📦 安装Python依赖包..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Python依赖安装完成"
else
    echo "❌ Python依赖安装失败"
    exit 1
fi

# 安装Crawl4AI
echo "🕷️ 安装Crawl4AI..."
pip3 install -U crawl4ai

# 运行Crawl4AI设置
echo "⚙️ 配置Crawl4AI..."
crawl4ai-setup

# 验证Crawl4AI安装
echo "🔍 验证Crawl4AI安装..."
crawl4ai-doctor

# 手动安装浏览器（如果需要）
echo "🌐 安装浏览器支持..."
python3 -m playwright install --with-deps chromium

# 运行系统测试
echo "🧪 运行系统测试..."
python3 test_system.py

if [ $? -eq 0 ]; then
    echo "✅ 系统测试通过"
else
    echo "⚠️ 系统测试有警告，但可以继续使用"
fi

# 显示启动信息
echo ""
echo "🎉 安装完成！"
echo "=================================================="
echo "📋 接下来的步骤："
echo ""
echo "1. 启动系统："
echo "   python3 run.py"
echo ""
echo "2. 打开浏览器访问："
echo "   http://localhost:5000"
echo ""
echo "3. 使用默认账户登录："
echo "   用户名: admin"
echo "   密码: admin123"
echo ""
echo "4. 在全局设置中配置LLM API密钥"
echo ""
echo "📖 详细使用说明请查看 README.md"
echo ""

# 询问是否立即启动
read -p "🚀 是否立即启动系统？(y/N): " start_now
if [[ $start_now =~ ^[Yy]$ ]]; then
    echo "🚀 启动系统..."
    python3 run.py
fi
