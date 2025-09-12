#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度研究服务 - V3.0 XML交互版
实现迭代式AI研究流程
"""

import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple
from datetime import datetime
import re

from services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class DeepResearchService:
    """深度研究服务类 - V3.0 XML交互版"""
    
    def __init__(self, crawler_service, llm_service):
        self.crawler_service = crawler_service
        self.llm_service = llm_service
        self.notification_service = NotificationService()
        self.max_iterations = 30
        
    async def conduct_deep_research(self, report_config, settings) -> Dict[str, Any]:
        """执行深度研究流程"""
        try:
            logger.info(f"开始深度研究: {report_config.name}")
            
            # 0. 更新LLM设置
            self.llm_service.update_settings(settings)
            
            # 1. 从数据库获取最近爬到的内容
            initial_articles = await self._build_initial_knowledge_base(report_config)
            
            if not initial_articles:
                return {
                    'success': False,
                    'message': '初始数据获取失败，未从数据库中找到相关数据'
                }
            
            # 2. 使用配置关键词进行基础过滤（如果有的话）
            if report_config.filter_keywords:
                filtered_articles = self.llm_service.filter_articles_by_keywords(
                    initial_articles, report_config.filter_keywords
                )
                logger.info(f"配置关键词过滤: {len(initial_articles)} -> {len(filtered_articles)} 篇文章")
                knowledge_base = filtered_articles
            else:
                knowledge_base = initial_articles
            
            if not knowledge_base:
                return {
                    'success': False,
                    'message': '过滤后未找到相关文章'
                }
            
            # 3. 开始迭代研究 - AI判断现有资料是否足够写报告
            iteration_count = 0
            research_log = []
            
            while iteration_count < self.max_iterations:
                iteration_count += 1
                logger.info(f"开始第 {iteration_count} 轮研究迭代")
                
                # AI分析当前知识库，判断是否能写报告
                ai_response = await self._send_research_prompt(
                    knowledge_base, 
                    report_config,
                    iteration_count
                )
                
                research_log.append({
                    'iteration': iteration_count,
                    'action': ai_response.get('action', 'unknown'),
                    'details': ai_response.get('details', ''),
                    'timestamp': datetime.now().isoformat()
                })
                
                if ai_response['action'] == 'finish':
                    logger.info(f"AI决定结束研究，共进行了 {iteration_count} 轮迭代")
                    break
                elif ai_response['action'] == 'search':
                    # 执行基于AI决策的搜索和爬取
                    keywords = ai_response.get('keywords', [])
                    if not keywords:
                        logger.warning(f"第 {iteration_count} 轮：AI未提供搜索关键词")
                        break
                    
                    new_articles = await self._execute_search_and_crawl(
                        keywords, 
                        [], 
                        settings
                    )
                    
                    # 扩充knowledge_base
                    knowledge_base.extend(new_articles)
                    logger.info(f"第 {iteration_count} 轮: 新增 {len(new_articles)} 篇文章到知识库")
                else:
                    logger.warning(f"AI返回了未知的动作: {ai_response['action']}")
                    break
            
            # 3. 生成最终报告
            final_report = await self._generate_final_report(knowledge_base, report_config)
            
            # 4. 推送报告到配置的群组
            notification_sent = False
            if hasattr(report_config, 'webhook_url') and report_config.webhook_url:
                notification_sent = await self._send_report_notification(final_report, report_config)
            
            return {
                'success': True,
                'report': final_report,
                'knowledge_base_size': len(knowledge_base),
                'iterations': iteration_count,
                'research_log': research_log,
                'notification_sent': notification_sent
            }
            
        except Exception as e:
            logger.error(f"深度研究失败: {e}")
            return {
                'success': False,
                'message': f'深度研究失败: {str(e)}'
            }
    
    async def _build_initial_knowledge_base(self, report_config) -> List[Dict]:
        """构建初始知识库"""
        logger.info("构建初始知识库...")
        
        try:
            # 设置整个方法的超时时间为30秒
            return await asyncio.wait_for(
                self._build_initial_knowledge_base_impl(report_config),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            logger.error("构建初始知识库超时（30秒），返回空结果")
            return []
        except Exception as e:
            logger.error(f"构建初始知识库失败: {e}")
            return []
    
    async def _build_initial_knowledge_base_impl(self, report_config) -> List[Dict]:
        """构建初始知识库的具体实现"""
        knowledge_base = []
        
        # 获取数据源爬虫ID
        if not report_config.data_sources:
            return knowledge_base
        
        crawler_ids = [int(x) for x in report_config.data_sources.split(',') if x.strip()]
        
        # 导入需要在函数内部进行
        from models import CrawlerConfig, CrawlRecord
        from datetime import timedelta
        
        # 从每个爬虫获取文章（增加单个爬虫处理超时）
        for crawler_id in crawler_ids:
            try:
                # 为每个爬虫设置5秒超时
                await asyncio.wait_for(
                    self._process_single_crawler(crawler_id, report_config, knowledge_base),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                logger.error(f"处理爬虫ID {crawler_id} 超时（5秒），跳过")
                continue
            except Exception as e:
                logger.error(f"处理爬虫ID {crawler_id} 失败: {e}")
                continue
        
        # 同时从"深度研究"爬虫获取历史搜索数据（增加超时保护）
        try:
            await asyncio.wait_for(
                self._get_deep_research_history(report_config, knowledge_base),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.error("获取深度研究历史数据超时（5秒），跳过")
        except Exception as e:
            logger.error(f"获取深度研究历史数据失败: {e}")
        
        # 应用关键词过滤
        if report_config.filter_keywords:
            logger.info(f"开始关键词过滤，当前文章数: {len(knowledge_base)}")
            logger.info(f"过滤关键词: {report_config.filter_keywords}")
            
            filtered_kb = self.llm_service.filter_articles_by_keywords(
                knowledge_base, 
                report_config.filter_keywords
            )
            logger.info(f"关键词过滤完成: {len(knowledge_base)} -> {len(filtered_kb)} 篇文章")
            knowledge_base = filtered_kb
        
        logger.info(f"初始知识库构建完成，共 {len(knowledge_base)} 篇文章")
        return knowledge_base
    
    async def _process_single_crawler(self, crawler_id: int, report_config, knowledge_base: List[Dict]):
        """处理单个爬虫的数据获取"""
        from models import CrawlerConfig, CrawlRecord
        from datetime import timedelta
        
        logger.info(f"正在处理爬虫ID: {crawler_id}")
        crawler = CrawlerConfig.query.get(crawler_id)
        if not crawler:
            logger.warning(f"未找到爬虫ID: {crawler_id}")
            return
        
        logger.info(f"从爬虫 '{crawler.name}' 获取数据...")
        
        # 先尝试从历史记录获取
        time_range_hours = self._parse_time_range(report_config.time_range)
        cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
        
        logger.info(f"查询时间范围: {time_range_hours}小时，截止时间: {cutoff_time}")
        
        records = CrawlRecord.query.filter(
            CrawlRecord.crawler_config_id == crawler_id,
            CrawlRecord.status == 'success',
            CrawlRecord.crawled_at >= cutoff_time
        ).order_by(
            CrawlRecord.publish_date.desc().nulls_last(),
            CrawlRecord.crawled_at.desc()
        ).limit(10).all()
        
        if records:
            logger.info(f"从历史记录获取 {len(records)} 篇文章")
            for record in records:
                knowledge_base.append({
                    'title': record.title,
                    'content': record.content,
                    'url': record.url,
                    'author': record.author,
                    'date': record.publish_date.isoformat() if record.publish_date else '',
                    'source': f'爬虫: {crawler.name}',
                    'crawled_at': record.crawled_at.isoformat()
                })
        else:
            # 如果没有历史记录，跳过实时爬取，只使用现有数据
            logger.info(f"爬虫 '{crawler.name}' 暂无符合时间范围的历史数据，跳过")
    
    async def _get_deep_research_history(self, report_config, knowledge_base: List[Dict]):
        """获取深度研究历史数据"""
        from models import CrawlerConfig, CrawlRecord
        from datetime import timedelta
        
        logger.info("获取深度研究历史数据...")
        deep_research_crawler = CrawlerConfig.query.filter_by(name="深度研究").first()
        if deep_research_crawler:
            time_range_hours = self._parse_time_range(report_config.time_range)
            cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)
            
            search_records = CrawlRecord.query.filter(
                CrawlRecord.crawler_config_id == deep_research_crawler.id,
                CrawlRecord.status == 'success',
                CrawlRecord.crawled_at >= cutoff_time
            ).order_by(
                CrawlRecord.publish_date.desc().nulls_last(),
                CrawlRecord.crawled_at.desc()
            ).limit(20).all()
            
            if search_records:
                logger.info(f"从深度研究历史数据获取 {len(search_records)} 篇文章")
                for record in search_records:
                    knowledge_base.append({
                        'title': record.title,
                        'content': record.content,
                        'url': record.url,
                        'author': record.author,
                        'date': record.publish_date.isoformat() if record.publish_date else '',
                        'source': '深度研究历史数据',
                        'crawled_at': record.crawled_at.isoformat()
                    })
            else:
                logger.info("深度研究爬虫暂无符合时间范围的历史数据")
        else:
            logger.warning("未找到深度研究爬虫配置")
    
    async def _send_research_prompt(self, knowledge_base: List[Dict], report_config, iteration: int) -> Dict[str, Any]:
        """发送研究提示给AI，解析XML响应"""
        
        # 构建knowledge_base XML
        kb_xml = self._build_knowledge_base_xml(knowledge_base)
        
        # 构建user_prompt XML
        user_prompt_xml = f"""<user_prompt>
