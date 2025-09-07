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
            
            # 金山协作机器人消息格式（根据实际API调整）
            data = {
                "msg_type": "rich_text",
                "content": {
                    "title": message_title,
                    "text": content
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
        return truncated + "\n\n...\n\n*内容过长，已截取部分内容*"
    
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
        notification_lines.append("*这是报告摘要，完整报告请查看系统后台*")
        
        result = '\n'.join(notification_lines)
        
        # 确保不超过长度限制
        max_length = 2000
        if len(result) > max_length:
            result = result[:max_length-50] + "\n\n*内容已截取*"
        
        return result
    
    def test_webhook(self, notification_type: str, webhook_url: str) -> Dict:
        """测试Webhook连接"""
        try:
            test_message = f"这是来自智能信息分析平台的测试消息\n\n发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            success = self.send_notification(
                notification_type=notification_type,
                webhook_url=webhook_url,
                content=test_message,
                title="测试消息"
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
