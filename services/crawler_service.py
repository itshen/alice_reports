#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫服务
基于Crawl4AI实现网页内容抓取
"""

import asyncio
import re
import logging
from datetime import datetime, timedelta
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import json

# 使用标准库，避免依赖问题
try:
    from dateutil import parser as date_parser
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False

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
                        "selector": ".date, .publish-date, .article-date, time, .news-date, .post-date, .timestamp, .time, .published, .created, .article-time, .post-time, [datetime], .meta-time, .publish-time",
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
                            if data_list and isinstance(data_list, list) and len(data_list) > 0:
                                extracted_data = data_list[0]  # 取第一个匹配的结果
                        except (json.JSONDecodeError, TypeError, IndexError) as e:
                            logger.debug(f"解析提取内容失败: {e}")
                            pass
                    
                    # 清理和优化内容
                    content = extracted_data.get('content', '')
                    if not content:
                        # 如果结构化提取失败，尝试从markdown中提取纯文本内容
                        content = self._extract_clean_content_from_markdown(result.markdown)
                    else:
                        # 清理已提取的内容
                        content = self._clean_article_content(content)
                    
                    title = extracted_data.get('title', '') or (result.metadata.get('title', '') if result.metadata else '')
                    
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
    
    def _parse_publish_date(self, date_str, markdown_content="", title=""):
        """解析文章发布日期"""
        if not date_str or not date_str.strip():
            # 如果没有明确的日期，尝试从其他信息中提取
            date_str = self._extract_date_from_content(markdown_content + " " + title)
        
        if not date_str or not date_str.strip():
            return None
        
        try:
            # 清理日期字符串
            date_str = date_str.strip()
            
            # 常见的中文日期格式（优先匹配带时间的格式）
            chinese_patterns = [
                r'(\d{4})年(\d{1,2})月(\d{1,2})日[\s]*(\d{1,2}):(\d{2})',  # 2025年9月11日 08:02
                r'(\d{4})年(\d{1,2})月(\d{1,2})日',  # 2025年9月11日
                r'(\d{1,2})月(\d{1,2})日[\s]*(\d{1,2}):(\d{2})',  # 9月11日 08:02
                r'(\d{1,2})月(\d{1,2})日',  # 9月11日
                r'今天[\s]*(\d{1,2}):(\d{2})',  # 今天 08:02
                r'昨天[\s]*(\d{1,2}):(\d{2})',  # 昨天 08:02
                r'前天[\s]*(\d{1,2}):(\d{2})',  # 前天 08:02
                r'今天',
                r'昨天',
                r'前天',
                r'(\d+)小时前',
                r'(\d+)分钟前',
                r'刚刚'
            ]
            
            # 处理中文日期
            for pattern in chinese_patterns:
                match = re.search(pattern, date_str)
                if match:
                    return self._parse_chinese_date(match, pattern, date_str)
            
            # 尝试处理标准格式（保留空格，因为需要分离日期和时间）
            # 先处理带时间的格式（包含空格）
            datetime_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})[\s]+(\d{1,2}:\d{2})', date_str)
            if datetime_match:
                date_part, time_part = datetime_match.groups()
                try:
                    # 解析日期部分
                    if '-' in date_part:
                        year, month, day = map(int, date_part.split('-'))
                    else:
                        year, month, day = map(int, date_part.split('/'))
                    
                    # 解析时间部分
                    hour, minute = map(int, time_part.split(':'))
                    return datetime(year, month, day, hour, minute, 0)
                except ValueError:
                    pass
            
            # 处理不带时间的标准格式
            clean_date = re.sub(r'[^\d\-/]', '', date_str)
            
            if re.match(r'\d{4}-\d{1,2}-\d{1,2}$', clean_date):
                # 标准格式 YYYY-MM-DD
                parts = clean_date.split('-')
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                return datetime(year, month, day, 12, 0, 0)
            elif re.match(r'\d{4}/\d{1,2}/\d{1,2}$', clean_date):
                # 格式 YYYY/MM/DD
                parts = clean_date.split('/')
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                return datetime(year, month, day, 12, 0, 0)
            
            # 使用dateutil解析其他标准格式（如果可用）
            if DATEUTIL_AVAILABLE:
                try:
                    parsed_date = date_parser.parse(date_str, fuzzy=True)
                    
                    # 如果解析出的日期是未来日期，可能有误，使用当前时间
                    if parsed_date > datetime.now():
                        return datetime.now()
                    
                    return parsed_date
                except:
                    pass
            
            # 使用标准库解析常见英文格式
            english_formats = [
                '%b %d, %Y',      # Sep 11, 2025
                '%B %d, %Y',      # September 11, 2025
                '%Y-%m-%d %H:%M:%S',  # 2025-09-11 15:30:00
                '%Y-%m-%d %H:%M',     # 2025-09-11 15:30
                '%m/%d/%Y',       # 09/11/2025
                '%d/%m/%Y',       # 11/09/2025
            ]
            
            for fmt in english_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    if parsed_date > datetime.now():
                        return datetime.now()
                    return parsed_date
                except ValueError:
                    continue
            
            # 如果都无法解析，返回None
            return None
            
        except Exception as e:
            logger.debug(f"日期解析失败: {date_str}, 错误: {e}")
            return None
    
    def _extract_date_from_content(self, content):
        """从内容中提取日期信息"""
        if not content:
            return None
        
        # 常见的日期模式（包含时间）
        date_patterns = [
            r'(\d{4}年\d{1,2}月\d{1,2}日[\s]*\d{1,2}:\d{2})',  # 2025年9月11日 08:02
            r'(\d{4}年\d{1,2}月\d{1,2}日)',  # 2025年9月11日
            r'(\d{4}-\d{1,2}-\d{1,2}[\s]+\d{1,2}:\d{2}:\d{2})',  # 2025-09-11 08:02:30
            r'(\d{4}-\d{1,2}-\d{1,2}[\s]+\d{1,2}:\d{2})',  # 2025-09-11 08:02
            r'(\d{4}-\d{1,2}-\d{1,2})',  # 2025-09-11
            r'(\d{1,2}月\d{1,2}日[\s]*\d{1,2}:\d{2})',  # 9月11日 08:02
            r'(\d{1,2}月\d{1,2}日)',  # 9月11日
            r'(\d+小时前)',
            r'(\d+分钟前)',
            r'(今天|昨天|前天)',
            r'(刚刚)',
            r'发布于[\s]*(\d{4}-\d{1,2}-\d{1,2}[\s]*\d{1,2}:\d{2})',
            r'时间[:：][\s]*(\d{4}-\d{1,2}-\d{1,2}[\s]*\d{1,2}:\d{2})',
            r'(\d{4}/\d{1,2}/\d{1,2}[\s]+\d{1,2}:\d{2})',  # 2025/09/11 08:02
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return None
    
    def _parse_chinese_date(self, match, pattern, original_str):
        """解析中文日期格式"""
        try:
            now = datetime.now()
            groups = match.groups()
            
            # 带时间的今天/昨天/前天
            if '今天' in original_str and len(groups) >= 2:
                hour, minute = int(groups[-2]), int(groups[-1])
                return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            elif '昨天' in original_str and len(groups) >= 2:
                hour, minute = int(groups[-2]), int(groups[-1])
                return (now - timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
            elif '前天' in original_str and len(groups) >= 2:
                hour, minute = int(groups[-2]), int(groups[-1])
                return (now - timedelta(days=2)).replace(hour=hour, minute=minute, second=0, microsecond=0)
            # 不带时间的今天/昨天/前天
            elif '今天' in original_str:
                return now.replace(hour=12, minute=0, second=0, microsecond=0)
            elif '昨天' in original_str:
                return (now - timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
            elif '前天' in original_str:
                return (now - timedelta(days=2)).replace(hour=12, minute=0, second=0, microsecond=0)
            elif '小时前' in original_str:
                hours = int(match.group(1))
                return now - timedelta(hours=hours)
            elif '分钟前' in original_str:
                minutes = int(match.group(1))
                return now - timedelta(minutes=minutes)
            elif '刚刚' in original_str:
                return now - timedelta(minutes=5)
            # 带时间的完整日期：2025年9月11日 08:02
            elif '年' in pattern and '月' in pattern and '日' in pattern and len(groups) >= 5:
                year, month, day, hour, minute = int(groups[0]), int(groups[1]), int(groups[2]), int(groups[3]), int(groups[4])
                return datetime(year, month, day, hour, minute, 0)
            # 带时间的月日：9月11日 08:02
            elif '月' in pattern and '日' in pattern and len(groups) >= 4:
                month, day, hour, minute = int(groups[0]), int(groups[1]), int(groups[2]), int(groups[3])
                return datetime(now.year, month, day, hour, minute, 0)
            # 不带时间的完整日期：2025年9月11日
            elif '年' in pattern and '月' in pattern and '日' in pattern:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
                return datetime(year, month, day, 12, 0, 0)
            # 不带时间的月日：9月11日
            elif '月' in pattern and '日' in pattern:
                month = int(match.group(1))
                day = int(match.group(2))
                return datetime(now.year, month, day, 12, 0, 0)
            
        except Exception as e:
            logger.debug(f"中文日期解析失败: {original_str}, 错误: {e}")
        
        return None
    
    async def run_crawler_task(self, crawler_config):
        """执行爬虫任务"""
        try:
            # 导入数据库相关模块（避免循环导入）
            from models import db
            
            logger.info(f"开始执行爬虫任务: {crawler_config.name}")
            
            # 1. 从列表页提取URL
            urls = await self.extract_urls_from_page(
                crawler_config.list_url, 
                crawler_config.url_regex
            )
            
            if not urls:
                logger.warning(f"爬虫 {crawler_config.name} 未找到任何URL")
                
                # 即使没有找到URL也要更新最后运行时间
                try:
                    crawler_config.last_run = datetime.utcnow()
                    db.session.commit()
                    logger.info(f"✅ 已更新爬虫 {crawler_config.name} 的最后运行时间（未找到URL）")
                except Exception as e:
                    logger.error(f"更新last_run时间失败: {e}")
                    db.session.rollback()
                
                return {
                    'success': True,
                    'saved_count': 0,
                    'failed_count': 0,
                    'total_processed': 0
                }
            
            logger.info(f"爬虫 {crawler_config.name} 找到 {len(urls)} 个URL")
            
            # 2. 过滤已存在的URL，避免重复爬取
            new_urls = await self._filter_new_urls(urls, crawler_config.id)
            
            if not new_urls:
                logger.info(f"爬虫 {crawler_config.name} 所有URL都已存在，跳过爬取")
                
                # 即使没有新URL也要更新最后运行时间
                try:
                    crawler_config.last_run = datetime.utcnow()
                    db.session.commit()
                    logger.info(f"✅ 已更新爬虫 {crawler_config.name} 的最后运行时间（无新URL）")
                except Exception as e:
                    logger.error(f"更新last_run时间失败: {e}")
                    db.session.rollback()
                
                return {
                    'success': True,
                    'saved_count': 0,
                    'failed_count': 0,
                    'total_processed': 0
                }
            
            logger.info(f"爬虫 {crawler_config.name} 过滤后需要爬取 {len(new_urls)} 个新URL")
            
            # 3. 逐个抓取文章内容并立即保存（带重试机制）
            saved_count = 0
            failed_count = 0
            base_delay = 1.0  # 基础延迟
            
            for i, url in enumerate(new_urls[:20]):  # 限制每次最多抓取20篇文章
                logger.info(f"正在爬取第 {i+1}/{min(len(new_urls), 20)} 篇文章")
                
                # 带重试的抓取
                result = await self._crawl_with_retry(url, max_retries=3)
                
                # 立即保存到数据库
                save_success = await self._save_single_result(result, crawler_config)
                if save_success:
                    saved_count += 1
                    # 成功时使用基础延迟
                    delay = base_delay
                else:
                    failed_count += 1
                    # 失败时增加延迟
                    delay = base_delay * 2
                
                # 动态延迟避免被封
                logger.debug(f"等待 {delay:.1f} 秒后继续...")
                await asyncio.sleep(delay)
            
            logger.info(f"爬虫 {crawler_config.name} 完成，成功保存 {saved_count} 篇文章，失败 {failed_count} 篇")
            
            # 更新爬虫最后运行时间
            try:
                crawler_config.last_run = datetime.utcnow()
                db.session.commit()
                logger.info(f"✅ 已更新爬虫 {crawler_config.name} 的最后运行时间")
            except Exception as e:
                logger.error(f"更新last_run时间失败: {e}")
                db.session.rollback()
            
            # 返回统计信息而不是具体结果
            return {
                'success': True,
                'saved_count': saved_count,
                'failed_count': failed_count,
                'total_processed': saved_count + failed_count
            }
        
        except Exception as e:
            logger.error(f"执行爬虫任务失败 {crawler_config.name}: {e}")
            
            # 即使失败也要更新最后运行时间
            try:
                crawler_config.last_run = datetime.utcnow()
                db.session.commit()
                logger.info(f"✅ 已更新爬虫 {crawler_config.name} 的最后运行时间（任务失败）")
            except Exception as update_error:
                logger.error(f"更新last_run时间失败: {update_error}")
                db.session.rollback()
            
            return []
    
    async def _crawl_with_retry(self, url, max_retries=3):
        """带重试机制的文章抓取"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # 重试时增加延迟（指数退避）
                    retry_delay = (2 ** attempt) * 1.0  # 1秒, 2秒, 4秒
                    logger.info(f"第 {attempt + 1} 次重试 {url}，等待 {retry_delay:.1f} 秒...")
                    await asyncio.sleep(retry_delay)
                
                result = await self.crawl_article_content(url)
                
                # 如果成功，直接返回
                if result['success']:
                    if attempt > 0:
                        logger.info(f"✅ 重试成功: {url}")
                    return result
                else:
                    # 如果失败，记录错误并继续重试
                    last_error = result.get('error', 'Unknown error')
                    logger.warning(f"第 {attempt + 1} 次尝试失败: {last_error}")
                    
            except Exception as e:
                last_error = str(e)
                logger.warning(f"第 {attempt + 1} 次尝试异常: {e}")
        
        # 所有重试都失败了
        logger.error(f"❌ {max_retries} 次重试后仍然失败: {url}, 最后错误: {last_error}")
        return {
            'success': False,
            'url': url,
            'error': f"重试 {max_retries} 次后失败: {last_error}"
        }
    
    async def _save_single_result(self, result, crawler_config):
        """立即保存单条爬取结果到数据库"""
        try:
            # 导入模型（避免循环导入）
            from models import CrawlRecord, db
            from app import app
            from datetime import datetime
            
            with app.app_context():
                # 再次检查URL是否已存在（防止并发问题）
                existing = CrawlRecord.query.filter_by(
                    url=result['url'], 
                    status='success'
                ).first()
                
                if existing:
                    logger.info(f"URL已存在，跳过保存: {result['url']}")
                    return True  # 算作成功，因为数据已存在
                
                if result['success']:
                    # 解析发布日期
                    publish_date = self._parse_publish_date(
                        result.get('date', ''),
                        result.get('markdown', ''),
                        result.get('title', '')
                    )
                    
                    record = CrawlRecord(
                        crawler_config_id=crawler_config.id,
                        url=result['url'],
                        title=result.get('title', ''),
                        content=result.get('content', ''),
                        author=result.get('author', ''),
                        publish_date=publish_date,  # 使用解析出的发布日期
                        crawled_at=datetime.utcnow(),  # 爬取时间
                        status='success'
                    )
                    
                    date_info = publish_date.strftime('%Y-%m-%d %H:%M') if publish_date else '未知'
                    logger.info(f"✅ 保存成功记录 [发布:{date_info}]: {result.get('title', result['url'])[:50]}...")
                else:
                    record = CrawlRecord(
                        crawler_config_id=crawler_config.id,
                        url=result['url'],
                        crawled_at=datetime.utcnow(),
                        status='failed',
                        error_message=result.get('error', '')
                    )
                    logger.info(f"❌ 保存失败记录: {result['url'][:60]}... - {result.get('error', 'Unknown error')}")
                
                db.session.add(record)
                
                # 立即提交这条记录
                db.session.commit()
                logger.debug(f"💾 单条记录已提交到数据库")
                
                return True
                
        except Exception as e:
            logger.error(f"保存单条记录失败: {e}, URL: {result.get('url', 'Unknown')}")
            # 回滚这次操作
            try:
                from app import app
                with app.app_context():
                    db.session.rollback()
            except:
                pass
            return False
    
    async def _filter_new_urls(self, urls, crawler_config_id):
        """过滤出新的URL，避免重复爬取"""
        try:
            # 导入CrawlRecord模型（避免循环导入）
            from models import CrawlRecord
            
            new_urls = []
            for url in urls:
                # 检查URL是否已存在于数据库中
                existing = CrawlRecord.query.filter_by(
                    url=url,
                    status='success'
                ).first()
                
                if not existing:
                    new_urls.append(url)
                else:
                    logger.debug(f"URL已存在，跳过: {url}")
            
            logger.info(f"URL过滤完成: 总共 {len(urls)} 个，新增 {len(new_urls)} 个，已存在 {len(urls) - len(new_urls)} 个")
            return new_urls
            
        except Exception as e:
            logger.error(f"过滤URL失败: {e}")
            # 如果过滤失败，返回原始URL列表，确保爬虫能继续工作
            return urls
    
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