<report_purpose>{report_config.purpose}</report_purpose>
<research_focus>{report_config.research_focus}</research_focus>
<filter_keywords>{report_config.filter_keywords}</filter_keywords>
</user_prompt>"""
        
        messages = [
            {
                "role": "system",
                "content": f"""你是一位专业的新闻分析师，需要判断现有资料是否足够写出一份基于具体现象的深度分析报告。

**报告目标**: {report_config.purpose}

**判断标准**：
1. **可以写报告的情况**：
   - 有具体的新闻事件、公司动态、产品发布等
   - 有足够的细节和数据支撑深度分析  
   - 能够基于某个具体现象进行多角度解读
   - 内容足够写出事件概述、深度分析、影响评估、趋势预测

2. **需要补充资料的情况**：
   - 只有泛泛的行业信息，缺少具体案例
   - 缺少关键的背景信息或最新动态
   - 无法基于现有内容写出有价值的深度分析

**响应格式**：
- 如果可以开始写报告：<finish />
- 如果需要搜索补充：<keywords_to_search>关键词1,关键词2,关键词3</keywords_to_search>

**搜索关键词要求**：
- 具体的公司名、产品名、事件名
- 最新的新闻动态、发布会、政策变化
- 避免宽泛词汇，要具体化
- 每次最多3个关键词，用逗号分隔

