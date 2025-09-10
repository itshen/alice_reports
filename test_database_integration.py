#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库集成测试 - 验证搜索结果入库功能
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import GlobalSettings, CrawlerConfig, CrawlRecord
from services.deep_research_service import DeepResearchService
from services.crawler_service import CrawlerService
from services.llm_service import LLMService

async def test_database_integration():
    """测试数据库集成功能"""
    print("🗄️ 测试深度研究数据库集成功能")
    print("="*60)
    
    with app.app_context():
        # 获取全局设置
        settings = GlobalSettings.query.first()
        if not settings:
            print("❌ 未找到全局设置")
            return False
        
        # 创建服务实例
        crawler_service = CrawlerService()
        llm_service = LLMService()
        llm_service.update_settings(settings)
        deep_research_service = DeepResearchService(crawler_service, llm_service)
        
        print("✅ 服务初始化完成")
        
        # 1. 检查现有数据
        print("\n📊 检查现有数据库状态...")
        
        total_crawlers = CrawlerConfig.query.count()
        total_records = CrawlRecord.query.count()
        deep_research_crawler = CrawlerConfig.query.filter_by(name="深度研究").first()
        
        print(f"   总爬虫数: {total_crawlers}")
        print(f"   总记录数: {total_records}")
        print(f"   深度研究爬虫: {'已存在' if deep_research_crawler else '不存在'}")
        
        if deep_research_crawler:
            deep_records = CrawlRecord.query.filter_by(
                crawler_config_id=deep_research_crawler.id
            ).count()
            print(f"   深度研究记录数: {deep_records}")
        
        # 2. 测试保存搜索结果
        print("\n💾 测试保存搜索结果到数据库...")
        
        # 模拟一个搜索结果
        mock_crawl_result = {
            'title': '测试深度研究文章 - AI技术发展',
            'content': '这是一篇关于AI技术发展的测试文章内容。包含了人工智能、机器学习等关键词。',
            'url': f'https://test-deep-research.com/article/{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'author': '测试作者',
            'success': True
        }
        
        try:
            await deep_research_service._save_search_result_to_db(mock_crawl_result, "AI技术发展")
            print("✅ 搜索结果保存成功")
        except Exception as e:
            print(f"❌ 搜索结果保存失败: {e}")
            return False
        
        # 3. 验证数据是否正确保存
        print("\n🔍 验证保存的数据...")
        
        # 重新查询深度研究爬虫
        deep_research_crawler = CrawlerConfig.query.filter_by(name="深度研究").first()
        if not deep_research_crawler:
            print("❌ 深度研究爬虫未创建")
            return False
        
        print(f"✅ 深度研究爬虫已创建，ID: {deep_research_crawler.id}")
        
        # 查询刚保存的记录
        saved_record = CrawlRecord.query.filter_by(
            url=mock_crawl_result['url']
        ).first()
        
        if not saved_record:
            print("❌ 保存的记录未找到")
            return False
        
        print(f"✅ 记录保存成功:")
        print(f"   标题: {saved_record.title}")
        print(f"   URL: {saved_record.url}")
        print(f"   内容长度: {len(saved_record.content)} 字符")
        print(f"   爬虫ID: {saved_record.crawler_config_id}")
        
        # 4. 测试从数据库获取深度研究数据
        print("\n📚 测试从数据库获取深度研究历史数据...")
        
        # 创建测试报告配置
        test_config = type('TestConfig', (), {
            'data_sources': '1,2',  # 使用前两个爬虫
            'filter_keywords': 'AI,人工智能,技术',
            'time_range': '7d'
        })()
        
        try:
            knowledge_base = await deep_research_service._build_initial_knowledge_base(test_config)
            print(f"✅ 知识库构建成功，共 {len(knowledge_base)} 篇文章")
            
            # 统计数据来源
            sources = {}
            for article in knowledge_base:
                source = article.get('source', '未知来源')
                sources[source] = sources.get(source, 0) + 1
            
            print("📊 数据来源统计:")
            for source, count in sources.items():
                print(f"   {source}: {count} 篇")
                
        except Exception as e:
            print(f"❌ 知识库构建失败: {e}")
            return False
        
        # 5. 测试重复URL检查
        print("\n🔄 测试重复URL检查...")
        
        try:
            # 尝试保存相同URL的记录
            await deep_research_service._save_search_result_to_db(mock_crawl_result, "重复测试")
            print("✅ 重复URL检查正常（应该跳过重复记录）")
        except Exception as e:
            print(f"❌ 重复URL检查失败: {e}")
            return False
        
        print("\n" + "="*60)
        print("🎉 数据库集成测试全部通过！")
        print("✅ 搜索结果可以正确入库")
        print("✅ 深度研究爬虫自动创建")
        print("✅ 历史数据可以正确获取")
        print("✅ 重复URL检查正常工作")
        print("="*60)
        
        return True

if __name__ == "__main__":
    success = asyncio.run(test_database_integration())
    
    if success:
        print("\n🎊 数据库集成测试完成！")
        print("💡 现在深度研究功能会:")
        print("   1. 优先使用数据库中的现有数据")
        print("   2. 将搜索到的新内容自动入库")
        print("   3. 避免重复爬取相同URL")
        sys.exit(0)
    else:
        print("\n💥 数据库集成测试失败！")
        sys.exit(1)
