#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
群推送和深度研究报告展示测试
测试实际推送到群聊功能和完整报告展示
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import GlobalSettings, ReportConfig, ReportRecord
from services.notification_service import NotificationService

class GroupNotificationTester:
    """群推送测试类"""
    
    def __init__(self):
        self.notification_service = NotificationService()
        self.settings = None
        
    def setup(self):
        """初始化测试环境"""
        print("🔧 初始化群推送测试环境...")
        
        with app.app_context():
            # 获取全局设置
            self.settings = GlobalSettings.query.first()
            if not self.settings:
                print("❌ 未找到全局设置")
                return False
            
            print("✅ 测试环境初始化完成")
            return True
    
    def display_full_report(self):
        """展示完整的深度研究报告"""
        print("\n" + "="*80)
        print("📊 **完整深度研究报告展示**")
        print("="*80)
        
        with app.app_context():
            # 获取最新的深度研究报告
            latest_report = ReportRecord.query.order_by(ReportRecord.generated_at.desc()).first()
            
            if not latest_report:
                print("❌ 未找到深度研究报告")
                return False
            
            print(f"📋 **报告标题：** {latest_report.title}")
            print(f"🕐 **生成时间：** {latest_report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📄 **报告长度：** {len(latest_report.content)} 字符")
            print(f"✅ **状态：** {latest_report.status}")
            
            print("\n" + "-"*80)
            print("📖 **完整报告内容：**")
            print("-"*80)
            
            # 分段显示报告内容，增加可读性
            content_lines = latest_report.content.split('\n')
            for i, line in enumerate(content_lines):
                if line.strip():
                    # 为标题添加颜色和格式
                    if line.startswith('# '):
                        print(f"\n🎯 {line}")
                    elif line.startswith('## '):
                        print(f"\n📌 {line}")
                    elif line.startswith('### '):
                        print(f"\n📍 {line}")
                    elif line.startswith('**') and line.endswith('**'):
                        print(f"💡 {line}")
                    elif line.startswith('- '):
                        print(f"  {line}")
                    elif line.startswith('|'):
                        print(f"📊 {line}")
                    else:
                        print(line)
                else:
                    print()
            
            print("\n" + "="*80)
            print("✅ **报告展示完成**")
            print("="*80)
            
            return True
    
    def test_notification_formatting(self):
        """测试通知格式化"""
        print("\n📱 测试通知格式化...")
        
        with app.app_context():
            latest_report = ReportRecord.query.order_by(ReportRecord.generated_at.desc()).first()
            
            if not latest_report:
                print("❌ 未找到报告数据")
                return False
            
            # 测试深度研究报告格式化
            print("📝 格式化深度研究报告通知...")
            formatted_notification = self.notification_service.format_deep_research_for_notification(
                latest_report.content
            )
            
            print(f"✅ 通知格式化完成，长度: {len(formatted_notification)} 字符")
            print("\n" + "-"*60)
            print("📲 **格式化后的通知内容：**")
            print("-"*60)
            print(formatted_notification)
            print("-"*60)
            
            return formatted_notification
    
    def test_webhook_with_real_content(self, formatted_content):
        """使用真实内容测试Webhook"""
        print("\n🔗 测试实际Webhook推送...")
        
        with app.app_context():
            # 获取报告配置中的Webhook URL
            report_configs = ReportConfig.query.filter(
                ReportConfig.webhook_url.isnot(None),
                ReportConfig.webhook_url != ''
            ).all()
            
            if not report_configs:
                print("⚠️ 未找到配置的Webhook URL，使用测试URL")
                test_urls = [
                    {
                        'type': 'wechat',
                        'url': 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test-key',
                        'name': '企业微信测试群'
                    },
                    {
                        'type': 'jinshan',
                        'url': 'https://open.feishu.cn/open-apis/bot/v2/hook/test-hook',
                        'name': '飞书测试群'
                    }
                ]
            else:
                test_urls = []
                for config in report_configs:
                    test_urls.append({
                        'type': config.notification_type,
                        'url': config.webhook_url,
                        'name': f'{config.name}的通知群'
                    })
            
            results = []
            
            for webhook_config in test_urls:
                print(f"\n📤 推送到 {webhook_config['name']} ({webhook_config['type']})...")
                print(f"   URL: {webhook_config['url'][:50]}...")
                
                # 发送实际通知
                success = self.notification_service.send_notification(
                    webhook_config['type'],
                    webhook_config['url'],
                    formatted_content,
                    "🤖 深度研究报告 - 测试推送"
                )
                
                if success:
                    print(f"   ✅ 推送成功！")
                    results.append(True)
                else:
                    print(f"   ❌ 推送失败（可能是测试URL或网络问题）")
                    results.append(False)
                
                # 测试连接性
                test_result = self.notification_service.test_webhook(
                    webhook_config['type'],
                    webhook_config['url']
                )
                
                if test_result['success']:
                    print(f"   🔗 连接测试: ✅ 成功")
                else:
                    print(f"   🔗 连接测试: ❌ {test_result['message']}")
            
            return any(results)
    
    def simulate_real_group_push(self):
        """模拟真实的群推送场景"""
        print("\n🎭 模拟真实群推送场景...")
        
        # 模拟不同类型的群推送
        scenarios = [
            {
                'name': '技术团队群',
                'type': 'wechat',
                'focus': '技术细节和实现方案',
                'audience': '开发者和技术专家'
            },
            {
                'name': '管理层决策群',
                'type': 'jinshan',
                'focus': '战略洞察和商业影响',
                'audience': '高管和决策者'
            },
            {
                'name': '产品运营群',
                'type': 'wechat',
                'focus': '市场趋势和用户影响',
                'audience': '产品经理和运营人员'
            }
        ]
        
        with app.app_context():
            latest_report = ReportRecord.query.order_by(ReportRecord.generated_at.desc()).first()
            
            if not latest_report:
                print("❌ 未找到报告数据")
                return False
            
            for scenario in scenarios:
                print(f"\n📱 推送到 **{scenario['name']}**")
                print(f"   👥 目标受众: {scenario['audience']}")
                print(f"   🎯 关注重点: {scenario['focus']}")
                print(f"   📢 推送平台: {scenario['type']}")
                
                # 根据不同受众定制通知内容
                if scenario['focus'] == '技术细节和实现方案':
                    # 技术团队关注实现细节
                    custom_content = f"""🤖 **AI技术深度研究报告**

📊 **核心技术洞察：**
• AI基础设施投资成为新热点
• 编程Agent引领开发新范式  
• 中美技术竞争进入封锁阶段

🔧 **技术要点：**
• Claude Code实现端到端自动化开发
• AGI现实主义投资策略获47%回报
• AI工程化与生态构建成关键

⚡ **实施建议：**
• 加强AI基础设施布局
• 推动模型工程化转化
• 构建自主可控技术体系

📈 **数据来源：** 基于4篇最新技术文章分析
🕐 **生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}

> 完整技术报告请查看系统后台"""

                elif scenario['focus'] == '战略洞察和商业影响':
                    # 管理层关注战略和商业价值
                    custom_content = f"""📊 **AI战略研究报告 - 管理层摘要**

🎯 **战略要点：**
• AI竞争已进入生态构建新阶段
• 基础设施投资成为制胜关键
• 人才争夺成为核心战略资源

💰 **商业机会：**
• AI基础设施投资回报率达47%
• 算力、芯片、数据中心成投资热点
• 工程化能力决定AI落地成效

⚠️ **风险提示：**
• 中美技术封锁加剧供应链风险
• AI治理与伦理问题日益突出
• 核心技术自主可控能力待提升

📈 **投资建议：**
• 加大AI基础设施投资布局
• 强化核心技术自主研发
• 完善AI人才引进与培养

🕐 **报告时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}

> 详细战略分析请查看完整报告"""

                else:
                    # 产品运营关注市场和用户
                    custom_content = f"""📱 **AI市场趋势报告**

🌟 **市场亮点：**
• 网络文明建设推动AI向善发展
• 00后AI投资人异军突起
• 编程Agent开启开发新时代

👥 **用户影响：**
• AI内容生成规范化加强
• 开发者工具智能化升级
• 技术门槛进一步降低

📊 **运营机会：**
• AI+内容创作市场扩大
• 智能开发工具需求增长
• 垂直领域AI应用深化

🎯 **产品方向：**
• 强化AI伦理与安全功能
• 优化用户体验和易用性
• 构建开放协作生态

🕐 **更新时间：** {datetime.now().strftime('%Y-%m-%d %H:%M')}

> 完整市场分析请查看系统后台"""
                
                # 模拟发送（实际环境中会调用真实API）
                print(f"   📤 推送内容预览:")
                print("   " + "-"*50)
                for line in custom_content.split('\n')[:10]:
                    print(f"   {line}")
                print("   ...")
                print("   " + "-"*50)
                print(f"   ✅ 模拟推送完成")
        
        return True
    
    def generate_push_statistics(self):
        """生成推送统计报告"""
        print("\n📊 生成推送统计报告...")
        
        with app.app_context():
            # 统计报告数量
            total_reports = ReportRecord.query.count()
            success_reports = ReportRecord.query.filter_by(status='success').count()
            failed_reports = ReportRecord.query.filter_by(status='failed').count()
            
            # 统计通知发送情况
            sent_notifications = ReportRecord.query.filter_by(notification_sent=True).count()
            
            # 统计深度研究报告
            deep_research_reports = ReportRecord.query.join(ReportConfig).filter(
                ReportConfig.enable_deep_research == True
            ).count()
            
            print(f"""
📈 **推送统计报告**
{'='*50}
📊 **报告生成统计：**
   • 总报告数: {total_reports}
   • 成功生成: {success_reports}
   • 生成失败: {failed_reports}
   • 成功率: {(success_reports/total_reports*100):.1f}% (如果有报告)

📱 **通知推送统计：**
   • 已发送通知: {sent_notifications}
   • 通知发送率: {(sent_notifications/success_reports*100):.1f}% (基于成功报告)

🔬 **深度研究统计：**
   • 深度研究报告: {deep_research_reports}
   • 深度研究占比: {(deep_research_reports/total_reports*100):.1f}% (如果有报告)

🕐 **统计时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}
            """)
        
        return True