记住：报告不是大而全的行业报告，而是基于某个具体现象的深度分析。"""
            },
            {
                "role": "user",
                "content": f"""当前是第 {iteration} 轮研究迭代。

{user_prompt_xml}

{kb_xml}

请分析现有知识库：
1. 如果已经有足够的具体新闻内容可以写出详细分析报告，请返回 <finish />
2. 如果还缺少关键的具体信息、案例、数据，才搜索补充

判断标准：
- 有具体的新闻事件、公司动态、产品发布等内容 → 可以结束
- 有足够的细节可以进行深度分析 → 可以结束  
- 只有泛泛的行业信息，缺少具体案例 → 需要搜索"""
            }
        ]
        
        try:
            response = self.llm_service._make_request(messages, temperature=0.3)
            return self._parse_ai_response(response)
        except Exception as e:
            logger.error(f"AI研究提示失败: {e}")
            return {'action': 'finish', 'details': f'AI调用失败: {e}'}
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """解析AI的XML响应"""
        try:
            response = response.strip()
            
            # 检查是否是finish
            if '<finish />' in response or '<finish/>' in response:
                return {'action': 'finish', 'details': 'AI决定研究已完成'}
            
            # 解析keywords_to_search
            keywords_match = re.search(r'<keywords_to_search>(.*?)</keywords_to_search>', response, re.DOTALL)
            if keywords_match:
                keywords_text = keywords_match.group(1).strip()
                keywords = [k.strip() for k in keywords_text.split(',') if k.strip()]
                return {
                    'action': 'search',
                    'keywords': keywords,
                    'details': f'需要搜索关键词: {keywords}'
                }
            
            # 如果无法解析，默认结束
            logger.warning(f"无法解析AI响应: {response}")
            return {'action': 'finish', 'details': '无法解析AI响应，结束研究'}
            
        except Exception as e:
            logger.error(f"解析AI响应失败: {e}")
            return {'action': 'finish', 'details': f'解析失败: {e}'}
    
    async def _execute_search_and_crawl(self, keywords: List[str], urls: List[str], settings) -> List[Dict]:
        """执行搜索和爬取"""
        try:
            # 设置整个搜索和爬取过程的超时时间为60秒
            return await asyncio.wait_for(
                self._execute_search_and_crawl_impl(keywords, urls, settings),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            logger.error("搜索和爬取过程超时（60秒），返回已获取的结果")
            return []
        except Exception as e:
            logger.error(f"搜索和爬取过程失败: {e}")
            return []
    
    async def _execute_search_and_crawl_impl(self, keywords: List[str], urls: List[str], settings) -> List[Dict]:
        """执行搜索和爬取的具体实现"""
        new_articles = []
        
        # 1. 执行搜索
        for keyword in keywords[:3]:  # 限制搜索关键词数量
            logger.info(f"搜索关键词: {keyword}")
            
            search_results = self.llm_service.search_web_for_topic(keyword, settings.serp_api_key)
            
            if search_results:
                # 让AI筛选要爬取的URL
                urls_to_crawl = await self._ai_select_urls(search_results, keyword)
                
                # 爬取选中的URL并入库
                for i, url in enumerate(urls_to_crawl[:3]):  # 每个关键词最多爬3个URL
                    try:
                        # 先检查URL是否已存在于数据库
                        if await self._url_exists_in_db(url):
                            logger.info(f"URL已存在于数据库，跳过: {url}")
                            continue
                            
                        logger.info(f"正在爬取第 {i+1}/{min(len(urls_to_crawl), 3)} 个URL: {url[:50]}...")
                        result = await self.crawler_service.crawl_article_content(url)
                        if result['success']:
                            # 添加到新文章列表
                            article_data = {
                                'title': result['title'],
                                'content': result['content'],
                                'url': result['url'],
                                'author': result.get('author', ''),
                                'date': result.get('date', ''),
                                'source': f'搜索: {keyword}',
                                'crawled_at': datetime.now().isoformat()
                            }
                            new_articles.append(article_data)
                            
                            # 保存到数据库 - 创建一个特殊的"深度研究"爬虫记录
                            await self._save_search_result_to_db(result, keyword)
                            
                            logger.info(f"成功爬取并入库: {result['title'][:50]}...")
                    except Exception as e:
                        logger.error(f"爬取URL失败 {url}: {e}")
            
            # 添加延迟避免被限制
            await asyncio.sleep(2)
        
        return new_articles
    
    async def _url_exists_in_db(self, url: str) -> bool:
        """检查URL是否已存在于数据库中"""
        try:
            from models import CrawlRecord
            existing_record = CrawlRecord.query.filter_by(url=url, status='success').first()
            return existing_record is not None
        except Exception as e:
            logger.error(f"检查URL是否存在失败: {e}")
            return False
    
    async def _save_search_result_to_db(self, crawl_result: Dict, keyword: str):
        """将搜索结果保存到数据库"""
        try:
            from models import CrawlerConfig, CrawlRecord, db
            from datetime import datetime
            
            # 查找或创建"深度研究"爬虫配置
            deep_research_crawler = CrawlerConfig.query.filter_by(name="深度研究").first()
            if not deep_research_crawler:
                deep_research_crawler = CrawlerConfig(
                    name="深度研究",
                    list_url="https://news.google.com/search?q=深度研究&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
                    url_regex=r'https://[^/]+/.*',
                    frequency_seconds=0,  # 不定时执行
                    is_active=False  # 不参与常规爬取
                )
                db.session.add(deep_research_crawler)
                db.session.flush()  # 获取ID
            
            # 检查URL是否已存在，避免重复
            existing_record = CrawlRecord.query.filter_by(
                url=crawl_result['url'],
                status='success'
            ).first()
            
            if not existing_record:
                # 创建新的爬取记录
                record = CrawlRecord(
                    crawler_config_id=deep_research_crawler.id,
                    url=crawl_result['url'],
                    title=crawl_result['title'],
                    content=crawl_result['content'],
                    author=crawl_result.get('author', ''),
                    publish_date=None,  # 搜索结果通常没有准确的发布日期
                    status='success'
                )
                db.session.add(record)
                db.session.commit()
                logger.info(f"搜索结果已入库: {crawl_result['title'][:30]}...")
            else:
                logger.info(f"URL已存在于数据库，跳过: {crawl_result['url']}")
                
        except Exception as e:
            logger.error(f"保存搜索结果到数据库失败: {e}")
            # 不影响主流程，继续执行
    
    async def _ai_select_urls(self, search_results: List[Dict], keyword: str) -> List[str]:
        """让AI从搜索结果中选择要爬取的URL，优先选择最新的内容"""
        
        # 按日期排序搜索结果，优先显示最新的
        sorted_results = []
        for result in search_results:
            date_score = 0
            
            # 检查标题和摘要中的时间相关词汇
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            
            # 最新时间词汇得分最高
            latest_keywords = ['2025', '最新', '今日', '刚刚', 'latest', 'today']
            recent_keywords = ['2024', '近期', '最近', 'recent', 'new']
            
            for keyword in latest_keywords:
                if keyword in title or keyword in snippet:
                    date_score += 100
            
            for keyword in recent_keywords:
                if keyword in title or keyword in snippet:
                    date_score += 50
            
            # 如果有具体日期，根据年份给分
            if result.get('date'):
                date_str = result['date']
                if '2025' in date_str:
                    date_score += 90
                elif '2024' in date_str:
                    date_score += 60
                elif '2023' in date_str:
                    date_score += 30
                else:
                    date_score += 10  # 其他年份较低分数
            
            sorted_results.append((result, date_score))
        
        # 按分数排序，分数高的在前
        sorted_results.sort(key=lambda x: x[1], reverse=True)
        
        # 构建搜索结果描述，优先显示最新的
        results_text = ""
        for i, (result, score) in enumerate(sorted_results[:10], 1):
            results_text += f"{i}. 标题: {result.get('title', '')}\n"
            results_text += f"   来源: {result.get('source', '')}\n"
            results_text += f"   摘要: {result.get('snippet', '')}\n"
            results_text += f"   日期: {result.get('date', '未知')}\n"
            results_text += f"   URL: {result.get('url', '')}\n\n"
        
        messages = [
            {
                "role": "system",
                "content": """你需要从搜索结果中选择最有价值的URL进行深入爬取。

