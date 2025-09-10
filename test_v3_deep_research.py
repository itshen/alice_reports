#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V3.0 XML交互版深度研究测试用例
测试迭代式AI研究流程
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import GlobalSettings, ReportConfig, CrawlerConfig
from services.crawler_service import CrawlerService
from services.llm_service import LLMService
from services.deep_research_service import DeepResearchService

class V3DeepResearchTester:
    """V3.0 XML交互版深度研究测试类"""
    
    def __init__(self):
        self.crawler_service = CrawlerService()
        self.llm_service = LLMService()
        self.deep_research_service = None
        self.settings = None
        
    def setup(self):
        """初始化测试环境"""
        print("🔧 初始化V3.0深度研究测试环境...")
        
        with app.app_context():
            # 获取全局设置
            self.settings = GlobalSettings.query.first()
            if not self.settings:
                print("❌ 未找到全局设置")
                return False
            
            # 检查API Key配置
            if not self.settings.llm_api_key:
                print("❌ LLM API Key未配置")
                return False
            
            if not self.settings.serp_api_key:
                print("⚠️ SERP API Key未配置，将跳过搜索功能")
            
            # 更新LLM服务设置
            self.llm_service.update_settings(self.settings)
            
            # 创建深度研究服务
            self.deep_research_service = DeepResearchService(
                self.crawler_service, 
                self.llm_service
            )
            
            print(f"✅ 测试环境初始化完成")
            print(f"   LLM Provider: {self.settings.llm_provider}")
            print(f"   LLM Model: {self.settings.llm_model_name}")
            print(f"   LLM API Key: {'已配置' if self.settings.llm_api_key else '未配置'}")
            print(f"   SERP API Key: {'已配置' if self.settings.serp_api_key else '未配置'}")
            
            return True
    
    def create_test_report_config(self):
        """创建测试用的报告配置"""
        print("\n📋 创建测试报告配置...")
        
        with app.app_context():
            # 查找数据库中的报告配置，或创建测试配置
            from models import ReportConfig
            
            # 强制使用可控生图测试配置进行测试
            print("🎯 创建可控生图专项测试配置")
            
            # 首先尝试从数据库获取webhook配置
            existing_config = ReportConfig.query.filter_by(enable_deep_research=True).first()
            webhook_url = existing_config.webhook_url if existing_config else None
            notification_type = existing_config.notification_type if existing_config else 'wechat'
            
            # 创建可控生图专项测试配置
            test_config = type('TestReportConfig', (), {
                'id': 999,  # 测试用ID
                'name': '可控生图技术深度研究',
                'data_sources': '1,2,3',  # 使用前3个爬虫作为数据源
                'filter_keywords': '可控生图,Nano Banana,即梦,图像生成,AI绘画,文生图,图像编辑',
                'time_range': '7d',
                'purpose': '深入研究最近一周可控生图技术的最新进展和突破',
                'research_focus': '重点关注：1) Nano Banana技术特点和应用场景；2) 即梦4.0的技术创新和性能提升；3) 这些模型的实际测评效果和用户反馈；4) 可控生图技术的发展趋势和市场前景分析',
                'enable_deep_research': True,
                'notification_type': notification_type,
                'webhook_url': webhook_url  # 从数据库配置继承webhook设置
            })()
            
            print(f"✅ 测试配置创建完成:")
            print(f"   报告名称: {test_config.name}")
            print(f"   数据源: {test_config.data_sources}")
            print(f"   关键词: {test_config.filter_keywords}")
            print(f"   时间范围: {test_config.time_range}")
            print(f"   研究目的: {test_config.purpose}")
            print(f"   研究重点: {test_config.research_focus}")
            
            return test_config
    
    async def test_initial_knowledge_base(self, report_config):
        """测试初始知识库构建"""
        print("\n📚 测试初始知识库构建...")
        
        try:
            with app.app_context():
                knowledge_base = await self.deep_research_service._build_initial_knowledge_base(report_config)
            
            print(f"✅ 初始知识库构建完成")
            print(f"   文章数量: {len(knowledge_base)}")
            
            if knowledge_base:
                print(f"   示例文章:")
                for i, article in enumerate(knowledge_base[:3], 1):
                    print(f"     {i}. {article.get('title', '无标题')[:50]}...")
                    print(f"        来源: {article.get('source', '未知')}")
                    print(f"        URL: {article.get('url', 'N/A')}")
            
            return True, knowledge_base
            
        except Exception as e:
            print(f"❌ 初始知识库构建失败: {e}")
            return False, []
    
    async def test_ai_initial_analysis(self, knowledge_base, report_config):
        """测试AI初步分析功能"""
        print("\n🧠 测试AI初步分析功能...")
        
        try:
            with app.app_context():
                # 测试AI初步分析
                analysis_result = await self.deep_research_service._ai_initial_analysis(
                    knowledge_base, 
                    report_config
                )
            
            print(f"✅ AI初步分析测试完成")
            print(f"   现有知识摘要: {analysis_result.get('summary', '无')[:100]}...")
            print(f"   知识空白: {analysis_result.get('gaps', '无')[:100]}...")
            print(f"   研究方向数: {len(analysis_result.get('directions', []))}")
            print(f"   优先关键词: {', '.join(analysis_result.get('keywords', [])[:3])}")
            
            return True, analysis_result
            
        except Exception as e:
            print(f"❌ AI初步分析失败: {e}")
            return False, {}
    
    async def test_ai_guided_decision(self, knowledge_base, report_config, initial_analysis):
        """测试AI指导的研究决策"""
        print("\n🎯 测试AI指导研究决策...")
        
        try:
            with app.app_context():
                # 测试AI指导决策
                decision = await self.deep_research_service._send_guided_research_prompt(
                    knowledge_base, 
                    report_config, 
                    initial_analysis,
                    1
                )
            
            print(f"✅ AI指导决策测试完成")
            print(f"   AI决策: {decision.get('action', '未知')}")
            print(f"   决策理由: {decision.get('details', '无')[:100]}...")
            
            if decision.get('action') == 'search':
                keywords = decision.get('keywords', [])
                print(f"   搜索关键词: {', '.join(keywords[:3])}")
            
            return True, decision
            
        except Exception as e:
            print(f"❌ AI指导决策失败: {e}")
            return False, {}
    
    async def test_search_and_crawl(self, keywords):
        """测试搜索和爬取功能"""
        print("\n🔍 测试搜索和爬取功能...")
        
        if not self.settings.serp_api_key:
            print("⚠️ SERP API Key未配置，跳过搜索测试")
            return True, []
        
        try:
            # 测试搜索功能
            test_keywords = keywords[:2] if keywords else ['人工智能发展趋势', 'AI技术创新']
            
            with app.app_context():
                new_articles = await self.deep_research_service._execute_search_and_crawl(
                    test_keywords, 
                    [], 
                    self.settings
                )
            
            print(f"✅ 搜索和爬取测试完成")
            print(f"   搜索关键词: {test_keywords}")
            print(f"   新增文章: {len(new_articles)}")
            
            if new_articles:
                print(f"   示例文章:")
                for i, article in enumerate(new_articles[:2], 1):
                    print(f"     {i}. {article.get('title', '无标题')[:50]}...")
                    print(f"        来源: {article.get('source', '未知')}")
            
            return True, new_articles
            
        except Exception as e:
            print(f"❌ 搜索和爬取失败: {e}")
            return False, []
    
    def test_keyword_filtering(self, knowledge_base, report_config):
        """测试关键词过滤功能"""
        print("\n🔍 测试关键词过滤功能...")
        
        try:
            original_count = len(knowledge_base)
            print(f"   原始文章数: {original_count}")
            
            # 测试关键词过滤
            filtered_articles = self.llm_service.filter_articles_by_keywords(
                knowledge_base, 
                report_config.filter_keywords
            )
            
            filtered_count = len(filtered_articles)
            print(f"✅ 关键词过滤测试完成")
            print(f"   过滤关键词: {report_config.filter_keywords}")
            print(f"   过滤后文章数: {filtered_count}")
            print(f"   过滤率: {((original_count - filtered_count) / original_count * 100):.1f}%")
            
            if filtered_articles:
                print(f"   过滤后示例:")
                for i, article in enumerate(filtered_articles[:2], 1):
                    print(f"     {i}. {article.get('title', '无标题')[:50]}...")
            
            return True, filtered_articles
            
        except Exception as e:
            print(f"❌ 关键词过滤失败: {e}")
            return False, knowledge_base
    
    async def test_notification_push(self, report_content: str, report_config):
        """测试推送功能"""
        print("\n📢 测试推送功能...")
        
        # 检查是否有webhook配置
        if not hasattr(report_config, 'webhook_url') or not report_config.webhook_url:
            print("⚠️ 未配置Webhook URL，跳过推送测试")
            print("   💡 提示：请在【全局设置】或【报告配置】中配置Webhook URL以启用推送功能")
            return True  # 返回True表示测试通过（跳过）
        
        try:
            with app.app_context():
                # 测试推送报告
                success = await self.deep_research_service._send_report_notification(
                    report_content, report_config
                )
            
            print(f"✅ 推送测试完成")
            print(f"   推送类型: {getattr(report_config, 'notification_type', 'wechat')}")
            print(f"   Webhook URL: {report_config.webhook_url[:50]}...")
            print(f"   推送状态: {'成功' if success else '失败'}")
            
            if success:
                print("   📱 请检查群组是否收到通知消息")
            else:
                print("   ⚠️ 推送失败，请检查Webhook URL是否正确或网络连接")
            
            return success
            
        except Exception as e:
            print(f"❌ 推送测试失败: {e}")
            return False
    
    async def test_complete_deep_research(self, report_config):
        """测试完整的深度研究流程"""
        print("\n🔬 测试完整深度研究流程...")
        
        try:
            # 执行完整的深度研究
            with app.app_context():
                result = await self.deep_research_service.conduct_deep_research(
                    report_config, 
                    self.settings
                )
            
            if result['success']:
                print(f"✅ 完整深度研究流程测试成功")
                print(f"   知识库规模: {result['knowledge_base_size']} 篇文章")
                print(f"   研究迭代次数: {result['iterations']} 轮")
                print(f"   报告长度: {len(result['report'])} 字符")
                print(f"   推送状态: {'✅ 已推送' if result.get('notification_sent', False) else '❌ 未推送'}")
                
                # 显示研究日志
                print(f"\n📊 研究迭代日志:")
                for log_entry in result['research_log']:
                    print(f"   第{log_entry['iteration']}轮: {log_entry['action']} - {log_entry['details']}")
                
                # 保存报告到文件
                report_filename = f"v3_deep_research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                with open(report_filename, 'w', encoding='utf-8') as f:
                    f.write(result['report'])
                
                print(f"\n📄 完整报告已保存到: {report_filename}")
                
                # 显示报告预览
                print(f"\n📖 报告预览 (前500字符):")
                print("-" * 60)
                print(result['report'][:500])
                print("...")
                print("-" * 60)
                
                # 如果报告生成成功但推送失败，单独测试推送
                if not result.get('notification_sent', False):
                    print(f"\n📢 报告推送失败，进行单独推送测试...")
                    push_success = await self.test_notification_push(result['report'], report_config)
                    result['notification_sent'] = push_success
                
                return True, result
            else:
                print(f"❌ 深度研究流程失败: {result['message']}")
                return False, {}
                
        except Exception as e:
            print(f"❌ 完整深度研究流程测试失败: {e}")
            return False, {}
    
    def test_xml_parsing(self):
        """测试XML解析功能"""
        print("\n🔧 测试XML解析功能...")
        
        try:
            # 测试初步分析结果解析
            analysis_response = """<analysis>
<current_knowledge>
现有文章主要覆盖AI技术发展动态
</current_knowledge>
<knowledge_gaps>
缺乏具体技术细节和商业化数据
</knowledge_gaps>
<research_directions>
深入分析技术突破点
调研商业化进展
</research_directions>
<priority_keywords>
AI技术突破,商业化进展,市场数据
</priority_keywords>
</analysis>"""
            
            parsed = self.deep_research_service._parse_initial_analysis(analysis_response)
            assert 'summary' in parsed
            assert 'gaps' in parsed
            assert len(parsed['directions']) > 0
            print("✅ AI分析结果解析正确")
            
            # 测试研究决策解析
            decision_response = """<research_decision>
<action>search</action>
<keywords>AI技术创新,商业应用,市场趋势</keywords>
<reasoning>需要补充技术细节和市场数据</reasoning>
</research_decision>"""
            
            parsed = self.deep_research_service._parse_research_decision(decision_response)
            assert parsed['action'] == 'search'
            assert len(parsed['keywords']) == 3
            print("✅ 研究决策解析正确")
            
            # 测试结束决策解析
            finish_response = """<research_decision>
<action>finish</action>
<reasoning>已获得足够信息，可以生成报告</reasoning>
</research_decision>"""
            
            parsed = self.deep_research_service._parse_research_decision(finish_response)
            assert parsed['action'] == 'finish'
            print("✅ 结束决策解析正确")
            
            # 测试knowledge_base XML构建
            test_articles = [
                {
                    'title': '测试文章1',
                    'url': 'https://example.com/1',
                    'content': '这是测试内容',
                    'source': '测试来源',
                    'date': '2025-01-01'
                }
            ]
            
            kb_xml = self.deep_research_service._build_knowledge_base_xml(test_articles)
            assert '<knowledge_base>' in kb_xml
            assert '<article id=\'1\'>' in kb_xml
            print("✅ knowledge_base XML构建正确")
            
            return True
            
        except Exception as e:
            print(f"❌ XML解析测试失败: {e}")
            return False
    
    def generate_test_summary(self, results):
        """生成测试总结"""
        print("\n" + "="*80)
        print("📋 V3.0 AI指导深度研究测试总结")
        print("="*80)
        
        print(f"🕐 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 测试环境: {self.settings.llm_provider} ({self.settings.llm_model_name})")
        print(f"🔑 SERP API: {'已配置' if self.settings.serp_api_key else '未配置'}")
        
        print(f"\n📊 测试结果:")
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {test_name}: {status}")
        
        print(f"\n🎯 总体结果: {passed_tests}/{total_tests} 项测试通过")
        
        if passed_tests == total_tests:
            print("🎉 所有测试通过！V3.0 AI指导深度研究功能运行正常")
            return True
        else:
            print("⚠️ 部分测试失败，请检查相关配置和服务")
            return False