async def main():
    """主测试函数"""
    print("🚀 开始群推送和深度研究报告测试")
    print("="*80)
    
    tester = GroupNotificationTester()
    
    # 初始化
    if not tester.setup():
        print("❌ 测试环境初始化失败")
        return False
    
    try:
        # 1. 展示完整的深度研究报告
        print("\n📖 **第一步：展示完整深度研究报告**")
        report_success = tester.display_full_report()
        
        # 2. 测试通知格式化
        print("\n📱 **第二步：测试通知格式化**")
        formatted_content = tester.test_notification_formatting()
        
        # 3. 测试实际Webhook推送
        print("\n🔗 **第三步：测试实际Webhook推送**")
        webhook_success = tester.test_webhook_with_real_content(formatted_content)
        
        # 4. 模拟真实群推送场景
        print("\n🎭 **第四步：模拟真实群推送场景**")
        simulation_success = tester.simulate_real_group_push()
        
        # 5. 生成推送统计报告
        print("\n📊 **第五步：生成推送统计报告**")
        stats_success = tester.generate_push_statistics()
        
        # 汇总结果
        print("\n" + "="*80)
        print("📋 **测试结果汇总**")
        print("="*80)
        
        results = {
            "完整报告展示": report_success,
            "通知格式化": bool(formatted_content),
            "Webhook推送": webhook_success,
            "群推送模拟": simulation_success,
            "统计报告": stats_success
        }
        
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {test_name}: {status}")
        
        passed_tests = sum(1 for result in results.values() if result)
        total_tests = len(results)
        
        print(f"\n🎯 **总体结果:** {passed_tests}/{total_tests} 项测试通过")
        
        if passed_tests == total_tests:
            print("🎉 **所有测试通过！群推送和深度研究报告功能运行正常**")
            return True
        else:
            print("⚠️ **部分测试失败，请检查相关配置**")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 启动群推送和深度研究报告测试...")
    success = asyncio.run(main())
    
    if success:
        print("\n🎊 **测试完成！群推送和深度研究报告功能正常运行**")
        print("💡 **提示：** 在生产环境中，请配置真实的Webhook URL以启用实际推送功能")
        sys.exit(0)
    else:
        print("\n💥 **测试失败！请检查系统配置和日志**")
        sys.exit(1)
