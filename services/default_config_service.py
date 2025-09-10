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
        },
        # B端企业服务专项监控配置 - 一个关键词一条
        # 1. 竞争动态格局
        {
            "name": "B端-企业服务并购",
            "list_url": "https://news.google.com/search?q=企业服务并购&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "url_regex": r'https://[^/]+/.*',
            "frequency_seconds": 3600,
            "is_active": True
        },
        {
            "name": "B端-生态联盟",
            "list_url": "https://news.google.com/search?q=B端生态联盟&hl=zh-CN&gl=CN&ceid=CN:zh-Hans", 
            "url_regex": r'https://[^/]+/.*',
            "frequency_seconds": 3600,
            "is_active": True
        },
        {
            "name": "B端-战略合作",
            "list_url": "https://news.google.com/search?q=企业服务战略合作&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "url_regex": r'https://[^/]+/.*',
            "frequency_seconds": 3600,
            "is_active": True
        },
        # 2. 技术演进追踪
        {
            "name": "B端-AI Agent",
            "list_url": "https://news.google.com/search?q=B端AI Agent&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "url_regex": r'https://[^/]+/.*',
            "frequency_seconds": 3600,
            "is_active": True
        },
        {
            "name": "B端-无代码平台",
            "list_url": "https://news.google.com/search?q=无代码企业服务&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "url_regex": r'https://[^/]+/.*',
            "frequency_seconds": 3600,
            "is_active": True
        },
        {
            "name": "B端-SMB协议",
            "list_url": "https://news.google.com/search?q=SMB protocol&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "url_regex": r'https://[^/]+/.*',
            "frequency_seconds": 3600,
            "is_active": True
        },
        # 3. 产品创新
        {
            "name": "B端-垂直SaaS",
            "list_url": "https://news.google.com/search?q=垂直SaaS&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "url_regex": r'https://[^/]+/.*',
            "frequency_seconds": 3600,
            "is_active": True
        },
        {
            "name": "B端-设计趋势",
            "list_url": "https://news.google.com/search?q=B端设计趋势&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "url_regex": r'https://[^/]+/.*',
            "frequency_seconds": 3600,
            "is_active": True
        },
        # 4. 商业模式
        {
            "name": "B端-订阅定价",
            "list_url": "https://news.google.com/search?q=B端订阅定价&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "url_regex": r'https://[^/]+/.*',
            "frequency_seconds": 3600,
            "is_active": True
        },
        {
            "name": "B端-企业软件出海",
            "list_url": "https://news.google.com/search?q=企业软件出海&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "url_regex": r'https://[^/]+/.*',
            "frequency_seconds": 3600,
            "is_active": True
        },
        # 5. 政策变更
        {
            "name": "B端-数据合规",
            "list_url": "https://news.google.com/search?q=企业数据合规&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "url_regex": r'https://[^/]+/.*',
            "frequency_seconds": 3600,
            "is_active": True
        },
        {
            "name": "B端-国产替代",
            "list_url": "https://news.google.com/search?q=国产替代&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "url_regex": r'https://[^/]+/.*',
            "frequency_seconds": 3600,
            "is_active": True
        },
        {
            "name": "B端-国产替代",
            "list_url": "https://news.google.com/search?q=企业服务&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
            "url_regex": r'https://[^/]+/.*',
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
        },
        # B端企业服务 - 5个独立报告配置
        {
            "name": "B端竞争动态格局分析",
            "data_sources": "8,9,10",  # 企业服务并购,生态联盟,战略合作
            "filter_keywords": "企业服务并购,B端生态联盟,企业服务战略合作,新玩家入局,生态对抗",
            "time_range": "7d",
            "purpose": "监控B端企业服务领域的竞争动态变化，包括新玩家入局、战略合作并购、生态对抗等",
            "enable_deep_research": True,
            "research_focus": """🎯 **竞争动态格局深度分析**：
- 新玩家入局：产品定位、市场策略、差异化优势分析
- 战略合作/并购：交易背景、协同效应、市场影响评估
- 生态对抗：竞争策略、技术壁垒、用户迁移成本分析
- 市场格局变化：头部厂商地位变化、中小企业机会识别
- 投资机会：潜在投资标的、估值分析、风险评估""",
            "notification_type": "jinshan",
            "webhook_url": "",
            "is_active": False
        },
        {
            "name": "B端技术演进追踪报告", 
            "data_sources": "11,12,13",  # AI Agent,无代码平台,SMB协议
            "filter_keywords": "B端AI Agent,无代码企业服务,SMB protocol,区块链企业应用,隐私计算",
            "time_range": "7d",
            "purpose": "追踪B端企业服务的技术发展趋势，包括AI Agent、无代码工具、协议优化等技术演进",
            "enable_deep_research": True,
            "research_focus": """🔬 **技术演进深度追踪**：
- AI Agent生产级应用：落地场景、性能表现、商业价值分析
- 无代码工具发展：平台能力进化、兼容性提升、企业采用度
- 协议优化升级：SMB性能提升、安全增强、部署实践案例
- 区块链/隐私计算：供应链金融应用、安全合规要求、成本效益
- 技术趋势预测：新兴技术采用周期、技术成熟度评估""",
            "notification_type": "jinshan",
            "webhook_url": "",
            "is_active": False
        },
        {
            "name": "B端产品创新洞察报告",
            "data_sources": "14,15",  # 垂直SaaS,设计趋势
            "filter_keywords": "垂直SaaS,B端设计趋势,用户体验升级,硬件融合,行业专属功能",
            "time_range": "7d", 
            "purpose": "洞察B端产品创新动态，包括垂直场景方案、用户体验升级、硬件融合等产品创新",
            "enable_deep_research": True,
            "research_focus": """🚀 **产品创新深度洞察**：
- 垂直场景方案：行业专属功能开发、合规要求适配、集成能力提升
- 用户体验升级：交互设计变革、效率提升措施、学习成本降低
- 硬件融合方案：订阅模式创新、服务化趋势、成本优化策略
- 产品差异化：功能创新点、技术壁垒、用户价值主张
- 创新趋势预测：产品发展方向、市场需求变化、技术可行性""",
            "notification_type": "jinshan",
            "webhook_url": "",
            "is_active": False
        },
        {
            "name": "B端商业模式观察报告",
            "data_sources": "16,17",  # 订阅定价,企业软件出海
            "filter_keywords": "B端订阅定价,企业软件出海,SaaS商业模式,按需付费,生态扩展",
            "time_range": "7d",
            "purpose": "观察B端企业服务的商业模式变化，包括定价策略、生态扩展、出海动态等",
            "enable_deep_research": True,
            "research_focus": """💼 **商业模式深度观察**：
- 定价策略演进：分层订阅优化、按需付费模式、价值定价策略
- 生态扩展分析：平台抽成调整、开发者激励机制、生态健康度评估
- 出海动态追踪：本土化策略、合规适配要求、市场表现分析
- 盈利模式创新：收入结构变化、成本控制策略、规模效应实现
- 商业趋势预测：模式演进方向、市场机会识别、风险因素分析""",
            "notification_type": "jinshan",
            "webhook_url": "",
            "is_active": False
        },
        {
            "name": "B端政策变更解读报告",
            "data_sources": "18,19,20",  # 数据合规,国产替代,企业服务
            "filter_keywords": "企业数据合规,企业服务国产替代,隐私安全,政策法规,合规成本",
            "time_range": "7d",
            "purpose": "解读影响B端企业服务的政策变更，包括数据合规、隐私安全、国产替代等政策影响",
            "enable_deep_research": True,
            "research_focus": """📋 **政策变更深度解读**：
- 数据合规要求：最新法规要求、企业响应策略、合规成本评估
- 隐私安全标准：技术标准更新、审计要求变化、风险评估方法
- 国产替代政策：政策导向分析、市场机会识别、技术挑战评估
- 监管影响分析：合规压力评估、业务调整需求、成本收益分析
- 政策趋势预测：监管方向预判、合规准备建议、风险应对策略""",
            "notification_type": "jinshan",
            "webhook_url": "",
            "is_active": False
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
