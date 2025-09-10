#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI指导的深度研究流程
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from services.deep_research_service import DeepResearchService
from services.crawler_service import CrawlerService
from services.llm_service import LLMService
from models import GlobalSettings, ReportConfig, CrawlerConfig, CrawlRecord
from datetime import datetime, timedelta

def create_mock_report_config():
    """创建模拟报告配置"""
    class MockReportConfig:
        def __init__(self):
            self.name = "AI技术发展趋势研究"
            self.purpose = "分析AI技术在2025年的发展趋势和机遇"
            self.research_focus = "重点关注大模型技术、多模态AI、AI应用落地"
            self.filter_keywords = "AI,人工智能,大模型,机器学习"
            self.time_range = "最近7天"
            self.data_sources = [1, 2]  # 假设的爬虫ID
    
    return MockReportConfig()

def create_mock_knowledge_base():
    """创建模拟知识库数据"""
    return [
        {
            'title': 'OpenAI发布GPT-5预览版，性能大幅提升',
            'content': 'OpenAI近日发布了GPT-5的预览版本，在推理能力、多模态理解等方面都有显著提升。新模型在数学、编程、科学推理等任务上的表现比GPT-4提升了30%以上...',
            'url': 'https://example.com/gpt5-preview',
            'source': 'TechCrunch',
            'date': '2025-01-15',
            'crawled_at': '2025-01-15T10:00:00'
        },
        {
            'title': '谷歌Gemini 2.0正式发布，支持实时推理',
            'content': '谷歌发布了Gemini 2.0模型，新增了实时推理能力，可以在对话过程中动态调整回答策略。该模型在多轮对话和复杂任务处理方面表现出色...',
            'url': 'https://example.com/gemini-2-0',
            'source': 'Google AI Blog',
            'date': '2025-01-14',
            'crawled_at': '2025-01-14T15:30:00'
        },
        {
            'title': '百度文心大模型4.0在企业应用中的实践',
            'content': '百度文心大模型4.0在金融、医疗、教育等多个行业得到广泛应用。相比3.5版本，新版本在专业领域的准确性提升了25%，推理速度提升40%...',
            'url': 'https://example.com/wenxin-4-0',
            'source': '百度AI',
            'date': '2025-01-13',
            'crawled_at': '2025-01-13T09:15:00'
        },
        {
            'title': 'AI芯片市场2025年预测：英伟达依然领先',
            'content': '分析报告显示，2025年AI芯片市场预计增长45%。英伟达H100和即将发布的H200芯片继续占据市场主导地位，但华为、寒武纪等中国厂商快速追赶...',
            'url': 'https://example.com/ai-chip-market',
            'source': 'IDC Research',
            'date': '2025-01-12',
            'crawled_at': '2025-01-12T14:20:00'
        },
        {
            'title': 'Meta发布Llama 3.5，开源模型新突破',
            'content': 'Meta发布了开源大模型Llama 3.5，在保持开源特性的同时，性能接近GPT-4水平。这一发布将进一步推动开源AI生态的发展...',
            'url': 'https://example.com/llama-3-5',
            'source': 'Meta AI',
            'date': '2025-01-11',
            'crawled_at': '2025-01-11T11:45:00'
        }
    ]

async def test_initial_analysis():
    """测试AI初步分析功能"""
    print("🧠 测试AI初步分析功能")
    print("="*50)
    
    try:
        # 创建服务实例
        crawler_service = CrawlerService()
        llm_service = LLMService()
        deep_research_service = DeepResearchService(crawler_service, llm_service)
        
        # 模拟数据
        mock_config = create_mock_report_config()
        mock_knowledge = create_mock_knowledge_base()
        
        print(f"📚 模拟知识库: {len(mock_knowledge)} 篇文章")
        for i, article in enumerate(mock_knowledge, 1):
            print(f"  {i}. {article['title'][:60]}...")
        
        print(f"\n🎯 研究配置:")
        print(f"  主题: {mock_config.purpose}")
        print(f"  侧重点: {mock_config.research_focus}")
        print(f"  关键词: {mock_config.filter_keywords}")
        
        # 执行AI初步分析
        print(f"\n🤖 开始AI初步分析...")
        analysis_result = await deep_research_service._ai_initial_analysis(mock_knowledge, mock_config)
        
        print(f"✅ 分析完成！")
        print(f"\n📊 分析结果:")
        print(f"现有知识摘要: {analysis_result.get('summary', '无')}")
        print(f"\n🔍 知识空白: {analysis_result.get('gaps', '无')}")
        print(f"\n🎯 研究方向:")
        for i, direction in enumerate(analysis_result.get('directions', []), 1):
            print(f"  {i}. {direction}")
        print(f"\n🔑 优先关键词: {', '.join(analysis_result.get('keywords', []))}")
        
        return analysis_result
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return None

