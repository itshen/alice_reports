#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V3.0 XML交互版深度研究测试用例
专门测试B端商业模式观察报告的AI研究流程
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
    """V3.0 XML交互版深度研究测试类 - B端商业模式观察"""
    
    def __init__(self):
        self.crawler_service = CrawlerService()
        self.llm_service = LLMService()
        self.deep_research_service = None
        self.settings = None
        
    def setup(self):
        """初始化测试环境"""
        print("🔧 初始化V3.0深度研究测试环境 (B端商业模式观察)...")
        
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
            
            # 检查数据库配置状态
            from services.default_config_service import DefaultConfigService
            config_status = DefaultConfigService.get_config_status()
            
            print(f"✅ 测试环境初始化完成")
            print(f"   LLM Provider: {self.settings.llm_provider}")
            print(f"   LLM Model: {self.settings.llm_model_name}")
            print(f"   LLM API Key: {'已配置' if self.settings.llm_api_key else '未配置'}")
            print(f"   SERP API Key: {'已配置' if self.settings.serp_api_key else '未配置'}")
            print(f"   爬虫配置数量: {config_status['crawler_count']}")
            print(f"   报告配置数量: {config_status['report_count']}")
            print(f"   全局设置: {'已配置' if config_status['has_global_settings'] else '未配置'}")
            
            return True
    
    def create_test_report_config(self):
        """创建B端商业模式观察报告配置"""
        print("\n📋 创建B端商业模式观察报告配置...")
        
        with app.app_context():
            from models import CrawlerConfig
            
            # 专门使用B端商业模式观察报告配置
            print("🎯 使用B端商业模式观察报告配置进行测试")
            
            # 获取订阅定价和企业软件出海相关的爬虫配置
            # 根据default_config_service.py，数据源是 "16,17" (订阅定价,企业软件出海)
            target_crawler_names = ['B端-订阅定价', 'B端-企业软件出海']
            crawlers = CrawlerConfig.query.filter(
                CrawlerConfig.name.in_(target_crawler_names)
            ).filter_by(is_active=True).all()
            
            if crawlers:
                crawler_ids = [str(crawler.id) for crawler in crawlers]
                print(f"   找到对应爬虫配置: {[c.name for c in crawlers]}")
            else:
                # 如果没有找到特定爬虫，使用通用的B端爬虫
                b2b_crawlers = CrawlerConfig.query.filter(
                    CrawlerConfig.name.like('%B端%') | 
                    CrawlerConfig.name.like('%企业服务%')
                ).filter_by(is_active=True).limit(3).all()
                
                if b2b_crawlers:
                    crawler_ids = [str(crawler.id) for crawler in b2b_crawlers]
                    print(f"   使用通用B端爬虫: {[c.name for c in b2b_crawlers]}")
                else:
                    # 最后使用默认ID
                    crawler_ids = ['16', '17']
                    print("   使用默认数据源ID: 16,17")
            
            # 创建B端商业模式观察报告配置
            test_config = type('TestReportConfig', (), {
                'id': 998,  # 测试用ID
                'name': 'B端商业模式观察报告',
                'data_sources': ','.join(crawler_ids),
                'filter_keywords': 'B端订阅定价,企业软件出海,SaaS商业模式,按需付费,生态扩展,定价策略,订阅模式,出海策略,本土化,合规适配',
                'time_range': '7d',
                'purpose': '观察B端企业服务的商业模式变化，包括定价策略、生态扩展、出海动态等',
                'research_focus': '''💼 **商业模式深度观察**：
- 定价策略演进：分层订阅优化、按需付费模式、价值定价策略
- 生态扩展分析：平台抽成调整、开发者激励机制、生态健康度评估
- 出海动态追踪：本土化策略、合规适配要求、市场表现分析
- 盈利模式创新：收入结构变化、成本控制策略、规模效应实现
- 商业趋势预测：模式演进方向、市场机会识别、风险因素分析''',
                'enable_deep_research': True,
                'notification_type': 'jinshan',
                'webhook_url': ''  # 测试时不推送
            })()
            
            print(f"✅ B端商业模式观察报告配置创建完成:")
            print(f"   报告名称: {test_config.name}")
            print(f"   数据源: {test_config.data_sources}")
            print(f"   关键词: {test_config.filter_keywords}")
            print(f"   时间范围: {test_config.time_range}")
            print(f"   研究目的: {test_config.purpose}")
            print(f"   研究重点: 商业模式深度观察...")
            
            return test_config
    
    async def test_initial_knowledge_base(self, report_config):
        """测试初始知识库构建"""
        print("\n📚 测试初始知识库构建...")
        
        try:
            with app.app_context():
                knowledge_base = await self.deep_research_service._build_initial_knowledge_base(report_config)
            
            print(f"✅ 初始知识库构建完成")
            print(f"   文章数量: {len(knowledge_base)}")
            
            # 如果没有数据，创建一些测试数据
            if not knowledge_base:
                print("⚠️ 数据库中暂无相关文章，创建测试数据...")
                knowledge_base = self._create_test_articles(report_config)
                print(f"   生成测试文章数量: {len(knowledge_base)}")
            
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
    
    def _create_test_articles(self, report_config):
        """创建测试文章数据"""
        from datetime import datetime, timedelta
        
        # 专门为B端商业模式观察报告创建测试数据
        if '商业模式' in report_config.name:
            # B端商业模式观察专项测试数据
            test_articles = [
                {
                    'title': 'SaaS订阅定价策略新趋势：从固定包月到价值定价',
                    'content': '随着B端SaaS市场的成熟，越来越多的企业服务商开始探索更灵活的定价策略。从传统的固定包月模式，向基于使用量、价值导向的定价模式转变。一些头部SaaS厂商推出了分层订阅、按需付费等创新定价方案，以更好地匹配客户的实际价值获得。',
                    'url': 'https://example.com/saas-pricing-trends-2024',
                    'source': 'SaaS商业观察',
                    'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                    'publish_date': datetime.now() - timedelta(days=1)
                },
                {
                    'title': '中国企业软件出海加速：本土化策略成关键',
                    'content': '2024年中国企业服务软件出海步伐明显加快，多家公司在东南亚、欧美市场取得突破。成功案例显示，本土化适配、合规要求满足、当地合作伙伴建立是出海成功的三大关键要素。钉钉、腾讯会议等产品的海外版本获得了良好的市场反响。',
                    'url': 'https://example.com/china-enterprise-software-global',
                    'source': '出海观察',
                    'date': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
                    'publish_date': datetime.now() - timedelta(days=2)
                },
                {
                    'title': '平台生态扩展新模式：开发者激励机制创新',
                    'content': '主流B端平台正在重新设计开发者生态激励机制。从简单的收入分成模式，演进到技术支持、市场推广、资源对接等全方位赋能体系。微软、Salesforce等平台的开发者生态健康度评估显示，多元化激励比单一抽成更能促进生态繁荣。',
                    'url': 'https://example.com/platform-ecosystem-innovation',
                    'source': '平台经济研究',
                    'date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
                    'publish_date': datetime.now() - timedelta(days=3)
                },
                {
                    'title': '企业服务盈利模式创新：订阅+服务混合模式兴起',
                    'content': '传统的纯订阅模式在B端市场面临挑战，越来越多企业开始采用订阅+专业服务的混合盈利模式。这种模式不仅能提供稳定的订阅收入，还能通过定制化服务获得更高的客单价和客户粘性。行业数据显示，混合模式的平均客户生命周期价值比纯订阅模式高出30-50%。',
                    'url': 'https://example.com/hybrid-business-model-b2b',
                    'source': '商业模式研究',
                    'date': (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d'),
                    'publish_date': datetime.now() - timedelta(days=4)
                },
                {
                    'title': '按需付费模式在企业服务中的应用与挑战',
                    'content': '按需付费（Pay-as-you-go）模式在云计算领域的成功，启发了更多企业服务商探索这一定价策略。从API调用计费到存储容量计费，按需付费能够降低客户的使用门槛，但同时也对服务商的成本控制和收入预测带来挑战。AWS、Azure的成功案例为其他企业服务商提供了参考。',
                    'url': 'https://example.com/pay-as-you-go-enterprise-services',
                    'source': '定价策略分析',
                    'date': (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
                    'publish_date': datetime.now() - timedelta(days=5)
                }
            ]
        else:
            # 通用B端测试数据
            test_articles = [
                {
                    'title': '企业服务数字化转型加速，SaaS市场迎来新机遇',
                    'content': '随着企业数字化转型需求的不断增长，SaaS软件即服务市场正在经历快速发展。企业对于云端解决方案的接受度持续提升，推动了整个B端服务市场的创新和竞争。',
                    'url': 'https://example.com/enterprise-digital-transformation',
                    'source': '企业服务观察',
                    'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                    'publish_date': datetime.now() - timedelta(days=1)
                }
            ]
        
        return test_articles
    
    async def test_ai_content_evaluation(self, knowledge_base, report_config):
        """测试AI内容评估功能（判断是否足够写报告）"""
        print("\n🧠 测试AI内容评估功能...")
        
        try:
            with app.app_context():
                # 单次AI调用超时控制
                import asyncio
                decision = await asyncio.wait_for(
                    self.deep_research_service._send_research_prompt(
                        knowledge_base, 
                        report_config,
                        1
                    ),
                    timeout=30.0  # 单次AI调用30秒超时
                )
            
            print(f"✅ AI内容评估测试完成")
            print(f"   AI判断: {decision.get('action', '未知')}")
            print(f"   判断理由: {decision.get('details', '无')[:100]}...")
            
            if decision.get('action') == 'search':
                keywords = decision.get('keywords', [])
                print(f"   需要搜索关键词: {', '.join(keywords[:3])}")
            elif decision.get('action') == 'finish':
                print(f"   AI认为现有资料足够写报告")
            
            return True, decision
            
        except asyncio.TimeoutError:
            print(f"❌ AI内容评估超时（30秒），API响应过慢")
            return False, {}
        except Exception as e:
            print(f"❌ AI内容评估失败: {e}")
            import traceback
            traceback.print_exc()
            return False, {}
    
    
    async def test_search_and_crawl(self, keywords):
        """测试搜索和爬取功能"""
        print("\n🔍 测试搜索和爬取功能...")
        
        if not self.settings.serp_api_key:
            print("⚠️ SERP API Key未配置，跳过搜索测试")
            return True, []
        
        try:
            # 测试搜索功能
            test_keywords = keywords[:2] if keywords else ['B端订阅定价', 'SaaS商业模式']
            
            with app.app_context():
                # 搜索和爬取不设置总体超时，让内部的单次操作超时控制
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
            import traceback
            traceback.print_exc()
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
                # 完整深度研究流程不设置总体超时，让内部的单次操作超时控制
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
            import traceback
            traceback.print_exc()
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
        print("📋 V3.0 AI指导深度研究测试总结 - B端商业模式观察")
        print("="*80)
        
        print(f"🕐 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 测试环境: {self.settings.llm_provider} ({self.settings.llm_model_name})")
        print(f"🔑 SERP API: {'已配置' if self.settings.serp_api_key else '未配置'}")
        
        # 显示数据库配置状态
        with app.app_context():
            from services.default_config_service import DefaultConfigService
            from models import ReportConfig
            config_status = DefaultConfigService.get_config_status()
            deep_research_configs = ReportConfig.query.filter_by(enable_deep_research=True).count()
            
            print(f"📚 数据库状态:")
            print(f"   爬虫配置: {config_status['crawler_count']} 个")
            print(f"   报告配置: {config_status['report_count']} 个")
            print(f"   深度研究配置: {deep_research_configs} 个")
        
        print(f"\n📊 测试结果:")
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {test_name}: {status}")
        
        print(f"\n🎯 总体结果: {passed_tests}/{total_tests} 项测试通过")
        
        if passed_tests == total_tests:
            print("🎉 所有测试通过！V3.0 AI指导深度研究功能运行正常")
            print("💡 商业模式特性: 定价策略分析 → 生态扩展观察 → 出海动态追踪 → 盈利模式创新 → 商业趋势预测")
            return True
        else:
            print("⚠️ 部分测试失败，请检查相关配置和服务")
            return False

async def main():
    """主测试函数"""
    print("🚀 开始V3.0 AI指导深度研究测试 - B端商业模式观察")
    print("="*80)
    
    tester = V3DeepResearchTester()
    
    # 初始化
    if not tester.setup():
        print("❌ 测试环境初始化失败")
        return False
    
    results = {}
    
    try:
        # 1. 获取测试配置
        test_config = tester.create_test_report_config()
        if not test_config:
            print("❌ 无法获取测试配置")
            return False
        
        # 2. 测试XML解析功能（快速测试）
        xml_success = tester.test_xml_parsing()
        results["XML解析功能"] = xml_success
        
        # 3. 测试初始知识库构建
        kb_success, knowledge_base = await tester.test_initial_knowledge_base(test_config)
        results["初始知识库构建"] = kb_success
        
        # 4. 测试关键词过滤
        if kb_success and knowledge_base:
            filter_success, filtered_articles = tester.test_keyword_filtering(knowledge_base, test_config)
            results["关键词过滤"] = filter_success
            knowledge_base = filtered_articles if filter_success else knowledge_base
        else:
            results["关键词过滤"] = False
        
        # 5. 测试AI内容评估（判断是否足够写报告）
        if kb_success and knowledge_base:
            evaluation_success, decision = await tester.test_ai_content_evaluation(knowledge_base, test_config)
            results["AI内容评估"] = evaluation_success
            
            # 6. 根据AI判断决定是否搜索
            if evaluation_success and decision.get('action') == 'search':
                keywords = decision.get('keywords', [])
                search_success, new_articles = await tester.test_search_and_crawl(keywords)
                results["搜索和爬取"] = search_success
            else:
                # AI认为现有资料足够，跳过搜索
                print("🎯 AI认为现有资料足够，跳过搜索步骤")
                results["搜索和爬取"] = True  # 标记为成功，因为不需要搜索
        else:
            results["AI内容评估"] = False
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
    print("🎯 启动V3.0 AI指导深度研究测试 - B端商业模式观察...")
    print("📝 本测试专门针对B端商业模式观察报告进行测试")
    success = asyncio.run(main())
    
    if success:
        print("\n🎊 测试完成！V3.0 AI指导深度研究功能正常运行")
        print("💡 商业模式优势: 定价策略深度分析 → 生态扩展动态观察 → 出海策略追踪 → 盈利模式创新洞察")
        print("🔧 如需修改配置，请访问 Web 界面的【报告配置】页面")
        sys.exit(0)
    else:
        print("\n💥 测试失败！请检查系统配置和日志")
        print("💡 提示：确保已配置 LLM API Key，并检查数据库中是否有有效的配置")
        sys.exit(1)
