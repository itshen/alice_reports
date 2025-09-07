#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统功能测试脚本
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.crawler_service import CrawlerService
from services.llm_service import LLMService
from services.notification_service import NotificationService

async def test_crawler_service():
    """测试爬虫服务"""
    print("🕷️ 测试爬虫服务...")
    
    crawler_service = CrawlerService()
    
    # 测试连接
    result = await crawler_service.test_connection("https://example.com")
    if result['success']:
        print("✅ 爬虫连接测试成功")
        print(f"   页面标题: {result.get('title', 'N/A')}")
        print(f"   内容长度: {len(result.get('content', ''))}")
    else:
        print(f"❌ 爬虫连接测试失败: {result.get('error')}")
    
    return result['success']

def test_llm_service():
    """测试LLM服务"""
    print("\n🤖 测试LLM服务...")
    
    llm_service = LLMService()
    
    # 测试关键词过滤
    test_articles = [
        {
            'title': '人工智能技术突破',
            'content': '最新的AI技术在各个领域都有重大突破...',
            'url': 'https://example.com/ai-news'
        },
        {
            'title': '股市行情分析',
            'content': '今日股市表现良好，科技股领涨...',
            'url': 'https://example.com/stock-news'
        }
    ]
    
    filtered = llm_service.filter_articles_by_keywords(test_articles, "人工智能,AI")
    print(f"✅ 关键词过滤测试完成，过滤后文章数: {len(filtered)}")
    
    # 测试正则表达式生成
    regex = llm_service.generate_regex_from_samples("", ["科技新闻", "AI动态"])
    print(f"✅ 正则表达式生成测试完成: {regex}")
    
    return True

def test_notification_service():
    """测试通知服务"""
    print("\n📱 测试通知服务...")
    
    notification_service = NotificationService()
    
    # 测试消息格式化
    test_content = "# 测试报告\n\n这是一个测试报告的内容..."
    
    simple_format = notification_service.format_simple_report_for_notification(test_content)
    print(f"✅ 简单报告格式化测试完成，长度: {len(simple_format)}")
    
    deep_format = notification_service.format_deep_research_for_notification(test_content)
    print(f"✅ 深度报告格式化测试完成，长度: {len(deep_format)}")
    
    return True

async def main():
    """主测试函数"""
    print("🧪 开始系统功能测试")
    print("=" * 50)
    
    try:
        # 测试各个服务
        crawler_ok = await test_crawler_service()
        llm_ok = test_llm_service()
        notification_ok = test_notification_service()
        
        print("\n" + "=" * 50)
        print("📋 测试结果汇总:")
        print(f"   爬虫服务: {'✅ 通过' if crawler_ok else '❌ 失败'}")
        print(f"   LLM服务: {'✅ 通过' if llm_ok else '❌ 失败'}")
        print(f"   通知服务: {'✅ 通过' if notification_ok else '❌ 失败'}")
        
        if all([crawler_ok, llm_ok, notification_ok]):
            print("\n🎉 所有测试通过！系统功能正常")
            return True
        else:
            print("\n⚠️  部分测试失败，请检查相关配置")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
