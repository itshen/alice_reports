#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件示例
复制此文件为 config.py 并修改相应配置
"""

# Flask应用配置
class Config:
    # 安全密钥 - 生产环境请更换
    SECRET_KEY = 'your-secret-key-change-in-production'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 调试模式 - 生产环境请设为False
    DEBUG = False
    
    # 默认LLM配置
    DEFAULT_LLM_CONFIG = {
        'provider': 'qwen',
        'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        'model_name': 'qwen-plus',
        'api_key': ''  # 请在系统中配置
    }
    
    # 爬虫配置
    CRAWLER_CONFIG = {
        'default_interval_hours': 24,
        'max_articles_per_crawl': 20,
        'request_timeout': 30,
        'retry_times': 3,
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    # 报告配置
    REPORT_CONFIG = {
        'retention_days': 30,
        'max_content_length': 10000,
        'notification_timeout': 30
    }
    
    # 日志配置
    LOGGING_CONFIG = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': 'app.log'
    }

# 开发环境配置
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev.db'

# 生产环境配置  
class ProductionConfig(Config):
    DEBUG = False
    # 生产环境建议使用更安全的数据库
    # SQLALCHEMY_DATABASE_URI = 'postgresql://user:pass@localhost/dbname'

# 测试环境配置
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