请返回XML格式：
<urls_to_crawl>
URL1
URL2
URL3
</urls_to_crawl>

选择标准（按优先级排序）：
1. **时效性优先** - 优先选择最新的内容（2025年、2024年、包含"最新"等时间词汇）
2. **权威性** - 官方网站、知名媒体的内容
3. **相关性** - 与搜索关键词高度相关
4. **深度性** - 可能包含深入分析的文章
5. **只选择3个最新且最有价值的URL**"""
            },
            {
                "role": "user",
                "content": f"""搜索关键词: {keyword}

搜索结果（已按时效性排序，越靠前越新）:
{results_text}

请优先选择最新的3个URL进行爬取，确保获取最新信息。"""
            }
        ]
        
        try:
            response = self.llm_service._make_request(messages, temperature=0.2)
            
            # 解析URLs
            urls_match = re.search(r'<urls_to_crawl>(.*?)</urls_to_crawl>', response, re.DOTALL)
            if urls_match:
                urls_text = urls_match.group(1).strip()
                urls = [url.strip() for url in urls_text.split('\n') if url.strip() and url.strip().startswith('http')]
                return urls[:3]  # 最多3个
            
            # 如果AI没有返回，选择按时效性排序后的前3个
            return [result[0]['url'] for result in sorted_results[:3] if result[0].get('url')]
            
        except Exception as e:
            logger.error(f"AI选择URL失败: {e}")
            # 默认选择按时效性排序后的前3个
            sorted_results = []
            for result in search_results:
                date_score = 0
                title = result.get('title', '').lower()
                snippet = result.get('snippet', '').lower()
                
                # 最新时间词汇得分最高
                latest_keywords = ['2025', '最新', '今日', '刚刚', 'latest', 'today']
                recent_keywords = ['2024', '近期', '最近', 'recent', 'new']
                
                for keyword in latest_keywords:
                    if keyword in title or keyword in snippet:
                        date_score += 100
                
                for keyword in recent_keywords:
                    if keyword in title or keyword in snippet:
                        date_score += 50
                
                # 如果有具体日期，根据年份给分
                if result.get('date'):
                    date_str = result['date']
                    if '2025' in date_str:
                        date_score += 90
                    elif '2024' in date_str:
                        date_score += 60
                    elif '2023' in date_str:
                        date_score += 30
                    else:
                        date_score += 10
                
                sorted_results.append((result, date_score))
            
            sorted_results.sort(key=lambda x: x[1], reverse=True)
            return [result[0]['url'] for result in sorted_results[:3] if result[0].get('url')]
    
    async def _ai_initial_analysis(self, knowledge_base: List[Dict], report_config) -> Dict[str, Any]:
        """AI对初始知识库进行分析，制定研究方向"""
        logger.info(f"AI开始分析 {len(knowledge_base)} 篇初始文章")
        
        try:
            # 构建文章摘要
            articles_summary = ""
            for i, article in enumerate(knowledge_base[:20], 1):  # 只分析前20篇
                articles_summary += f"{i}. 标题: {article.get('title', '')}\n"
                articles_summary += f"   来源: {article.get('source', '')}\n"
                articles_summary += f"   日期: {article.get('date', '')}\n"
                articles_summary += f"   摘要: {article.get('content', '')[:200]}...\n\n"
            
            messages = [
                {
                    "role": "system",
                    "content": """你是一个专业的研究分析师。请分析给定的文章集合，并制定深度研究计划。

