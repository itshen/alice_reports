#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能信息分析与报告自动化平台启动脚本
"""

import os
import sys
from app import app, db, scheduler, create_tables

def setup_database():
    """设置数据库"""
    with app.app_context():
        # 调用创建表函数
        create_tables()
        
        print("✅ 数据库初始化完成")

def start_scheduler():
    """启动调度器"""
    try:
        if not scheduler.running:
            scheduler.start()
            print("✅ 任务调度器启动成功")
        else:
            print("ℹ️  任务调度器已在运行")
    except Exception as e:
        print(f"❌ 启动调度器失败: {e}")

def main():
    """主函数"""
    print("🚀 启动智能信息分析与报告自动化平台...")
    print("=" * 60)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        sys.exit(1)
    
    # 设置数据库
    setup_database()
    
    # 启动调度器
    start_scheduler()
    
    # 显示启动信息
    print("\n📋 系统信息:")
    print(f"   Python版本: {sys.version}")
    print(f"   工作目录: {os.getcwd()}")
    print(f"   数据库文件: {os.path.join(os.getcwd(), 'app.db')}")
    
    print("\n🌐 访问地址:")
    print("   本地访问: http://localhost:8866")
    print("   局域网访问: http://0.0.0.0:8866")
    
    print("\n👤 默认账户:")
    print("   用户名: admin")
    print("   密码: admin123")
    
    print("\n" + "=" * 60)
    print("🎉 系统启动完成！按 Ctrl+C 停止服务")
    
    try:
        # 启动Flask应用
        app.run(
            host='0.0.0.0',
            port=8866,
            debug=False,  # 生产环境建议关闭debug
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n🛑 正在停止服务...")
        if scheduler.running:
            scheduler.shutdown()
            print("✅ 任务调度器已停止")
        print("👋 服务已停止，再见！")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
