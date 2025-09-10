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
            # 设置5秒超时
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await asyncio.wait_for(
                    crawler.arun(url=url), 
                    timeout=5.0
                )
                
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
        
        except asyncio.TimeoutError:
            logger.error(f"连接超时: {url}")
            return {
                'success': False,
                'error': f'连接超时（5秒）: {url}'
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
            logger.info(f"开始提取URL from: {url}")
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await asyncio.wait_for(
                    crawler.arun(url=url), 
                    timeout=5.0
                )
                
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
        
        except asyncio.TimeoutError:
            logger.error(f"提取URL超时: {url}")
            return []
        except Exception as e:
            logger.error(f"提取URL失败: {e}")
            return []
    
    async def crawl_article_content(self, url):
        """抓取文章详细内容"""
        try:
            logger.info(f"开始爬取文章内容: {url}")
            
            # 统一设置5秒超时
            timeout = 5.0
            logger.info(f"设置超时时间: {timeout}秒")
            
            # 定义更精确的文章内容提取策略
            schema = {
                "name": "文章内容",
                "baseSelector": "article, .article, .content, .post, main, .article-content, .news-content, .post-body",
                "fields": [
                    {
                        "name": "title",
                        "selector": "h1, h2, .title, .headline, .article-title, .news-title, .post-title",
                        "type": "text"
                    },
                    {
                        "name": "content",
                        "selector": ".content, .article-body, .post-content, .news-body, .article-text, .main-content, .entry-content",
                        "type": "text"
                    },
                    {
                        "name": "author",
                        "selector": ".author, .byline, .writer, .article-author, .news-author",
                        "type": "text"
                    },
                    {
                        "name": "date",
                        "selector": ".date, .publish-date, .article-date, time, .news-date, .post-date",
                        "type": "text"
                    }
                ]
            }
            
            extraction_strategy = JsonCssExtractionStrategy(schema, verbose=False)
            
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await asyncio.wait_for(
                    crawler.arun(
                        url=url,
                        extraction_strategy=extraction_strategy,
                        # 移除更多不需要的元素
                        excluded_tags=[
                            'nav', 'footer', 'aside', 'script', 'style', 'header', 
                            'menu', 'sidebar', 'advertisement', 'ad', 'banner',
                            'breadcrumb', 'pagination', 'related', 'comment',
                            'social', 'share', 'widget', 'toolbar'
                        ],
                        # 等待页面加载
                        wait_for="body"
                    ),
                    timeout=timeout  # 根据域名动态设置超时时间
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
                    
                    # 清理和优化内容
                    content = extracted_data.get('content', '')
                    if not content:
                        # 如果结构化提取失败，尝试从markdown中提取纯文本内容
                        content = self._extract_clean_content_from_markdown(result.markdown)
                    else:
                        # 清理已提取的内容
                        content = self._clean_article_content(content)
                    
                    title = extracted_data.get('title', '') or result.metadata.get('title', '')
                    
                    logger.info(f"成功爬取文章: {title[:50]}...")
                    return {
                        'success': True,
                        'url': url,
                        'title': title,
                        'content': content,
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
        
        except asyncio.TimeoutError:
            logger.error(f"抓取文章内容超时 {url}")
            return {
                'success': False,
                'url': url,
                'error': f'抓取超时（5秒）: {url}'
            }
        except Exception as e:
            logger.error(f"抓取文章内容失败 {url}: {e}")
            return {
                'success': False,
                'url': url,
                'error': str(e)
            }
    
    def _clean_article_content(self, content):
        """清理文章内容，移除不相关信息"""
        if not content:
            return ""
        
        # 移除常见的导航和无关内容
        unwanted_patterns = [
            r'首页.*?网站地图',  # 导航菜单
            r'网站地图.*?地方频道',  # 网站导航
            r'地方频道.*?多语种频道',  # 地方频道列表
            r'多语种频道.*?新华报刊',  # 多语种导航
            r'新华报刊.*?承建网站',  # 报刊列表
            r'承建网站.*?客户端',  # 承建网站列表
            r'手机版.*?站内搜索',  # 移动版导航
            r'Copyright.*?All Rights Reserved',  # 版权信息
            r'制作单位：.*?版权所有：.*?',  # 版权信息
            r'\[.*?\]',  # 方括号内容（通常是链接文本）
            r'javascript:void\([^)]*\)',  # JavaScript链接
            r'https?://[^\s]+',  # 清理残留的URL
            r'_[^_]*_',  # 下划线包围的内容
            r'![^!]*!',  # 感叹号包围的内容
            r'网站无障碍',  # 无障碍链接
            r'PC版本',  # 版本切换
            r'客户端',  # 客户端下载
            r'字体：\s*小\s*中\s*大',  # 字体大小选择
            r'分享到：.*?\)',  # 分享按钮
            r'\([^)]*javascript[^)]*\)',  # 包含javascript的括号内容
            r'来源：[^\n]*\n',  # 来源信息（保留但不重复）
            r'^\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2}',  # 时间戳
        ]
        
        cleaned_content = content
        for pattern in unwanted_patterns:
            cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.IGNORECASE | re.DOTALL)
        
        # 清理多余的空白字符
        cleaned_content = re.sub(r'\n\s*\n', '\n\n', cleaned_content)  # 合并多个空行
        cleaned_content = re.sub(r'[ \t]+', ' ', cleaned_content)  # 合并多个空格
        cleaned_content = cleaned_content.strip()
        
        return cleaned_content
    
    def _extract_clean_content_from_markdown(self, markdown):
        """从markdown中提取干净的文章内容"""
        if not markdown:
            return ""
        
        # 分步骤清理内容
        content = markdown
        
        # 1. 移除大块的导航区域（使用更精确的模式）
        navigation_patterns = [
            r'!\[.*?\]\([^)]*\).*?手机版.*?网站地图.*?地方频道.*?多语种频道.*?新华报刊.*?承建网站.*?客户端',  # 完整导航块（包含图片）
            r'手机版.*?站内搜索.*?新华通讯社主办',  # 移动版导航到主办方
            r'Copyright.*?All Rights Reserved.*?制作单位：.*?版权所有：[^\n]*',  # 版权信息块
            r'\[.*?\]\([^)]*\)\s*\*\s*\[.*?\]\([^)]*\)\s*\*.*?地方频道',  # 链接列表模式
            r'地方频道\s*\*.*?多语种频道',  # 地方频道列表
            r'多语种频道\s*\*.*?新华报刊',  # 多语种频道列表
            r'新华报刊\s*\[.*?\].*?承建网站',  # 报刊列表
            r'承建网站\s*\[.*?\].*?客户端',  # 承建网站列表
        ]
        
        for pattern in navigation_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # 2. 移除小的无关元素
        small_unwanted_patterns = [
            r'javascript:void\([^)]*\)',  # JavaScript链接
            r'字体：\s*小\s*中\s*大',  # 字体大小选择
            r'分享到：[^#\n]*',  # 分享按钮（但保留#标题）
            r'\([^)]*javascript[^)]*\)',  # 包含javascript的括号内容
            r'网站无障碍',  # 无障碍链接
            r'PC版本',  # 版本切换
            r'!\[.*?\]\([^)]*\)',  # Markdown图片链接
            r'https?://[^\s\)]+',  # 清理残留的URL（但不在括号内的）
            r'\[.*?\]\([^)]*\)\s*\*\s*',  # 链接后的星号
            r'\*\s*\[.*?\]\([^)]*\)',  # 星号开头的链接
            r'^\s*\*\s*.*?$',  # 以星号开头的行（通常是导航项）
            r'^\s*\[.*?\]\([^)]*\)\s*$',  # 单独的链接行
        ]
        
        for pattern in small_unwanted_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # 3. 智能提取文章主体
        lines = content.split('\n')
        
        # 找到文章标题（通常是#开头或包含关键词）
        title_idx = -1
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('#') and ('新华网' in line or '评' in line or len(line) > 15):
                title_idx = i
                break
        
        # 如果找到标题，从标题开始提取
        if title_idx >= 0:
            start_idx = title_idx
        else:
            # 否则找到第一个看起来像正文的行
            start_idx = 0
            for i, line in enumerate(lines):
                line = line.strip()
                if (line and len(line) > 20 and 
                    not any(keyword in line.lower() for keyword in [
                        '首页', '导航', '菜单', '登录', '注册', '搜索', '网站地图'
                    ]) and
                    ('新华网' in line or '记者' in line or line.endswith('电') or '日' in line)):
                    start_idx = i
                    break
        
        # 找到文章结束位置
        end_idx = len(lines)
        for i in range(start_idx + 1, len(lines)):
            line = lines[i].strip()
            if any(keyword in line.lower() for keyword in [
                'copyright', '版权所有', '制作单位', '责任编辑', '纠错'
            ]):
                end_idx = i
                break
        
        # 提取文章主体
        article_lines = lines[start_idx:end_idx]
        article_content = '\n'.join(article_lines).strip()
        
        # 4. 最后清理
        article_content = re.sub(r'\n{3,}', '\n\n', article_content)  # 限制连续空行
        article_content = re.sub(r'[ \t]+', ' ', article_content)  # 合并多个空格
        
        return article_content
    
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
            for i, url in enumerate(urls[:20]):  # 限制每次最多抓取20篇文章
                logger.info(f"正在爬取第 {i+1}/{min(len(urls), 20)} 篇文章")
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
            return r'([^"]*\.html?[^"]*)"'
        
        # 分析样本标题，尝试找到共同模式
        # 这是一个简化的实现，实际可以使用LLM来生成更智能的正则
        
        # 常见的文章链接模式
        patterns = [
            r'([^"]*article[^"]*)"',
            r'([^"]*news[^"]*)"',
            r'([^"]*post[^"]*)"',
            r'([^"]*\.html[^"]*)"',
            r'"(/[^"]*\d{4}[^"]*)"'  # 包含年份的链接
        ]
        
        # 返回第一个模式作为默认
        return patterns[0]