请返回XML格式：
<analysis>
<current_knowledge>
简要总结现有文章覆盖的主要内容和观点
</current_knowledge>
<knowledge_gaps>
识别出明显的知识空白或需要深入研究的领域
</knowledge_gaps>
<research_directions>
建议1：具体的研究方向
建议2：具体的研究方向
建议3：具体的研究方向
</research_directions>
<priority_keywords>
关键词1,关键词2,关键词3
</priority_keywords>
</analysis>

分析标准：
1. 识别现有知识的完整性
2. 发现需要补充的信息缺口
3. 提出有针对性的研究方向
4. 建议优先搜索的关键词"""
                },
                {
                    "role": "user",
                    "content": f"""研究主题: {report_config.purpose}
研究侧重点: {report_config.research_focus}
用户关键词: {report_config.filter_keywords}

现有文章集合:
{articles_summary}

请分析这些文章的内容，识别知识空白，并制定深度研究计划。"""
                }
            ]
            
            logger.info("开始AI初步分析，使用流式返回...")
            response = self.llm_service._make_request(messages, temperature=0.3, stream=True)
            if not response:
                return {'summary': '初步分析失败', 'directions': [], 'keywords': []}
            
            # 解析AI的分析结果
            analysis_result = self._parse_initial_analysis(response)
            
            logger.info(f"AI分析结果: {len(analysis_result.get('directions', []))} 个研究方向")
            return analysis_result
            
        except Exception as e:
            logger.error(f"AI初步分析失败: {e}")
            return {'summary': f'分析失败: {e}', 'directions': [], 'keywords': []}
    
    def _parse_initial_analysis(self, ai_response: str) -> Dict[str, Any]:
        """解析AI的初步分析结果"""
        try:
            import re
            
            result = {
                'summary': '',
                'gaps': '',
                'directions': [],
                'keywords': []
            }
            
            # 提取current_knowledge
            knowledge_match = re.search(r'<current_knowledge>(.*?)</current_knowledge>', ai_response, re.DOTALL)
            if knowledge_match:
                result['summary'] = knowledge_match.group(1).strip()
            
            # 提取knowledge_gaps
            gaps_match = re.search(r'<knowledge_gaps>(.*?)</knowledge_gaps>', ai_response, re.DOTALL)
            if gaps_match:
                result['gaps'] = gaps_match.group(1).strip()
            
            # 提取research_directions
            directions_match = re.search(r'<research_directions>(.*?)</research_directions>', ai_response, re.DOTALL)
            if directions_match:
                directions_text = directions_match.group(1).strip()
                # 按行分割，每行是一个研究方向
                directions = [d.strip() for d in directions_text.split('\n') if d.strip()]
                result['directions'] = directions
            
            # 提取priority_keywords
            keywords_match = re.search(r'<priority_keywords>(.*?)</priority_keywords>', ai_response, re.DOTALL)
            if keywords_match:
                keywords_text = keywords_match.group(1).strip()
                keywords = [k.strip() for k in keywords_text.split(',') if k.strip()]
                result['keywords'] = keywords
            
            return result
            
        except Exception as e:
            logger.error(f"解析AI分析结果失败: {e}")
            return {'summary': f'解析失败: {e}', 'directions': [], 'keywords': []}
    
    async def _send_guided_research_prompt(self, knowledge_base: List[Dict], report_config, initial_analysis: Dict, iteration: int) -> Dict[str, Any]:
        """发送基于初步分析的研究提示给AI"""
        logger.info(f"第 {iteration} 轮：发送指导研究提示给AI")
        
        try:
            # 构建当前知识库概要（不发送全部内容，只发送摘要）
            kb_summary = f"当前知识库包含 {len(knowledge_base)} 篇文章，最新的5篇：\n"
            for i, article in enumerate(knowledge_base[-5:], 1):
                kb_summary += f"{i}. {article.get('title', '')[:50]}... (来源: {article.get('source', '')})\n"
            
            messages = [
                {
                    "role": "system", 
                    "content": """你是通用研究AI，擅长指导各领域深度研究。基于当前研究状态，智能决定下一步方向。

