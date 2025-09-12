#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大语言模型服务
支持通义千问、OpenRouter等多种LLM服务商
"""

import requests
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMService:
    """大语言模型服务类"""
    
    def __init__(self):
        self.settings = None
    
    def update_settings(self, settings):
        """更新LLM设置"""
        self.settings = settings
    
    def test_connection(self, settings=None) -> Dict[str, Any]:
        """测试LLM连接"""
        test_settings = settings or self.settings
        
        if not test_settings or not test_settings.llm_api_key:
            return {
                'success': False,
                'message': 'API Key未配置'
            }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {test_settings.llm_api_key}'
        }
        
        # 发送一个简单的测试消息
        data = {
            'model': test_settings.llm_model_name or 'qwen-plus',
            'messages': [
                {
                    'role': 'user',
                    'content': '请回复"连接测试成功"'
                }
            ],
            'temperature': 0.1,
            'max_tokens': 50
        }
        
        try:
            response = requests.post(
                f"{test_settings.llm_base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    return {
                        'success': True,
                        'message': f'连接成功！模型响应: {content}',
                        'model': test_settings.llm_model_name,
                        'provider': test_settings.llm_provider
                    }
                else:
                    return {
                        'success': False,
                        'message': '响应格式异常'
                    }
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json()
                    if 'error' in error_detail:
                        error_msg = error_detail['error'].get('message', error_msg)
                except:
                    pass
                
                return {
                    'success': False,
                    'message': f'连接失败: {error_msg}'
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'message': '连接超时，请检查网络或API地址'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'message': '无法连接到服务器，请检查API地址'
            }
        except Exception as e:
            logger.error(f"LLM连接测试失败: {e}")
            return {
                'success': False,
                'message': f'连接测试失败: {str(e)}'
            }
    
    def _make_request(self, messages: List[Dict], temperature: float = 0.7, stream: bool = False) -> str:
        """发送请求到LLM服务"""
        if not self.settings or not self.settings.llm_api_key:
            raise Exception("LLM设置未配置")
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.settings.llm_api_key}'
        }
        
        data = {
            'model': self.settings.llm_model_name,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': 4000,
            'stream': stream
        }
        
        try:
            if stream:
                return self._handle_stream_request(headers, data)
            else:
                response = requests.post(
                    f"{self.settings.llm_base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=120  # 增加超时时间
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content']
                else:
                    logger.error(f"LLM请求失败: {response.status_code} - {response.text}")
                    raise Exception(f"LLM请求失败: {response.status_code}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM请求异常: {e}")
            raise Exception(f"LLM请求异常: {e}")
    
    def _handle_stream_request(self, headers: Dict, data: Dict) -> str:
        """处理流式请求"""
        import json
        
        try:
            response = requests.post(
                f"{self.settings.llm_base_url}/chat/completions",
                headers=headers,
                json=data,
                stream=True,
                timeout=300  # 流式请求更长的超时时间
            )
            
            if response.status_code != 200:
                logger.error(f"流式LLM请求失败: {response.status_code} - {response.text}")
                raise Exception(f"流式LLM请求失败: {response.status_code}")
            
            content = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        line_str = line_str[6:]  # 移除 'data: ' 前缀
                        
                        if line_str.strip() == '[DONE]':
                            break
                            
                        try:
                            chunk_data = json.loads(line_str)
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                delta = chunk_data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    content += delta['content']
                                    # 实时显示进度（可选）
                                    print(delta['content'], end='', flush=True)
                        except json.JSONDecodeError:
                            # 忽略无法解析的行
                            continue
            
            logger.info(f"流式请求完成，生成内容长度: {len(content)}")
            return content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"流式LLM请求异常: {e}")
            raise Exception(f"流式LLM请求异常: {e}")
    
    def generate_url_regex(self, settings, page_content: str, url: str, requirement: str = '匹配文章详情页链接') -> Dict[str, Any]:
        """使用AI生成URL正则表达式"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": """你是一个正则表达式专家。分析网页内容，生成一个能够匹配文章详情页链接的正则表达式。

严格要求：
1. 只返回一行正则表达式，不要任何解释或说明
2. 必须使用完整格式：(正则表达式)"
3. 示例格式：(https://www\.news\.cn/comments/\d{8}/[a-f0-9]{32}/c\.html)"
4. 确保正则表达式语法正确，特别注意方括号[]必须正确闭合
5. 使用转义字符\来转义特殊字符如点号\.
6. 不要使用未闭合的字符集[或其他语法错误"""
                },
                {
                    "role": "user",
                    "content": f"""
网站URL：{url}

用户需求：{requirement}

网页HTML内容（前3000字符）：
{page_content[:3000]}

请根据用户需求分析这个网页的结构，生成一个正则表达式来匹配符合要求的链接。
注意观察链接的特征，比如包含特定路径、文件扩展名或ID模式。

用户的具体需求是：{requirement}
请确保生成的正则表达式能准确匹配到用户想要的链接类型。
"""
                }
            ]
            
            # 使用临时设置
            temp_settings = self.settings
            self.settings = settings
            
            result = self._make_request(messages, temperature=0.3)
            
            # 恢复原设置
            self.settings = temp_settings
            
            # 提取正则表达式
            import re
            
            # 清理AI返回的结果
            cleaned_result = result.strip()
            # 移除可能的markdown代码块标记
            cleaned_result = re.sub(r'^```.*?\n', '', cleaned_result, flags=re.MULTILINE)
            cleaned_result = re.sub(r'\n```$', '', cleaned_result)
            cleaned_result = re.sub(r'^`|`$', '', cleaned_result).strip()
            
            # 尝试多种模式提取正则表达式
            extracted_regex = None
            
            # 模式1: href="(...)" 格式
            pattern1 = re.search(r'href="([^"]+)"', cleaned_result)
            if pattern1:
                extracted_regex = pattern1.group(0)
            
            # 模式2: 直接的正则表达式（第一行）
            if not extracted_regex:
                lines = cleaned_result.split('\n')
                if lines:
                    extracted_regex = lines[0].strip()
            
            # 模式3: 如果包含括号，尝试提取括号内容
            if not extracted_regex:
                pattern3 = re.search(r'\(([^)]+)\)', cleaned_result)
                if pattern3:
                    extracted_regex = f'href="({pattern3.group(1)})"'
            
            # 如果还是没有找到，使用清理后的结果
            if not extracted_regex:
                extracted_regex = cleaned_result
            
            # 验证正则表达式语法
            try:
                re.compile(extracted_regex)
                logger.info(f"AI生成的正则表达式: {extracted_regex}")
            except re.error as e:
                logger.error(f"AI生成的正则表达式语法错误: {e}, 原始结果: {result}")
                # 如果语法错误，返回一个安全的默认正则表达式
                extracted_regex = r'href="([^"]*\.html[^"]*)"'
                logger.info(f"使用默认正则表达式: {extracted_regex}")
            
            return {
                'success': True,
                'regex': extracted_regex,
                'explanation': '基于页面结构分析生成的正则表达式'
            }
        
        except Exception as e:
            logger.error(f"AI生成正则表达式失败: {e}")
            # 返回默认正则表达式
            return {
                'success': True,
                'regex': r'href="([^"]*\.html[^"]*)"',
                'explanation': '使用默认正则表达式（匹配.html链接）'
            }
    
    def generate_regex_from_samples(self, page_content: str, sample_titles: List[str]) -> str:
        """根据样本标题生成正则表达式"""
        if not sample_titles:
            return r'href="([^"]*\.html?[^"]*)"'
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": "你是一个正则表达式专家。根据用户提供的网页内容和样本标题，生成一个能够匹配相关文章链接的正则表达式。只返回正则表达式，不要其他解释。"
                },
                {
                    "role": "user",
                    "content": f"""
网页内容片段：
{page_content[:2000]}

用户想要匹配的文章标题样本：
{chr(10).join(sample_titles)}

请生成一个正则表达式来匹配这些文章的链接URL。正则表达式应该能够从href属性中提取完整的URL。
"""
                }
            ]
            
            result = self._make_request(messages, temperature=0.3)
            
            # 提取正则表达式（去除可能的解释文字）
            import re
            regex_pattern = re.search(r'r?["\']([^"\']+)["\']', result)
            if regex_pattern:
                return regex_pattern.group(1)
            else:
                # 如果没有找到引号包围的正则，直接返回结果
                return result.strip()
        
        except Exception as e:
            logger.error(f"生成正则表达式失败: {e}")
            # 返回默认正则表达式
            return r'href="([^"]*\.html?[^"]*)"'
    
    def filter_articles_by_keywords(self, articles: List[Dict], keywords: str) -> List[Dict]:
        """根据关键词过滤文章"""
        if not keywords.strip():
            return articles
        
        keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
        if not keyword_list:
            return articles
        
        filtered_articles = []
        for article in articles:
            # 安全地获取标题和内容，确保不是None
            title = article.get('title') or ''
            content = article.get('content') or ''
            
            # 转换为小写进行匹配
            title_lower = title.lower() if title else ''
            content_lower = content.lower() if content else ''
            
            # 检查是否包含任一关键词
            for keyword in keyword_list:
                keyword_lower = keyword.lower()
                if keyword_lower in title_lower or keyword_lower in content_lower:
                    filtered_articles.append(article)
                    break
        
        return filtered_articles
    
    def generate_simple_report(self, articles: List[Dict], report_config) -> str:
        """生成常规报告（AI分析，无网络搜索）"""
        if not articles:
            return "本期未发现相关新闻。"
        
        try:
            # 准备文章内容用于AI分析
            articles_content = []
            for i, article in enumerate(articles[:20], 1):  # 最多分析20篇文章
                title = article.get('title', f'文章{i}')
                url = article.get('url', '')
                content = f"""
【文章{i}】
标题：{title}
链接：{url}
内容：{article.get('content', '')[:1000]}
时间：{article.get('date', '未知')}
---"""
                articles_content.append(content)
            
            # 构建AI分析提示
            messages = [
                {
                    "role": "system",
                    "content": f"""你是一位专业的信息分析师。请根据提供的文章内容，围绕以下目的进行分析：

{report_config.purpose}

请生成一份结构化的分析报告，包含：
1. **核心要点** - 提炼关键信息
2. **趋势分析** - 识别发展趋势和变化
3. **重要事件** - 突出重要动态，每一行之前，都要先说明文章的时间，格式是：mm.dd。
4. **影响评估** - 分析潜在影响
5. **总结洞察** - 提供有价值的结论

**重要要求：**
- 在分析任何观点或事件时，必须严格使用 [来源（仅来源二字）](来源链接) 格式引用来源
- 每个重要论点都必须有明确的来源引用
- 不要添加文章中没有的信息
- 确保所有引用的链接格式正确

**引用格式示例：**
"根据最新报告，数据合规要求日趋严格 [来源](https://example.com/news1)，同时国产替代政策持续推进 [来源](https://example.com/news2)。"

报告应该专业、客观、有深度，并且每个关键信息都有明确的来源追溯。"""
                },
                {
                    "role": "user", 
                    "content": f"""请基于以下 {len(articles)} 篇文章内容进行分析：

{chr(10).join(articles_content)}

请生成分析报告，并严格在每个重要观点后使用 [来源](来源链接) 格式标注来源。"""
                }
            ]
            
            # 调用LLM生成报告（使用流式返回）
            if not self.settings or not self.settings.llm_api_key:
                raise Exception("LLM配置未设置")
            
            logger.info("开始生成常规报告，使用流式返回...")
            response = self._make_request(messages, temperature=0.7, stream=True)
            ai_analysis = response.strip()
            
            # 构建最终报告
            report = f"""
**分析目的：** {report_config.purpose}\n
**过滤关键词：** {report_config.filter_keywords}\n
**时间范围：** {report_config.time_range}\n
**分析文章数：** {len(articles)} 篇\n

---

{ai_analysis}

---

## 📊 数据来源

本报告基于 {len(articles)} 篇相关文章分析生成：

"""
            
            # 添加文章来源列表
            for i, article in enumerate(articles[:10], 1):  # 显示前10篇
                report += f"{i}. [{article.get('title', '无标题')}]({article.get('url', '#')})\n"
            
            if len(articles) > 10:
                report += f"\n*(还有 {len(articles) - 10} 篇文章)*\n"
            
            report += "\n---\n*本报告由AI智能分析生成*"
            
            return report
        
        except Exception as e:
            logger.error(f"生成常规报告失败: {e}")
            return f"报告生成失败：{e}"
    
    def generate_deep_research_report(self, articles: List[Dict], report_config) -> str:
        """生成深度研究报告"""
        if not articles:
            return "未找到相关信息，无法生成深度研究报告。"
        
        try:
            # 准备文章内容
            articles_content = []
            for article in articles[:20]:  # 最多分析20篇文章
                content = f"标题：{article.get('title', '')}\n"
                content += f"内容：{article.get('content', '')[:1000]}\n"  # 限制长度
                content += f"来源：{article.get('url', '')}\n"
                articles_content.append(content)
            
            messages = [
                {
                    "role": "system",
                    "content": f"""你是一位专业的信息分析师和研究员。请根据提供的文章内容，围绕以下研究重点进行深入分析：

{report_config.research_focus}

请生成一份结构化的深度研究报告，包含以下部分：
1. 执行摘要
2. 关键发现
3. 深度分析
4. 趋势洞察
5. 结论与建议

报告应该专业、客观、有深度，并提供有价值的洞察。"""
                },
                {
                    "role": "user",
                    "content": f"""
研究目的：{report_config.purpose}

相关文章内容：
{chr(10).join(articles_content)}

请基于以上内容生成深度研究报告。
"""
                }
            ]
            
            result = self._make_request(messages, temperature=0.7)
            
            # 添加报告头部信息
            header = f"""# {report_config.name} - 深度研究报告

**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n
**研究目的：** {report_config.purpose}\n
**研究重点：** {report_config.research_focus}\n
**分析文章数：** {len(articles)} 篇\n

---

"""
            
            footer = f"""

---

## 📊 数据来源

本报告基于以下 {len(articles)} 篇文章进行分析：

"""
            
            # 添加数据来源列表
            for i, article in enumerate(articles[:10], 1):
                footer += f"{i}. [{article.get('title', '无标题')}]({article.get('url', '#')})\n"
            
            footer += "\n*本报告由智能信息分析平台自动生成*"
            
            return header + result + footer
        
        except Exception as e:
            logger.error(f"生成深度研究报告失败: {e}")
            return f"深度研究报告生成失败：{e}"
    
    def search_web_for_topic(self, topic: str, serp_api_key: str) -> List[Dict]:
        """使用搜索API获取主题相关信息"""
        if not serp_api_key:
            logger.warning("SERP API密钥未配置，跳过网络搜索")
            return []
        
        try:
            import requests
            
            logger.info(f"开始搜索主题: {topic}")
            
            # 使用SerpAPI进行搜索，匹配实际API格式
            search_url = "https://serpapi.com/search"
            params = {
                'engine': 'google',
                'q': topic,
                'api_key': serp_api_key,
                'num': 10,  # 获取前10个结果
                'hl': 'zh-cn',  # 中文搜索
                'gl': 'cn',  # 中国地区
                'json_restrictor': 'organic_results[].{position,title,snippet,redirect_link,date}'
            }
            
            response = requests.get(search_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                search_results = []
                organic_results = data.get('organic_results', [])
                
                for result in organic_results:
                    # 处理redirect_link，提取真实URL
                    url = result.get('redirect_link', '')
                    if url and 'url=' in url:
                        # 从Google重定向链接中提取真实URL
                        import urllib.parse
                        try:
                            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                            if 'url' in parsed:
                                url = parsed['url'][0]
                        except:
                            pass  # 如果解析失败，保持原URL
                    
                    # 从URL推断来源域名
                    source = ''
                    if url:
                        try:
                            from urllib.parse import urlparse
                            parsed_url = urlparse(url)
                            source = parsed_url.netloc
                        except:
                            source = url[:50] + '...' if len(url) > 50 else url
                    
                    search_results.append({
                        'title': result.get('title', ''),
                        'url': url,
                        'snippet': result.get('snippet', ''),
                        'source': source,
                        'date': result.get('date', ''),
                        'position': result.get('position', 0)
                    })
                
                logger.info(f"搜索完成，获得 {len(search_results)} 个结果")
                return search_results
            else:
                logger.error(f"搜索API请求失败: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"网络搜索失败: {e}")
            return []
    
    def generate_search_based_report(self, search_results: List[Dict], research_topic: str, research_focus: str) -> str:
        """基于搜索结果生成深度研究报告"""
        if not search_results:
            return "未找到相关搜索结果，无法生成研究报告。"
        
        try:
            # 准备搜索结果内容
            search_content = []
            for i, result in enumerate(search_results[:10], 1):
                content = f"搜索结果 {i}:\n"
                content += f"标题：{result.get('title', '')}\n"
                content += f"来源：{result.get('source', '')}\n"
                content += f"摘要：{result.get('snippet', '')}\n"
                content += f"链接：{result.get('url', '')}\n"
                if result.get('date'):
                    content += f"日期：{result['date']}\n"
                search_content.append(content)
            
            messages = [
                {
                    "role": "system",
                    "content": f"""你是一位专业的研究分析师。请基于提供的搜索结果，围绕研究主题进行深入分析。

研究主题：{research_topic}
研究重点：{research_focus}

请生成一份结构化的深度研究报告，包含以下部分：
1. 执行摘要
2. 关键发现
3. 深度分析
4. 趋势洞察
5. 结论与建议

报告应该专业、客观、有深度，并基于搜索结果提供有价值的洞察。"""
                },
                {
                    "role": "user",
                    "content": f"""
研究主题：{research_topic}
研究重点：{research_focus}

基于以下搜索结果进行深度分析：

{chr(10).join(search_content)}

请基于以上搜索结果生成深度研究报告。
"""
                }
            ]
            
            result = self._make_request(messages, temperature=0.7)
            
            # 添加报告头部信息
            header = f"""# {research_topic} - 深度研究报告

**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n
**研究主题：** {research_topic}\n
**研究重点：** {research_focus}\n
**搜索结果数：** {len(search_results)} 篇\n

---

"""
            
            footer = f"""

---

## 📊 数据来源

本报告基于以下 {len(search_results)} 个搜索结果进行分析：

"""
            
            # 添加搜索结果来源列表
            for i, result in enumerate(search_results[:10], 1):
                footer += f"{i}. [{result.get('title', '无标题')}]({result.get('url', '#')}) - {result.get('source', '未知来源')}\n"
            
            footer += "\n*本报告基于网络搜索结果由智能信息分析平台自动生成*"
            
            return header + result + footer
        
        except Exception as e:
            logger.error(f"生成基于搜索的深度研究报告失败: {e}")
            return f"深度研究报告生成失败：{e}"

# datetime已在上面导入
