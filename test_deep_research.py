#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度研究功能测试用例
基于当前系统逻辑，测试完整的深度研究流程
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import GlobalSettings, CrawlerConfig, ReportConfig, CrawlRecord, ReportRecord
from services.crawler_service import CrawlerService
from services.llm_service import LLMService
from services.notification_service import NotificationService

class DeepResearchTester:
    """深度研究测试类"""
    
    def __init__(self):
        self.crawler_service = CrawlerService()
        self.llm_service = LLMService()
        self.notification_service = NotificationService()
        self.settings = None
        
    def setup(self):
        """初始化测试环境"""
        print("🔧 初始化测试环境...")
        
        with app.app_context():
            # 获取全局设置
            self.settings = GlobalSettings.query.first()
            if not self.settings:
                print("❌ 未找到全局设置，请先配置系统")
                return False
            
            # 更新LLM服务设置
            self.llm_service.update_settings(self.settings)
            
            print(f"✅ 已加载配置:")
            print(f"   LLM Provider: {self.settings.llm_provider}")
            print(f"   LLM Model: {self.settings.llm_model_name}")
            print(f"   API Key: {'已配置' if self.settings.llm_api_key else '未配置'}")
            print(f"   SERP API: {'已配置' if self.settings.serp_api_key else '未配置'}")
            
            return True
    
    async def test_crawler_service(self):
        """测试爬虫服务"""
        print("\n🕷️ 测试爬虫服务...")
        
        with app.app_context():
            # 获取一个激活的爬虫配置
            crawler = CrawlerConfig.query.filter_by(is_active=True).first()
            if not crawler:
                print("❌ 未找到激活的爬虫配置")
                return False, []
            
            print(f"📰 使用爬虫: {crawler.name}")
            print(f"   列表页URL: {crawler.list_url}")
            print(f"   正则表达式: {crawler.url_regex}")
            
            try:
                # 测试连接
                print("🔗 测试连接...")
                connection_result = await self.crawler_service.test_connection(crawler.list_url)
                if not connection_result['success']:
                    print(f"❌ 连接测试失败: {connection_result['error']}")
                    return False, []
                
                print(f"✅ 连接成功，页面标题: {connection_result.get('title', 'N/A')}")
                
                # 提取URL列表
                print("🔍 提取URL列表...")
                urls = await self.crawler_service.extract_urls_from_page(
                    crawler.list_url, 
                    crawler.url_regex
                )
                
                if not urls:
                    print("❌ 未提取到任何URL")
                    return False, []
                
                print(f"✅ 提取到 {len(urls)} 个URL")
                print(f"   前3个URL: {urls[:3]}")
                
                # 抓取文章内容（测试前5篇）
                print("📄 抓取文章内容...")
                articles = []
                test_urls = urls[:5]  # 只测试前5个URL
                
                for i, url in enumerate(test_urls, 1):
                    print(f"   正在抓取 {i}/{len(test_urls)}: {url}")
                    result = await self.crawler_service.crawl_article_content(url)
                    
                    if result['success']:
                        articles.append({
                            'title': result['title'],
                            'content': result['content'],
                            'author': result.get('author', ''),
                            'url': result['url'],
                            'date': result.get('date', '')
                        })
                        print(f"     ✅ 成功: {result['title'][:50]}...")
                    else:
                        print(f"     ❌ 失败: {result['error']}")
                    
                    # 添加延迟避免被封
                    await asyncio.sleep(1)
                
                print(f"✅ 爬虫测试完成，成功抓取 {len(articles)} 篇文章")
                return True, articles
                
            except Exception as e:
                print(f"❌ 爬虫测试失败: {e}")
                return False, []
    
    def test_llm_service(self, articles):
        """测试LLM服务"""
        print("\n🤖 测试LLM服务...")
        
        if not articles:
            print("❌ 没有文章数据，跳过LLM测试")
            return False, None
        
        try:
            # 测试连接
            print("🔗 测试LLM连接...")
            connection_result = self.llm_service.test_connection()
            if not connection_result['success']:
                print(f"❌ LLM连接失败: {connection_result['message']}")
                return False, None
            
            print(f"✅ LLM连接成功: {connection_result['message']}")
            
            # 测试关键词过滤
            print("🔍 测试关键词过滤...")
            test_keywords = "AI,人工智能,科技,技术"
            filtered_articles = self.llm_service.filter_articles_by_keywords(articles, test_keywords)
            print(f"✅ 关键词过滤完成，原文章数: {len(articles)}, 过滤后: {len(filtered_articles)}")
            
            # 创建测试报告配置
            with app.app_context():
                test_report_config = type('TestReportConfig', (), {
                    'name': '深度研究测试报告',
                    'purpose': '测试深度研究功能的完整性和准确性',
                    'research_focus': '分析当前科技发展趋势，特别关注AI技术的最新进展和应用场景',
                    'data_sources': '1,2,3',
                    'filter_keywords': test_keywords,
                    'time_range': '24h'
                })()
            
            # 测试深度研究报告生成
            print("📊 生成深度研究报告...")
            deep_report = self.llm_service.generate_deep_research_report(filtered_articles, test_report_config)
            
            if deep_report and len(deep_report) > 100:
                print(f"✅ 深度研究报告生成成功，长度: {len(deep_report)} 字符")
                print(f"   报告预览: {deep_report[:200]}...")
                
                # 测试简单报告生成（对比）
                print("📋 生成简单报告（对比）...")
                simple_report = self.llm_service.generate_simple_report(filtered_articles, test_report_config)
                print(f"✅ 简单报告生成成功，长度: {len(simple_report)} 字符")
                
                return True, {
                    'deep_report': deep_report,
                    'simple_report': simple_report,
                    'articles_count': len(filtered_articles)
                }
            else:
                print("❌ 深度研究报告生成失败或内容过短")
                return False, None
                
        except Exception as e:
            print(f"❌ LLM服务测试失败: {e}")
            return False, None
    
    def test_notification_service(self, report_data):
        """测试通知服务"""
        print("\n📱 测试通知服务...")
        
        if not report_data:
            print("❌ 没有报告数据，跳过通知测试")
            return False
        
        try:
            # 测试深度研究报告格式化
            print("📝 测试深度研究报告格式化...")
            deep_notification = self.notification_service.format_deep_research_for_notification(
                report_data['deep_report']
            )
            print(f"✅ 深度研究通知格式化完成，长度: {len(deep_notification)} 字符")
            
            # 测试简单报告格式化
            print("📝 测试简单报告格式化...")
            simple_notification = self.notification_service.format_simple_report_for_notification(
                report_data['simple_report']
            )
            print(f"✅ 简单报告通知格式化完成，长度: {len(simple_notification)} 字符")
            
            # 测试Webhook（如果配置了的话）
            print("🔗 测试Webhook连接...")
            test_webhook_result = self.notification_service.test_webhook(
                'wechat', 
                'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test'
            )
            
            if test_webhook_result['success']:
                print("✅ Webhook测试成功")
            else:
                print(f"⚠️ Webhook测试失败（这是正常的，因为使用的是测试URL）: {test_webhook_result['message']}")
            
            return True
            
        except Exception as e:
            print(f"❌ 通知服务测试失败: {e}")
            return False
    
    async def test_end_to_end_workflow(self):
        """测试端到端工作流程"""
        print("\n🔄 测试端到端工作流程...")
        
        with app.app_context():
            try:
                # 获取深度研究报告配置
                deep_report = ReportConfig.query.filter_by(enable_deep_research=True).first()
                if not deep_report:
                    print("❌ 未找到深度研究报告配置")
                    return False
                
                print(f"📊 使用报告配置: {deep_report.name}")
                print(f"   研究重点: {deep_report.research_focus}")
                print(f"   数据源: {deep_report.data_sources}")
                
                # 获取数据源爬虫
                crawler_ids = [int(x) for x in deep_report.data_sources.split(',') if x.strip()]
                print(f"🕷️ 数据源爬虫ID: {crawler_ids}")
                
                # 模拟获取最近的爬取数据
                articles = []
                for crawler_id in crawler_ids[:2]:  # 只测试前2个数据源
                    crawler = CrawlerConfig.query.get(crawler_id)
                    if crawler:
                        print(f"   从爬虫 '{crawler.name}' 获取数据...")
                        
                        # 检查是否有历史数据
                        records = CrawlRecord.query.filter_by(
                            crawler_config_id=crawler_id,
                            status='success'
                        ).order_by(CrawlRecord.crawled_at.desc()).limit(5).all()
                        
                        if records:
                            print(f"     找到 {len(records)} 条历史记录")
                            for record in records:
                                articles.append({
                                    'title': record.title,
                                    'content': record.content,
                                    'author': record.author,
                                    'url': record.url,
                                    'date': record.publish_date.isoformat() if record.publish_date else ''
                                })
                        else:
                            print(f"     没有历史记录，执行实时抓取...")
                            # 实时抓取少量数据
                            results = await self.crawler_service.run_crawler_task(crawler)
                            for result in results[:3]:  # 只取前3篇
                                if result['success']:
                                    articles.append({
                                        'title': result['title'],
                                        'content': result['content'],
                                        'author': result.get('author', ''),
                                        'url': result['url'],
                                        'date': result.get('date', '')
                                    })
                
                if not articles:
                    print("❌ 未获取到任何文章数据")
                    return False
                
                print(f"✅ 共获取到 {len(articles)} 篇文章")
                
                # 过滤文章
                if deep_report.filter_keywords:
                    print(f"🔍 应用关键词过滤: {deep_report.filter_keywords}")
                    articles = self.llm_service.filter_articles_by_keywords(
                        articles, 
                        deep_report.filter_keywords
                    )
                    print(f"   过滤后文章数: {len(articles)}")
                
                # 生成深度研究报告
                print("📊 生成深度研究报告...")
                report_content = self.llm_service.generate_deep_research_report(articles, deep_report)
                
                if report_content and len(report_content) > 100:
                    print(f"✅ 深度研究报告生成成功，长度: {len(report_content)} 字符")
                    
                    # 保存报告记录（测试用）
                    test_record = ReportRecord(
                        report_config_id=deep_report.id,
                        title=f"{deep_report.name} - 测试报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        content=report_content,
                        summary=report_content[:200] + '...' if len(report_content) > 200 else report_content,
                        status='success'
                    )
                    db.session.add(test_record)
                    db.session.commit()
                    
                    print(f"✅ 测试报告已保存到数据库，ID: {test_record.id}")
                    
                    # 格式化通知内容
                    print("📱 格式化通知内容...")
                    notification_content = self.notification_service.format_deep_research_for_notification(
                        report_content
                    )
                    print(f"✅ 通知内容格式化完成，长度: {len(notification_content)} 字符")
                    
                    return True
                else:
                    print("❌ 深度研究报告生成失败")
                    return False
                    
            except Exception as e:
                print(f"❌ 端到端测试失败: {e}")
                return False
    
    def generate_test_report(self, results):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📋 深度研究功能测试报告")
        print("="*60)
        
        print(f"🕐 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 测试环境: {self.settings.llm_provider} ({self.settings.llm_model_name})")
        
        print("\n📊 测试结果汇总:")
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {test_name}: {status}")
        
        print(f"\n🎯 总体结果: {passed_tests}/{total_tests} 项测试通过")
        
        if passed_tests == total_tests:
            print("🎉 所有测试通过！深度研究功能运行正常")
            return True
        else:
            print("⚠️ 部分测试失败，请检查相关配置和服务")
            return False

async def main():
    """主测试函数"""
    print("🧪 开始深度研究功能测试")
    print("="*60)
    
    tester = DeepResearchTester()
    
    # 初始化
    if not tester.setup():
        print("❌ 测试环境初始化失败")
        return False
    
    results = {}
    
    try:
        # 测试爬虫服务
        crawler_success, articles = await tester.test_crawler_service()
        results["爬虫服务"] = crawler_success
        
        # 测试LLM服务
        llm_success, report_data = tester.test_llm_service(articles)
        results["LLM服务"] = llm_success
        
        # 测试通知服务
        notification_success = tester.test_notification_service(report_data)
        results["通知服务"] = notification_success
        
        # 测试端到端工作流程
        e2e_success = await tester.test_end_to_end_workflow()
        results["端到端流程"] = e2e_success
        
        # 生成测试报告
        overall_success = tester.generate_test_report(results)
        
        return overall_success
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生严重错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 启动深度研究功能测试...")
    success = asyncio.run(main())
    
    if success:
        print("\n🎊 测试完成！系统深度研究功能正常运行")
        sys.exit(0)
    else:
        print("\n💥 测试失败！请检查系统配置和日志")
        sys.exit(1)