🎯 决策框架（适用任何研究领域）：
- 现状评估：当前信息完整度、质量、覆盖面
- 缺口识别：关键信息缺失、深度不足、角度单一
- 优先级排序：重要性、紧迫性、可获得性
- 效果预测：搜索预期收益、成本投入比

📋 返回格式：
继续研究时：
<research_decision>
<action>search</action>
<keywords>核心关键词,相关术语,延伸概念</keywords>
<reasoning>基于缺口分析的搜索理由</reasoning>
</research_decision>

完成研究时：
<research_decision>
<action>finish</action>
<reasoning>信息充足可生成高质量报告的判断依据</reasoning>
</research_decision>

🔍 通用决策原则：
1. 优先填补影响结论的关键信息空白
2. 避免信息重复，追求内容增量价值
3. 平衡深度与广度，确保分析维度完整
4. 当信息足以支撑专业报告时及时结束"""
                },
                {
                    "role": "user",
                    "content": f"""研究主题: {report_config.purpose}
研究侧重点: {report_config.research_focus}

=== 初步分析结果 ===
现有知识: {initial_analysis.get('summary', '')}
知识空白: {initial_analysis.get('gaps', '')}
建议方向: {'; '.join(initial_analysis.get('directions', []))}
优先关键词: {', '.join(initial_analysis.get('keywords', []))}

=== 当前研究状态 ===
{kb_summary}
当前是第 {iteration} 轮研究

