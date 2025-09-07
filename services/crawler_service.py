#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫服务
基于Crawl4AI实现网页内容抓取
"""

import asyncio
import re
import logging
from datetime import datetime
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import json

logger = logging.getLogger(__name__)

class CrawlerService:
    """爬虫服务类"""
    
    def __init__(self):
        self.crawler = None
    
    async def test_connection(self, url):
        """测试连接并返回页面内容"""
        try:
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(url=url)
                
                if result.success:
                    # 提取页面中的所有链接
                    links = []
                    if result.links:
                        internal_links = result.links.get('internal', [])
                        external_links = result.links.get('external', [])
                        links = internal_links + external_links
                    
                    return {
                        'success': True,
                        'content': result.markdown,  # 返回markdown内容用于正则表达式匹配（恢复原逻辑）
                        'links': links[:100],  # 限制链接数量
                        'title': result.metadata.get('title', ''),
                        'html': result.html[:10000]  # 限制HTML长度
                    }
                else:
                    return {
                        'success': False,
                        'error': result.error_message or '连接失败'
                    }
        
        except Exception as e:
            logger.error(f"测试连接失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def extract_urls_from_page(self, url, regex_pattern):
        """从页面提取URL列表"""
        try:
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(url=url)
                
                if not result.success:
                    return []
                
                # 使用正则表达式在markdown中匹配URL（恢复原逻辑）
                pattern = re.compile(regex_pattern)
                matches = pattern.findall(result.markdown)
                
                # 调试日志
                logger.info(f"正则表达式: {regex_pattern}")
                logger.info(f"Markdown内容长度: {len(result.markdown)}")
                logger.info(f"匹配到的URL数量: {len(matches)}")
                if matches:
                    logger.info(f"前3个匹配的URL: {matches[:3]}")
                
                # 去重并返回
                unique_matches = list(set(matches))
                logger.info(f"去重后URL数量: {len(unique_matches)}")
                return unique_matches
        
        except Exception as e:
            logger.error(f"提取URL失败: {e}")
            return []
    
    async def crawl_article_content(self, url):
        """抓取文章详细内容"""
        try:
            # 定义文章内容提取策略
            schema = {
                "name": "文章内容",
                "baseSelector": "article, .article, .content, .post, main",
                "fields": [
                    {
                        "name": "title",
                        "selector": "h1, h2, .title, .headline, .article-title",
                        "type": "text"
                    },
                    {
                        "name": "content",
                        "selector": ".content, .article-body, .post-content, p",
                        "type": "text"
                    },
                    {
                        "name": "author",
                        "selector": ".author, .byline, .writer, .article-author",
                        "type": "text"
                    },
                    {
                        "name": "date",
                        "selector": ".date, .publish-date, .article-date, time",
                        "type": "text"
                    }
                ]
            }
            
            extraction_strategy = JsonCssExtractionStrategy(schema, verbose=False)
            
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(
                    url=url,
                    extraction_strategy=extraction_strategy,
                    # 移除不需要的元素
                    excluded_tags=['nav', 'footer', 'aside', 'script', 'style', 'header'],
                    # 等待页面加载
                    wait_for="body"
                )
                
                if result.success:
                    # 解析提取的结构化数据
                    extracted_data = {}
                    if result.extracted_content:
                        try:
                            data_list = json.loads(result.extracted_content)
                            if data_list and len(data_list) > 0:
                                extracted_data = data_list[0]  # 取第一个匹配的结果
                        except json.JSONDecodeError:
                            pass
                    
                    # 如果结构化提取失败，使用markdown内容
                    if not extracted_data.get('content'):
                        extracted_data['content'] = result.markdown
                    
                    if not extracted_data.get('title'):
                        extracted_data['title'] = result.metadata.get('title', '')
                    
                    return {
                        'success': True,
                        'url': url,
                        'title': extracted_data.get('title', ''),
                        'content': extracted_data.get('content', ''),
                        'author': extracted_data.get('author', ''),
                        'date': extracted_data.get('date', ''),
                        'markdown': result.markdown
                    }
                else:
                    return {
                        'success': False,
                        'url': url,
                        'error': result.error_message or '抓取失败'
                    }
        
        except Exception as e:
            logger.error(f"抓取文章内容失败 {url}: {e}")
            return {
                'success': False,
                'url': url,
                'error': str(e)
            }
    
    async def run_crawler_task(self, crawler_config):
        """执行爬虫任务"""
        try:
            logger.info(f"开始执行爬虫任务: {crawler_config.name}")
            
            # 1. 从列表页提取URL
            urls = await self.extract_urls_from_page(
                crawler_config.list_url, 
                crawler_config.url_regex
            )
            
            if not urls:
                logger.warning(f"爬虫 {crawler_config.name} 未找到任何URL")
                return []
            
            logger.info(f"爬虫 {crawler_config.name} 找到 {len(urls)} 个URL")
            
            # 2. 批量抓取文章内容
            results = []
            for url in urls[:20]:  # 限制每次最多抓取20篇文章
                result = await self.crawl_article_content(url)
                results.append(result)
                
                # 添加延迟避免被封
                await asyncio.sleep(1)
            
            logger.info(f"爬虫 {crawler_config.name} 完成，成功抓取 {len([r for r in results if r['success']])} 篇文章")
            
            return results
        
        except Exception as e:
            logger.error(f"执行爬虫任务失败 {crawler_config.name}: {e}")
            return []
    
    def generate_regex_with_ai(self, page_content, sample_titles):
        """使用AI生成正则表达式（占位符实现）"""
        # 这里可以集成LLM来智能生成正则表达式
        # 目前提供一个简单的实现
        
        # 基于样本标题生成简单的正则表达式
        if not sample_titles:
            return r'href="([^"]*\.html?[^"]*)"'
        
        # 分析样本标题，尝试找到共同模式
        # 这是一个简化的实现，实际可以使用LLM来生成更智能的正则
        
        # 常见的文章链接模式
        patterns = [
            r'href="([^"]*article[^"]*)"',
            r'href="([^"]*news[^"]*)"',
            r'href="([^"]*post[^"]*)"',
            r'href="([^"]*\.html[^"]*)"',
            r'href="(/[^"]*\d{4}[^"]*)"'  # 包含年份的链接
        ]
        
        # 返回第一个模式作为默认
        return patterns[0]
