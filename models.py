#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模型定义
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# 创建数据库实例
db = SQLAlchemy()

class GlobalSettings(db.Model):
    """全局设置表"""
    __tablename__ = 'global_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    serp_api_key = db.Column(db.String(255), default='')
    llm_provider = db.Column(db.String(50), default='qwen')
    llm_base_url = db.Column(db.String(255), default='')
    llm_api_key = db.Column(db.String(255), default='')
    llm_model_name = db.Column(db.String(100), default='qwen-plus')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CrawlerConfig(db.Model):
    """爬虫配置表"""
    __tablename__ = 'crawler_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    list_url = db.Column(db.String(500), nullable=False)
    url_regex = db.Column(db.Text, nullable=False)
    frequency_seconds = db.Column(db.Integer, default=3600)  # 执行频率（秒），默认1小时
    is_active = db.Column(db.Boolean, default=True)
    last_run = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联的爬取记录
    crawl_records = db.relationship('CrawlRecord', backref='crawler_config', lazy=True, cascade='all, delete-orphan')

class CrawlRecord(db.Model):
    """爬取记录表"""
    __tablename__ = 'crawl_records'
    
    id = db.Column(db.Integer, primary_key=True)
    crawler_config_id = db.Column(db.Integer, db.ForeignKey('crawler_configs.id'), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    author = db.Column(db.String(100))
    publish_date = db.Column(db.DateTime)
    crawled_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='success')  # success, failed
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ReportConfig(db.Model):
    """报告配置表"""
    __tablename__ = 'report_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    data_sources = db.Column(db.Text)  # 存储爬虫ID列表，逗号分隔
    filter_keywords = db.Column(db.Text)  # 过滤关键词，逗号分隔
    time_range = db.Column(db.String(20), default='24h')  # 24h, 3d, 7d, 30d
    purpose = db.Column(db.Text)
    enable_deep_research = db.Column(db.Boolean, default=False)
    research_focus = db.Column(db.Text)
    notification_type = db.Column(db.String(20), default='wechat')  # wechat, jinshan
    webhook_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    last_run = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联的报告记录
    report_records = db.relationship('ReportRecord', backref='report_config', lazy=True, cascade='all, delete-orphan')

class ReportRecord(db.Model):
    """报告记录表"""
    __tablename__ = 'report_records'
    
    id = db.Column(db.Integer, primary_key=True)
    report_config_id = db.Column(db.Integer, db.ForeignKey('report_configs.id'), nullable=False)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    summary = db.Column(db.Text)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='success')  # success, failed, generating
    error_message = db.Column(db.Text)
    notification_sent = db.Column(db.Boolean, default=False)

class TaskLog(db.Model):
    """任务日志表"""
    __tablename__ = 'task_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    task_type = db.Column(db.String(50), nullable=False)  # crawler, report
    task_id = db.Column(db.Integer, nullable=False)  # 对应的任务ID
    message = db.Column(db.Text)
    level = db.Column(db.String(20), default='info')  # info, warning, error
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 这个文件将在app.py中被导入，db实例会被设置
