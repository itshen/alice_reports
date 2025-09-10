#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知服务
支持企业微信、金山协作等平台的消息推送
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)

class NotificationService:
    """通知服务类"""
    
    def send_notification(self, notification_type: str, webhook_url: str, content: str, title: str = None) -> bool:
        """发送通知"""
        try:
            if notification_type == 'wechat':
                return self._send_wechat_notification(webhook_url, content, title)
            elif notification_type == 'jinshan':
                return self._send_jinshan_notification(webhook_url, content, title)
            else:
                logger.error(f"不支持的通知类型: {notification_type}")
                return False
        
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
            return False
    
    def _send_wechat_notification(self, webhook_url: str, content: str, title: str = None) -> bool:
        """发送企业微信通知"""
        try:
            # 构建消息内容
            if title:
                message = f"## {title}\n\n{content}"
            else:
                message = content
            
            # 企业微信机器人消息格式
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": message
                }
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                webhook_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.info("企业微信通知发送成功")
                    return True
                else:
                    logger.error(f"企业微信通知发送失败: {result.get('errmsg')}")
                    return False
            else:
                logger.error(f"企业微信通知请求失败: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"发送企业微信通知异常: {e}")
            return False
    
    def _send_jinshan_notification(self, webhook_url: str, content: str, title: str = None) -> bool:
        """发送金山协作通知"""
        try:
            # 构建消息内容
            message_title = title or "智能信息分析报告"
            
            # 如果有标题，将标题和内容组合为Markdown格式
            if title:
                full_content = f"## {message_title}\n\n{content}"
            else:
                full_content = content
            
            # 金山协作机器人消息格式（使用Markdown格式以支持更丰富的展示）
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "text": full_content
                }
            }
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                webhook_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("金山协作通知发送成功")
                return True
            else:
                logger.error(f"金山协作通知请求失败: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"发送金山协作通知异常: {e}")
            return False
    
    def format_simple_report_for_notification(self, report_content: str) -> str:
        """格式化简单报告用于通知"""
        # 限制通知内容长度，避免超出平台限制
        max_length = 4000
        
        if len(report_content) <= max_length:
            return report_content
        
        # 截取前部分内容并添加省略提示
        truncated = report_content[:max_length-100]
        return truncated + "\n\n> **提示：** *内容过长，已截取部分内容，完整报告请查看系统后台*"
    
    def format_deep_research_for_notification(self, report_content: str) -> str:
        """格式化深度研究报告用于通知"""
        # 对于深度报告，提取关键部分发送通知
        lines = report_content.split('\n')
        
        # 提取标题和执行摘要部分
        notification_lines = []
        in_summary = False
        summary_lines = 0
        
        for line in lines:
            # 添加标题
            if line.startswith('# '):
                notification_lines.append(line)
                continue
            
            # 查找执行摘要部分
            if '执行摘要' in line or '摘要' in line:
                in_summary = True
                notification_lines.append(line)
                continue
            
            # 在摘要部分收集内容
            if in_summary:
                if line.startswith('#') and summary_lines > 0:
                    # 遇到下一个标题，结束摘要收集
                    break
                
                notification_lines.append(line)
                if line.strip():
                    summary_lines += 1
                
                # 限制摘要长度
                if summary_lines >= 10:
                    break
        
        # 添加查看完整报告的提示
        notification_lines.append("\n---")
        notification_lines.append("> **提示：** *这是报告摘要，完整报告请查看系统后台*")
        
        result = '\n'.join(notification_lines)
        
        # 确保不超过长度限制
        max_length = 2000
        if len(result) > max_length:
            result = result[:max_length-80] + "\n\n> **提示：** *内容已截取*"
        
        return result
    
    def _add_universal_annotations(self, line: str) -> str:
        """通用智能标注系统 - 自适应任何研究领域"""
        if not line.strip():
            return line
        
        import re
        
        # 1. 数据类型标注 - 适用于任何定量研究
        if re.search(r'\d+[年月日]|\d{4}年|\d+月|\d+日|\d{4}-\d{2}-\d{2}', line):
            return f"{line} **[时间节点]**"
        elif re.search(r'\d+%|\d+倍|\d+\.\d+%|\d+比\d+|增长\d+|下降\d+', line):
            return f"{line} **[量化指标]**"
        elif re.search(r'\d+万|\d+亿|\d+千万|\$\d+|€\d+|￥\d+', line):
            return f"{line} **[规模数据]**"
        elif re.search(r'\d+篇|\d+个|\d+项|\d+轮|\d+次|\d+人|\d+家', line):
            return f"{line} **[统计计数]**"
        
        # 2. 信息性质标注 - 适用于任何信息类型
        elif any(keyword in line for keyword in ['发布', '推出', '上线', '发表', '宣布', '启动', '开始']):
            return f"{line} **[发布动态]**"
        elif any(keyword in line for keyword in ['突破', '创新', '首次', '新增', '升级', '改进', '优化']):
            return f"{line} **[创新进展]**"
        elif any(keyword in line for keyword in ['预测', '预计', '将会', '未来', '趋势', '展望', '可能']):
            return f"{line} **[前瞻分析]**"
        elif any(keyword in line for keyword in ['显示', '表明', '证明', '研究发现', '数据表明', '结果显示']):
            return f"{line} **[研究发现]**"
        elif any(keyword in line for keyword in ['优势', '特点', '特征', '功能', '性能', '能力', '特色']):
            return f"{line} **[特征描述]**"
        elif any(keyword in line for keyword in ['影响', '作用', '效果', '结果', '后果', '意义']):
            return f"{line} **[影响评估]**"
        elif any(keyword in line for keyword in ['问题', '挑战', '困难', '风险', '限制', '缺陷']):
            return f"{line} **[问题识别]**"
        elif any(keyword in line for keyword in ['建议', '推荐', '应该', '需要', '建议', '方案']):
            return f"{line} **[策略建议]**"
        
        # 3. 来源可信度标注 - 适用于任何信息来源
        elif any(keyword in line for keyword in ['根据', '据', '引用', '来源于', '参考']):
            return f"{line} **[引用来源]**"
        elif any(keyword in line for keyword in ['官方', '权威', '专业', '学术', '科学']):
            return f"{line} **[权威资料]**"
        elif any(keyword in line for keyword in ['用户', '客户', '消费者', '受访者', '调研对象']):
            return f"{line} **[用户观点]**"
        elif any(keyword in line for keyword in ['专家', '学者', '研究员', '分析师', '权威人士']):
            return f"{line} **[专家观点]**"
        
        # 4. 行业领域标注 - 自动识别研究领域
        elif any(keyword in line for keyword in ['技术', '科技', '算法', '系统', '平台', '工具']):
            return f"{line} **[技术领域]**"
        elif any(keyword in line for keyword in ['市场', '商业', '经济', '商务', '贸易', '销售']):
            return f"{line} **[商业领域]**"
        elif any(keyword in line for keyword in ['政策', '法规', '制度', '规定', '标准', '法律']):
            return f"{line} **[政策法规]**"
        elif any(keyword in line for keyword in ['社会', '文化', '教育', '健康', '环境', '生活']):
            return f"{line} **[社会领域]**"
        
        # 默认返回原始行
        return line
    
    def test_webhook(self, notification_type: str, webhook_url: str) -> Dict:
        """测试Webhook连接"""
        try:
            # 为不同平台优化测试消息格式
            if notification_type == 'jinshan':
                test_message = f"""这是来自 **智能信息分析平台** 的测试消息

> **发送时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**功能特性：**
- ✅ 智能爬虫监控
- ✅ 自动报告生成  
- ✅ 多平台推送

---
*测试成功，系统运行正常！*"""
            else:
                test_message = f"这是来自智能信息分析平台的测试消息\n\n发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            success = self.send_notification(
                notification_type=notification_type,
                webhook_url=webhook_url,
                content=test_message,
                title="🔔 系统测试消息"
            )
            
            if success:
                return {
                    'success': True,
                    'message': '测试消息发送成功'
                }
            else:
                return {
                    'success': False,
                    'message': '测试消息发送失败'
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'测试失败: {str(e)}'
            }
