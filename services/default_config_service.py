#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
默认配置服务
用于管理和恢复系统的默认配置
"""

from models import CrawlerConfig, ReportConfig, GlobalSettings, db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DefaultConfigService:
    """默认配置服务类"""
    
    # 默认爬虫配置
    DEFAULT_CRAWLER_CONFIGS = [
        {
            "name": "科技",
            "list_url": "https://www.news.cn/comments/wpyc/index.html",
            "url_regex": "(https://www\\.news\\.cn/comments/\\d{8}/[a-f0-9]{32}/c\\.html)",
            "frequency_seconds": 3600,
            "is_active": True
        },
        {
            "name": "虎嗅",
            "list_url": "https://m.huxiu.com/channel/105.html",
            "url_regex": "(https://www\\.huxiu\\.com/article/\\d+\\.html)",
            "frequency_seconds": 3600,
            "is_active": True
        },
        {
            "name": "36 氪 - AI",
            "list_url": "https://36kr.com/information/AI/",
            "url_regex": "(https://36kr\\.com/p/\\d+)",
            "frequency_seconds": 3600,
            "is_active": True
        },
        {
            "name": "36 氪 - 职场",
            "list_url": "https://36kr.com/information/web_zhichang/",
            "url_regex": "(https://36kr\\.com/p/\\d+)",
            "frequency_seconds": 3600,
            "is_active": True
        },
        {
            "name": "36 氪 - 其他",
            "list_url": "https://36kr.com/information/other/",
            "url_regex": "(https://36kr\\.com/p/\\d+|https://36kr\\.com/topics/\\d+|https://36kr\\.com/academe/\\d+|https://36kr\\.com/information/\\d+/)",
            "frequency_seconds": 3600,
            "is_active": True
        },
        {
            "name": "新华网 - 数字经济",
            "list_url": "https://www.news.cn/tech/szjj/index.html",
            "url_regex": "(https://www\\.news\\.cn/\\w+/\\d{8}/[a-f0-9]{32}/c\\.html)",
            "frequency_seconds": 3600,
            "is_active": True
        },
        {
            "name": "新华网 - 科技快讯",
            "list_url": "https://www.news.cn/tech/kjkx/index.html",
            "url_regex": "(https://www\\.news\\.cn/\\w+/\\d{8}/[a-f0-9]{32}/c\\.html)",
            "frequency_seconds": 3600,
            "is_active": True
        }
    ]
    
    # 默认报告配置
    DEFAULT_REPORT_CONFIGS = [
        {
            "name": "科技新闻日报",
            "data_sources": "1,2,3,6,7",  # 对应默认爬虫配置的ID
            "filter_keywords": "人工智能,AI,科技,技术,创新",
            "time_range": "24h",
            "purpose": "汇总每日科技新闻，关注人工智能和技术创新动态",
            "enable_deep_research": False,
            "research_focus": "",
            "notification_type": "wechat",
            "webhook_url": "",
            "is_active": True
        },
        {
            "name": "AI 深度研究周报",
            "data_sources": "3",  # 36氪AI频道
            "filter_keywords": "人工智能,AI,大模型,机器学习,深度学习",
            "time_range": "7d",
            "purpose": "深度分析AI行业发展趋势和技术进展",
            "enable_deep_research": True,
            "research_focus": "请深入分析AI技术的最新发展趋势、市场竞争格局、技术突破和商业应用前景",
            "notification_type": "wechat",
            "webhook_url": "",
            "is_active": False  # 默认不激活，需要用户手动配置
        }
    ]
    
    # 默认全局设置
    DEFAULT_GLOBAL_SETTINGS = {
        "serp_api_key": "",
        "llm_provider": "qwen",
        "llm_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "llm_api_key": "",
        "llm_model_name": "qwen-plus"
    }
    
    @classmethod
    def init_default_configs(cls):
        """初始化默认配置"""
        try:
            logger.info("开始初始化默认配置...")
            
            # 初始化默认爬虫配置
            cls._init_default_crawler_configs()
            
            # 初始化默认报告配置
            cls._init_default_report_configs()
            
            # 初始化默认全局设置
            cls._init_default_global_settings()
            
            logger.info("默认配置初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"初始化默认配置失败: {str(e)}")
            return False
    
    @classmethod
    def _init_default_crawler_configs(cls):
        """初始化默认爬虫配置"""
        # 检查是否已有爬虫配置
        existing_count = CrawlerConfig.query.count()
        if existing_count > 0:
            logger.info(f"已存在 {existing_count} 个爬虫配置，跳过默认配置初始化")
            return
        
        logger.info("创建默认爬虫配置...")
        for config_data in cls.DEFAULT_CRAWLER_CONFIGS:
            crawler_config = CrawlerConfig(
                name=config_data['name'],
                list_url=config_data['list_url'],
                url_regex=config_data['url_regex'],
                frequency_seconds=config_data['frequency_seconds'],
                is_active=config_data['is_active']
            )
            db.session.add(crawler_config)
        
        db.session.commit()
        logger.info(f"成功创建 {len(cls.DEFAULT_CRAWLER_CONFIGS)} 个默认爬虫配置")
    
    @classmethod
    def _init_default_report_configs(cls):
        """初始化默认报告配置"""
        # 检查是否已有报告配置
        existing_count = ReportConfig.query.count()
        if existing_count > 0:
            logger.info(f"已存在 {existing_count} 个报告配置，跳过默认配置初始化")
            return
        
        logger.info("创建默认报告配置...")
        for config_data in cls.DEFAULT_REPORT_CONFIGS:
            report_config = ReportConfig(
                name=config_data['name'],
                data_sources=config_data['data_sources'],
                filter_keywords=config_data['filter_keywords'],
                time_range=config_data['time_range'],
                purpose=config_data['purpose'],
                enable_deep_research=config_data['enable_deep_research'],
                research_focus=config_data['research_focus'],
                notification_type=config_data['notification_type'],
                webhook_url=config_data['webhook_url'],
                is_active=config_data['is_active']
            )
            db.session.add(report_config)
        
        db.session.commit()
        logger.info(f"成功创建 {len(cls.DEFAULT_REPORT_CONFIGS)} 个默认报告配置")
    
    @classmethod
    def _init_default_global_settings(cls):
        """初始化默认全局设置"""
        # 检查是否已有全局设置
        existing_settings = GlobalSettings.query.first()
        if existing_settings:
            logger.info("已存在全局设置，跳过默认设置初始化")
            return
        
        logger.info("创建默认全局设置...")
        global_settings = GlobalSettings(
            serp_api_key=cls.DEFAULT_GLOBAL_SETTINGS['serp_api_key'],
            llm_provider=cls.DEFAULT_GLOBAL_SETTINGS['llm_provider'],
            llm_base_url=cls.DEFAULT_GLOBAL_SETTINGS['llm_base_url'],
            llm_api_key=cls.DEFAULT_GLOBAL_SETTINGS['llm_api_key'],
            llm_model_name=cls.DEFAULT_GLOBAL_SETTINGS['llm_model_name']
        )
        db.session.add(global_settings)
        db.session.commit()
        logger.info("成功创建默认全局设置")
    
    @classmethod
    def restore_default_configs(cls, config_type='all'):
        """恢复默认配置
        
        Args:
            config_type (str): 配置类型 'crawler', 'report', 'global', 'all'
        """
        try:
            logger.info(f"开始恢复默认配置: {config_type}")
            
            if config_type in ['crawler', 'all']:
                cls._restore_default_crawler_configs()
            
            if config_type in ['report', 'all']:
                cls._restore_default_report_configs()
            
            if config_type in ['global', 'all']:
                cls._restore_default_global_settings()
            
            logger.info("默认配置恢复完成")
            return True
            
        except Exception as e:
            logger.error(f"恢复默认配置失败: {str(e)}")
            db.session.rollback()
            return False
    
    @classmethod
    def _restore_default_crawler_configs(cls):
        """恢复默认爬虫配置"""
        logger.info("恢复默认爬虫配置...")
        
        # 删除现有配置
        CrawlerConfig.query.delete()
        
        # 创建默认配置
        for config_data in cls.DEFAULT_CRAWLER_CONFIGS:
            crawler_config = CrawlerConfig(
                name=config_data['name'],
                list_url=config_data['list_url'],
                url_regex=config_data['url_regex'],
                frequency_seconds=config_data['frequency_seconds'],
                is_active=config_data['is_active']
            )
            db.session.add(crawler_config)
        
        db.session.commit()
        logger.info(f"成功恢复 {len(cls.DEFAULT_CRAWLER_CONFIGS)} 个默认爬虫配置")
    
    @classmethod
    def _restore_default_report_configs(cls):
        """恢复默认报告配置"""
        logger.info("恢复默认报告配置...")
        
        # 删除现有配置
        ReportConfig.query.delete()
        
        # 创建默认配置
        for config_data in cls.DEFAULT_REPORT_CONFIGS:
            report_config = ReportConfig(
                name=config_data['name'],
                data_sources=config_data['data_sources'],
                filter_keywords=config_data['filter_keywords'],
                time_range=config_data['time_range'],
                purpose=config_data['purpose'],
                enable_deep_research=config_data['enable_deep_research'],
                research_focus=config_data['research_focus'],
                notification_type=config_data['notification_type'],
                webhook_url=config_data['webhook_url'],
                is_active=config_data['is_active']
            )
            db.session.add(report_config)
        
        db.session.commit()
        logger.info(f"成功恢复 {len(cls.DEFAULT_REPORT_CONFIGS)} 个默认报告配置")
    
    @classmethod
    def _restore_default_global_settings(cls):
        """恢复默认全局设置"""
        logger.info("恢复默认全局设置...")
        
        # 删除现有设置
        GlobalSettings.query.delete()
        
        # 创建默认设置
        global_settings = GlobalSettings(
            serp_api_key=cls.DEFAULT_GLOBAL_SETTINGS['serp_api_key'],
            llm_provider=cls.DEFAULT_GLOBAL_SETTINGS['llm_provider'],
            llm_base_url=cls.DEFAULT_GLOBAL_SETTINGS['llm_base_url'],
            llm_api_key=cls.DEFAULT_GLOBAL_SETTINGS['llm_api_key'],
            llm_model_name=cls.DEFAULT_GLOBAL_SETTINGS['llm_model_name']
        )
        db.session.add(global_settings)
        db.session.commit()
        logger.info("成功恢复默认全局设置")
    
    @classmethod
    def get_config_status(cls):
        """获取配置状态"""
        return {
            'crawler_count': CrawlerConfig.query.count(),
            'report_count': ReportConfig.query.count(),
            'has_global_settings': GlobalSettings.query.first() is not None
        }