async def main():
    """主测试函数"""
    print("🚀 开始V3.0 AI指导深度研究测试")
    print("="*80)
    
    tester = V3DeepResearchTester()
    
    # 初始化
    if not tester.setup():
        print("❌ 测试环境初始化失败")
        return False
    
    results = {}
    
    try:
        # 1. 创建测试配置
        test_config = tester.create_test_report_config()
        
        # 2. 测试XML解析功能
        xml_success = tester.test_xml_parsing()
        results["XML解析功能"] = xml_success
        
        # 3. 测试初始知识库构建
        kb_success, knowledge_base = await tester.test_initial_knowledge_base(test_config)
        results["初始知识库构建"] = kb_success
        
        # 4. 测试关键词过滤
        if kb_success and knowledge_base:
            filter_success, filtered_articles = tester.test_keyword_filtering(knowledge_base, test_config)
            results["关键词过滤"] = filter_success
            knowledge_base = filtered_articles  # 使用过滤后的文章
        else:
            results["关键词过滤"] = False
        
        # 5. 测试AI初步分析
        if kb_success and knowledge_base:
            analysis_success, initial_analysis = await tester.test_ai_initial_analysis(knowledge_base, test_config)
            results["AI初步分析"] = analysis_success
        else:
            results["AI初步分析"] = False
            initial_analysis = {}
        
        # 6. 测试AI指导决策
        if analysis_success and initial_analysis:
            decision_success, decision = await tester.test_ai_guided_decision(knowledge_base, test_config, initial_analysis)
            results["AI指导决策"] = decision_success
            
            # 7. 测试搜索和爬取
            keywords = decision.get('keywords', []) if decision_success else []
            search_success, new_articles = await tester.test_search_and_crawl(keywords)
            results["搜索和爬取"] = search_success
        else:
            results["AI指导决策"] = False
            results["搜索和爬取"] = False
        
        # 8. 测试完整深度研究流程（包含推送）
        complete_success, complete_result = await tester.test_complete_deep_research(test_config)
        results["完整深度研究流程"] = complete_success
        
        # 9. 检查推送功能（如果完整流程中推送失败，这里不会重复）
        if complete_success and complete_result:
            notification_success = complete_result.get('notification_sent', False)
            results["报告推送功能"] = notification_success
        else:
            results["报告推送功能"] = False
        
        # 生成测试总结
        overall_success = tester.generate_test_summary(results)
        
        return overall_success
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生严重错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎯 启动V3.0 AI指导深度研究测试...")
    success = asyncio.run(main())
    
    if success:
        print("\n🎊 测试完成！V3.0 AI指导深度研究功能正常运行")
        print("💡 新特性: 基于数据库内容 → 关键词过滤 → AI分析指导 → 精准搜索 → 高质量报告")
        sys.exit(0)
    else:
        print("\n💥 测试失败！请检查系统配置和日志")
        sys.exit(1)