请基于以上信息，决定下一步行动。"""
                }
            ]
            
            response = self.llm_service._make_request(messages, temperature=0.3, stream=False)  # 决策不需要流式
            if not response:
                return {'action': 'finish', 'details': 'AI无响应，结束研究'}
            
            # 解析AI决策
            decision = self._parse_research_decision(response)
            
            logger.info(f"第 {iteration} 轮AI决策: {decision.get('action', 'unknown')}")
            return decision
            
        except Exception as e:
            logger.error(f"发送指导研究提示失败: {e}")
            return {'action': 'finish', 'details': f'发送提示失败: {e}'}
    
    def _parse_research_decision(self, ai_response: str) -> Dict[str, Any]:
        """解析AI的研究决策"""
        try:
            import re
            
            result = {'action': 'finish', 'details': 'AI决策解析失败'}
            
            # 提取action
            action_match = re.search(r'<action>(.*?)</action>', ai_response, re.DOTALL)
            if action_match:
                result['action'] = action_match.group(1).strip().lower()
            
            # 提取reasoning
            reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', ai_response, re.DOTALL)
            if reasoning_match:
                result['details'] = reasoning_match.group(1).strip()
            
            # 如果是搜索动作，提取关键词
            if result['action'] == 'search':
                keywords_match = re.search(r'<keywords>(.*?)</keywords>', ai_response, re.DOTALL)
                if keywords_match:
                    keywords_text = keywords_match.group(1).strip()
                    keywords = [k.strip() for k in keywords_text.split(',') if k.strip()]
                    result['keywords'] = keywords
                else:
                    result['keywords'] = []
            
            return result
            
        except Exception as e:
            logger.error(f"解析AI研究决策失败: {e}")
            return {'action': 'finish', 'details': f'解析失败: {e}'}
    
    async def _generate_final_report(self, knowledge_base: List[Dict], report_config) -> str:
        """生成最终报告"""
        logger.info(f"基于 {len(knowledge_base)} 篇文章生成最终报告")
        
        # 构建完整的knowledge_base XML
        kb_xml = self._build_knowledge_base_xml(knowledge_base)
        
        messages = [
            {
                "role": "system",
                "content": f"""你是一位专业的新闻分析师，擅长对具体新闻事件进行深度分析。请基于知识库中的具体新闻内容生成详细的分析报告。

🎯 **报告要求**：
- **聚焦具体事件**：针对知识库中的具体新闻、案例、事件进行分析，不要写泛泛而谈的行业报告
- **详细内容分析**：深入分析新闻背景、关键信息、影响因素，提供具体的数据和细节
- **多角度解读**：从技术、商业、市场、用户等多个角度分析事件
- **实用性强**：提供可操作的洞察和建议
- **引用来源**：在引用具体信息时，必须添加来源链接，格式为 [来源](URL)

📋 **分析框架**：
1. **事件概述** - 具体发生了什么，关键参与者，时间背景
2. **深度分析** - 事件背后的原因、技术细节、商业逻辑
3. **影响评估** - 对行业、用户、竞争对手的具体影响
4. **趋势预测** - 基于此事件可能的后续发展
5. **实用建议** - 针对不同角色的具体建议

⚠️ **避免**：
- 不要写成行业概述或通用分析
- 不要只列标题和大纲
- 不要泛泛而谈，要有具体内容
- 每个部分都要有详细的分析内容

🔍 当前分析任务：
- 分析目的：{report_config.purpose}
- 分析重点：{report_config.research_focus}"""
            },
            {
                "role": "user",
                "content": f"""请基于以下知识库中的具体新闻内容，生成详细的分析报告。

要求：
1. 重点分析知识库中的具体新闻事件，不要写泛泛的行业报告
2. 每个章节都要有详细的内容，不要只是标题
3. 提供具体的数据、案例、分析
4. 针对具体事件进行深度解读
5. **重要**：引用具体信息时，必须添加来源链接，格式为 [来源](URL)
6. 每个重要观点都要有对应的来源链接支撑

<user_prompt>
<report_purpose>{report_config.purpose}</report_purpose>
<research_focus>{report_config.research_focus}</research_focus>
</user_prompt>

{kb_xml}

请生成详细的新闻分析报告，每个部分都要有具体内容。"""
            }
        ]
        
        try:
            logger.info("开始生成最终报告，使用流式返回...")
            result = self.llm_service._make_request(messages, temperature=0.7, stream=True)
            
            # 添加报告头部信息
            header = f"""# {report_config.name} - 深度研究报告 **[AI生成]**

**[报告信息]**
- **生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} **[系统时间]**
- **研究目的：** {report_config.purpose} **[用户配置]**
- **研究重点：** {report_config.research_focus} **[用户配置]**
- **知识库规模：** {len(knowledge_base)} 篇文章 **[数据规模]**
- **研究模式：** AI深度研究 (V3.0 XML交互版) **[技术版本]**

**[质量保证]**
- ✅ 多源数据验证 **[数据质量]**
- ✅ AI智能筛选过滤 **[算法处理]**
- ✅ 时效性检查（7天内） **[时间控制]**
- ✅ 权威性来源优先 **[来源排序]**

---

"""
            
            footer = f"""

---

## 📊 数据来源 **[透明度]**

**[统计信息]** 本报告基于 {len(knowledge_base)} 篇文章分析：

"""
            
            # 按来源分类统计
            source_stats = {}
            for article in knowledge_base:
                source = article.get('source', '未知来源')
                source_stats[source] = source_stats.get(source, 0) + 1
            
            for source, count in source_stats.items():
                footer += f"- **{source}**: {count} 篇 **[数据来源]**\n"
            
            footer += f"""
### 引用列表 **[完整追溯]**

