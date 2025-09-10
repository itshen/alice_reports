#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试用的报告配置，包含Webhook设置
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import ReportConfig

def create_test_report_config():
    """创建测试用的报告配置"""
    print("🔧 创建测试用报告配置...")
    
    with app.app_context():
        # 检查是否已存在深度研究配置
        existing_config = ReportConfig.query.filter_by(enable_deep_research=True).first()
        
        if existing_config:
            print(f"✅ 已存在深度研究配置: {existing_config.name}")
            print(f"   ID: {existing_config.id}")
            print(f"   Webhook URL: {'已配置' if existing_config.webhook_url else '未配置'}")
            
            # 询问是否要更新
            update = input("\n是否要更新配置？(y/n): ").lower().strip()
            if update == 'y':
                update_config(existing_config)
            else:
                print("保持现有配置不变")
            
            return existing_config
        else:
            # 创建新配置
            return create_new_config()

def create_new_config():
    """创建新的报告配置"""
    print("\n📋 创建新的深度研究配置...")
    
    # 收集配置信息
    name = input("报告名称 (默认: AI技术发展趋势深度研究): ").strip() or "AI技术发展趋势深度研究"
    
    print("\n📊 数据源配置:")
    print("请输入要使用的爬虫ID，用逗号分隔 (例如: 1,2,3)")
    data_sources = input("数据源 (默认: 1,2,3): ").strip() or "1,2,3"
    
    print("\n🔍 过滤配置:")
    filter_keywords = input("关键词 (默认: 人工智能,AI,机器学习,深度学习,大模型): ").strip() or "人工智能,AI,机器学习,深度学习,大模型"
    
    print("\n⏰ 时间范围:")
    print("可选: 24h, 3d, 7d, 30d")
    time_range = input("时间范围 (默认: 7d): ").strip() or "7d"
    
    print("\n🎯 研究配置:")
    purpose = input("研究目的 (默认: 深入研究AI技术发展趋势): ").strip() or "深入研究AI技术发展趋势"
    research_focus = input("研究重点 (默认: AI技术突破和创新): ").strip() or "AI技术突破和创新"
    
    print("\n📢 推送配置:")
    print("支持的推送类型: wechat (企业微信), jinshan (金山协作)")
    notification_type = input("推送类型 (默认: wechat): ").strip() or "wechat"
    
    print("\n🔗 Webhook配置:")
    print("请输入Webhook URL (如果不需要推送功能可留空):")
    webhook_url = input("Webhook URL: ").strip() or None
    
    try:
        with app.app_context():
            # 创建配置
            config = ReportConfig(
                name=name,
                data_sources=data_sources,
                filter_keywords=filter_keywords,
                time_range=time_range,
                purpose=purpose,
                research_focus=research_focus,
                enable_deep_research=True,
                notification_type=notification_type,
                webhook_url=webhook_url,
                is_active=True
            )
            
            db.session.add(config)
            db.session.commit()
            
            print(f"\n✅ 报告配置创建成功！")
            print(f"   配置ID: {config.id}")
            print(f"   配置名称: {config.name}")
            print(f"   推送状态: {'已配置' if webhook_url else '未配置'}")
            
            return config
            
    except Exception as e:
        print(f"❌ 创建配置失败: {e}")
        return None

def update_config(config):
    """更新现有配置"""
    print(f"\n📝 更新配置: {config.name}")
    
    # 只更新关键字段
    print("\n📢 推送配置更新:")
    current_type = config.notification_type or 'wechat'
    print(f"当前推送类型: {current_type}")
    notification_type = input(f"新推送类型 (回车保持 {current_type}): ").strip()
    if notification_type:
        config.notification_type = notification_type
    
    current_webhook = config.webhook_url or '未配置'
    print(f"当前Webhook URL: {current_webhook}")
    webhook_url = input("新Webhook URL (回车保持不变): ").strip()
    if webhook_url:
        config.webhook_url = webhook_url
    
    try:
        with app.app_context():
            db.session.commit()
            print(f"✅ 配置更新成功！")
            print(f"   推送类型: {config.notification_type}")
            print(f"   Webhook URL: {'已配置' if config.webhook_url else '未配置'}")
            
    except Exception as e:
        print(f"❌ 更新配置失败: {e}")

def test_webhook_config():
    """测试Webhook配置"""
    print("\n🧪 测试Webhook配置...")
    
    with app.app_context():
        configs = ReportConfig.query.filter_by(enable_deep_research=True).all()
        
        if not configs:
            print("❌ 未找到深度研究配置")
            return
        
        for config in configs:
            if config.webhook_url:
                print(f"\n测试配置: {config.name}")
                
                # 导入通知服务
                from services.notification_service import NotificationService
                notification_service = NotificationService()
                
                # 测试webhook
                result = notification_service.test_webhook(
                    config.notification_type, 
                    config.webhook_url
                )
                
                if result['success']:
                    print(f"✅ Webhook测试成功")
                else:
                    print(f"❌ Webhook测试失败: {result['message']}")
            else:
                print(f"⚠️ 配置 {config.name} 未设置Webhook URL")

def main():
    """主函数"""
    print("🚀 深度研究报告配置管理工具")
    print("="*50)
    
    while True:
        print("\n选择操作:")
        print("1. 创建/查看报告配置")
        print("2. 测试Webhook配置") 
        print("3. 退出")
        
        choice = input("\n请选择 (1-3): ").strip()
        
        if choice == '1':
            create_test_report_config()
        elif choice == '2':
            test_webhook_config()
        elif choice == '3':
            print("👋 再见！")
            break
        else:
            print("❌ 无效选择，请重试")

if __name__ == "__main__":
    main()