async def test_research_decision():
    """测试AI研究决策功能"""
    print("\n" + "="*60)
    print("🎯 测试AI研究决策功能")
    print("="*50)
    
    try:
        # 创建服务实例
        crawler_service = CrawlerService()
        llm_service = LLMService()
        deep_research_service = DeepResearchService(crawler_service, llm_service)
        
        # 模拟数据
        mock_config = create_mock_report_config()
        mock_knowledge = create_mock_knowledge_base()
        
        # 模拟初步分析结果
        mock_analysis = {
            'summary': '现有文章主要覆盖了大模型技术发展、主要厂商动态、芯片市场等方面',
            'gaps': '缺乏具体的技术细节、商业化程度分析、用户体验评估等深度内容',
            'directions': [
                '深入分析GPT-5的技术突破点和应用场景',
                '调研企业级AI应用的实际落地效果',
                '分析AI芯片技术发展对整体行业的影响'
            ],
            'keywords': ['GPT-5技术细节', 'AI企业应用案例', 'AI芯片技术发展']
        }
        
        print(f"📋 使用模拟的初步分析结果:")
        print(f"  现有知识: {mock_analysis['summary']}")
        print(f"  知识空白: {mock_analysis['gaps']}")
        print(f"  建议关键词: {', '.join(mock_analysis['keywords'])}")
        
        # 测试多轮决策
        for iteration in range(1, 4):
            print(f"\n🔄 第 {iteration} 轮研究决策...")
            
            decision = await deep_research_service._send_guided_research_prompt(
                mock_knowledge, mock_config, mock_analysis, iteration
            )
            
            print(f"  AI决策: {decision.get('action', '未知')}")
            print(f"  原因: {decision.get('details', '无')}")
            
            if decision.get('action') == 'search':
                keywords = decision.get('keywords', [])
                print(f"  搜索关键词: {', '.join(keywords)}")
            elif decision.get('action') == 'finish':
                print(f"  AI决定结束研究")
                break
            
            # 模拟添加新文章到知识库
            if decision.get('action') == 'search':
                mock_knowledge.append({
                    'title': f'第{iteration}轮搜索获得的新文章',
                    'content': f'基于关键词{decision.get("keywords", [])}搜索到的相关内容...',
                    'url': f'https://example.com/search-result-{iteration}',
                    'source': f'搜索来源-{iteration}',
                    'date': '2025-01-16',
                    'crawled_at': '2025-01-16T12:00:00'
                })
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

async def test_filter_and_analysis():
    """测试关键词过滤和分析组合"""
    print("\n" + "="*60)
    print("🔍 测试关键词过滤和AI分析组合")
    print("="*50)
    
    try:
        # 创建服务实例
        crawler_service = CrawlerService()
        llm_service = LLMService()
        
        # 准备测试数据
        all_articles = create_mock_knowledge_base()
        
        # 添加一些不相关的文章
        all_articles.extend([
            {
                'title': '今日股市行情分析',
                'content': '今日A股市场表现平稳，沪深300指数微跌0.2%...',
                'url': 'https://example.com/stock-market',
                'source': '财经网',
                'date': '2025-01-15'
            },
            {
                'title': '新能源汽车销量创新高',
                'content': '2024年新能源汽车销量突破800万辆，同比增长35%...',
                'url': 'https://example.com/ev-sales',
                'source': '汽车之家',
                'date': '2025-01-14'
            }
        ])
        
        print(f"📚 原始文章数: {len(all_articles)}")
        for i, article in enumerate(all_articles, 1):
            print(f"  {i}. {article['title'][:50]}...")
        
        # 测试关键词过滤
        filter_keywords = "AI,人工智能,大模型,机器学习"
        print(f"\n🔍 使用关键词过滤: {filter_keywords}")
        
        filtered_articles = llm_service.filter_articles_by_keywords(all_articles, filter_keywords)
        
        print(f"✅ 过滤后文章数: {len(filtered_articles)}")
        for i, article in enumerate(filtered_articles, 1):
            print(f"  {i}. {article['title'][:50]}...")
        
        return len(filtered_articles) > 0
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 AI指导深度研究流程测试")
    print("="*60)
    
    try:
        # 测试关键词过滤
        filter_success = await test_filter_and_analysis()
        
        # 测试AI初步分析
        analysis_result = await test_initial_analysis()
        analysis_success = analysis_result is not None
        
        # 测试AI研究决策
        decision_success = await test_research_decision()
        
        print("\n" + "="*60)
        print("📋 测试结果汇总:")
        print(f"   关键词过滤: {'✅ 通过' if filter_success else '❌ 失败'}")
        print(f"   AI初步分析: {'✅ 通过' if analysis_success else '❌ 失败'}")
        print(f"   AI研究决策: {'✅ 通过' if decision_success else '❌ 失败'}")
        
        if all([filter_success, analysis_success, decision_success]):
            print("\n🎉 AI指导研究流程测试全部通过！")
            print("💡 新流程特点:")
            print("   1. 📊 从数据库获取最近爬到的内容")
            print("   2. 🔍 根据用户关键词进行智能过滤")
            print("   3. 🧠 AI深度分析现有知识，识别空白")
            print("   4. 🎯 AI制定有针对性的研究计划")
            print("   5. 🔄 基于分析结果进行迭代搜索")
            print("   6. 📝 生成基于充分研究的高质量报告")
            return True
        else:
            print("\n⚠️ 部分测试失败，请检查相关功能")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    with app.app_context():
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