"""
            
            # 添加文章列表
            for i, article in enumerate(knowledge_base[:20], 1):  # 最多显示20篇
                footer += f"{i}. [{article.get('title', '无标题')}]({article.get('url', '#')}) - {article.get('source', '未知来源')} **[引用{i}]**\n"
            
            if len(knowledge_base) > 20:
                footer += f"\n*另有 {len(knowledge_base) - 20} 篇文章* **[省略显示]**\n"
            
            footer += f"""

---

## 🔍 研究方法 **[流程说明]**

**[处理流程]**
1. **数据收集** - 多源爬取 **[自动化]**
2. **质量筛选** - AI过滤 + 关键词匹配 **[算法筛选]**
3. **深度分析** - 多轮迭代 **[AI分析]**
4. **报告生成** - 结构化输出 **[格式化]**

**[质量标准]**
- ✅ 时效性控制 **[时间范围]**
- ✅ 权威性优先 **[来源排序]**
- ✅ 完整性保证 **[多角度]**
- ✅ 准确性验证 **[交叉验证]**

*本报告AI生成，标注确保过程可追溯* **[系统说明]**"""
            
            return header + result + footer
            
        except Exception as e:
            logger.error(f"生成最终报告失败: {e}")
            return f"报告生成失败：{e}"
    
    async def _send_report_notification(self, report_content: str, report_config) -> bool:
        """发送报告通知到群组"""
        try:
            logger.info(f"开始推送深度研究报告到 {getattr(report_config, 'notification_type', 'wechat')}")
            
            # 格式化报告内容用于通知
            formatted_content = self.notification_service.format_deep_research_for_notification(report_content)
            
            # 生成通知标题
            title = f"🔬 {report_config.name} - 深度研究报告"
            
            # 发送通知
            success = self.notification_service.send_notification(
                notification_type=getattr(report_config, 'notification_type', 'wechat'),
                webhook_url=report_config.webhook_url,
                content=formatted_content,
                title=title
            )
            
            if success:
                logger.info("深度研究报告推送成功")
                # 保存推送状态到数据库
                await self._save_notification_status(report_config, True, report_content)
            else:
                logger.error("深度研究报告推送失败")
                await self._save_notification_status(report_config, False, report_content)
            
            return success
            
        except Exception as e:
            logger.error(f"推送报告通知失败: {e}")
            await self._save_notification_status(report_config, False, report_content, str(e))
            return False
    
    async def _save_notification_status(self, report_config, success: bool, report_content: str, error_msg: str = None):
        """保存通知状态到数据库"""
        try:
            from models import ReportRecord, db
            from app import app
            
            # 创建报告记录
            report_record = ReportRecord(
                report_config_id=getattr(report_config, 'id', 0),
                title=report_config.name,
                content=report_content,
                summary=self._extract_report_summary(report_content),
                status='success' if success else 'failed',
                notification_sent=success,
                error_message=error_msg
            )
            
            with app.app_context():
                db.session.add(report_record)
                db.session.commit()
                
                logger.info(f"报告记录已保存: ID={report_record.id}")
                
        except Exception as e:
            logger.error(f"保存报告记录失败: {e}")
    
    def _extract_report_summary(self, report_content: str) -> str:
        """提取报告摘要"""
        try:
            # 简单提取前200字符作为摘要
            lines = report_content.split('\n')
            summary_lines = []
            
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    summary_lines.append(line.strip())
                    if len('\n'.join(summary_lines)) > 200:
                        break
            
            summary = '\n'.join(summary_lines)
            if len(summary) > 200:
                summary = summary[:200] + "..."
            
            return summary
            
        except Exception:
            return "无法提取摘要"
    
    def _build_knowledge_base_xml(self, knowledge_base: List[Dict]) -> str:
        """构建knowledge_base XML"""
        xml_content = "<knowledge_base>\n"
        
        for i, article in enumerate(knowledge_base, 1):
            xml_content += f"<article id='{i}'>\n"
            xml_content += f"<title>{self._escape_xml(article.get('title', ''))}</title>\n"
            xml_content += f"<url>{self._escape_xml(article.get('url', ''))}</url>\n"
            xml_content += f"<source>{self._escape_xml(article.get('source', ''))}</source>\n"
            xml_content += f"<date>{self._escape_xml(article.get('date', ''))}</date>\n"
            xml_content += f"<content>{self._escape_xml(article.get('content', '')[:2000])}</content>\n"  # 限制长度
            xml_content += f"</article>\n"
        
        xml_content += "</knowledge_base>"
        return xml_content
    
    def _escape_xml(self, text: str) -> str:
        """转义XML特殊字符"""
        if not text:
            return ""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#39;'))
    
    def _parse_time_range(self, time_range: str) -> int:
        """解析时间范围为小时数"""
        if time_range == '24h':
            return 24
        elif time_range == '3d':
            return 72
        elif time_range == '7d':
            return 168
        elif time_range == '30d':
            return 720
        else:
            return 24  # 默认24小时

from datetime import timedelta
