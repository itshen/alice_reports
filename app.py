#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能信息分析与报告自动化平台
主应用入口
"""

import os
import asyncio
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from datetime import datetime, timedelta
import json
import re
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# 数据库配置
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "app.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 导入数据库实例
from models import db

# 初始化数据库
db.init_app(app)

# 配置调度器
jobstores = {
    'default': SQLAlchemyJobStore(url=app.config['SQLALCHEMY_DATABASE_URI'])
}
scheduler = BackgroundScheduler(jobstores=jobstores)

# 导入模型
from models import User, GlobalSettings, CrawlerConfig, CrawlRecord, ReportConfig, ReportRecord, TaskLog

# 创建服务实例
from services.crawler_service import CrawlerService
from services.llm_service import LLMService
from services.notification_service import NotificationService
from services.default_config_service import DefaultConfigService
from services.deep_research_service import DeepResearchService

crawler_service = CrawlerService()
llm_service = LLMService()
notification_service = NotificationService()
deep_research_service = DeepResearchService(crawler_service, llm_service)

def crawler_job_wrapper(crawler_id):
    """爬虫任务包装器，用于调度器调用"""
    try:
        logger.info(f"调度器触发爬虫任务，ID: {crawler_id}")
        
        with app.app_context():
            crawler = CrawlerConfig.query.get(crawler_id)
            if not crawler:
                logger.error(f"未找到爬虫配置，ID: {crawler_id}")
                return
            
            if not crawler.is_active:
                logger.info(f"爬虫 {crawler.name} 已禁用，跳过执行")
                return
            
            # 立即更新开始执行时间
            crawler.last_run = datetime.utcnow()
            db.session.commit()
            logger.info(f"✅ 定时任务开始执行: {crawler.name}")
            
            # 在新线程中执行异步任务
            def run_async_task():
                try:
                    with app.app_context():
                        # 重新获取爬虫配置（避免会话问题）
                        current_crawler = CrawlerConfig.query.get(crawler_id)
                        if not current_crawler:
                            logger.error(f"定时任务线程中未找到爬虫配置，ID: {crawler_id}")
                            return
                        
                        results = asyncio.run(crawler_service.run_crawler_task(current_crawler))
                        if isinstance(results, dict) and results.get('success'):
                            logger.info(f"定时爬虫任务完成: {current_crawler.name}, 成功保存 {results.get('saved_count', 0)} 条记录")
                        else:
                            logger.warning(f"定时爬虫任务异常: {current_crawler.name}, 结果: {results}")
                except Exception as e:
                    logger.error(f"定时爬虫任务执行失败: 爬虫ID {crawler_id}, 错误: {e}")
                    # 即使失败也要确保有执行时间记录
                    try:
                        with app.app_context():
                            failed_crawler = CrawlerConfig.query.get(crawler_id)
                            if failed_crawler:
                                failed_crawler.last_run = datetime.utcnow()
                                db.session.commit()
                                logger.info(f"✅ 已更新失败的定时爬虫执行时间: {failed_crawler.name}")
                    except Exception as update_e:
                        logger.error(f"更新失败的定时爬虫执行时间失败: {update_e}")
            
            import threading
            thread = threading.Thread(target=run_async_task)
            thread.start()
            
    except Exception as e:
        logger.error(f"调度器任务包装器失败: {e}")

def report_job_wrapper(report_id):
    """报告任务包装器，用于调度器调用"""
    try:
        logger.info(f"调度器触发报告任务，ID: {report_id}")
        
        with app.app_context():
            report = ReportConfig.query.get(report_id)
            if not report:
                logger.error(f"未找到报告配置，ID: {report_id}")
                return
            
            if not report.is_active:
                logger.info(f"报告 {report.name} 已禁用，跳过执行")
                return
            
            if not report.enable_scheduled_push:
                logger.info(f"报告 {report.name} 未启用定时推送，跳过执行")
                return
            
            # 立即更新开始执行时间
            report.last_run = datetime.utcnow()
            db.session.commit()
            logger.info(f"✅ 定时报告任务开始执行: {report.name}")
            
            # 在新线程中执行异步任务
            def run_async_task():
                try:
                    with app.app_context():
                        # 重新获取报告配置（避免会话问题）
                        current_report = ReportConfig.query.get(report_id)
                        if not current_report:
                            logger.error(f"定时任务线程中未找到报告配置，ID: {report_id}")
                            return
                        
                        # 执行报告生成任务（复用现有逻辑）
                        generate_report_task_internal(current_report)
                        
                except Exception as e:
                    logger.error(f"定时报告任务执行失败: 报告ID {report_id}, 错误: {e}")
                    # 即使失败也要确保有执行时间记录
                    try:
                        with app.app_context():
                            failed_report = ReportConfig.query.get(report_id)
                            if failed_report:
                                failed_report.last_run = datetime.utcnow()
                                db.session.commit()
                                logger.info(f"✅ 已更新失败的定时报告执行时间: {failed_report.name}")
                    except Exception as update_e:
                        logger.error(f"更新失败的定时报告执行时间失败: {update_e}")
            
            import threading
            thread = threading.Thread(target=run_async_task)
            thread.start()
            
    except Exception as e:
        logger.error(f"调度器报告任务包装器失败: {e}")

def setup_crawler_scheduler():
    """设置爬虫自动调度任务"""
    try:
        logger.info("正在设置爬虫自动调度任务...")
        
        crawlers = CrawlerConfig.query.filter_by(is_active=True).all()
        logger.info(f"发现 {len(crawlers)} 个激活的爬虫配置")
        
        for crawler in crawlers:
            job_id = f"crawler_{crawler.id}"
            
            # 检查任务是否已存在
            existing_job = scheduler.get_job(job_id)
            if existing_job:
                logger.info(f"任务已存在，先删除: {crawler.name}")
                scheduler.remove_job(job_id)
            
            # 添加新的定时任务
            try:
                scheduler.add_job(
                    func=crawler_job_wrapper,
                    args=[crawler.id],
                    trigger='interval',
                    seconds=crawler.frequency_seconds,
                    id=job_id,
                    name=f"爬虫-{crawler.name}",
                    replace_existing=True,
                    max_instances=1  # 防止任务重叠
                )
                logger.info(f"已添加定时任务: {crawler.name} (每 {crawler.frequency_seconds//3600} 小时)")
                
            except Exception as e:
                logger.error(f"添加任务失败: {crawler.name}, 错误: {e}")
        
        # 显示所有任务
        jobs = scheduler.get_jobs()
        logger.info(f"当前调度器中的任务数量: {len(jobs)}")
        for job in jobs:
            logger.info(f"调度任务: {job.name} (ID: {job.id})")
            
    except Exception as e:
        logger.error(f"设置爬虫调度任务失败: {e}")

def generate_report_task_internal(report):
    """内部报告生成任务逻辑"""
    try:
        # 获取数据源
        if not report.data_sources:
            logger.warning(f"报告 {report.name} 没有配置数据源")
            return
        
        crawler_ids = [int(x) for x in report.data_sources.split(',') if x.strip()]
        
        # 计算时间范围
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        time_range = report.time_range
        
        if time_range == '24h':
            cutoff_time = now - timedelta(hours=24)
        elif time_range == '2d':
            cutoff_time = now - timedelta(days=2)
        elif time_range == '3d':
            cutoff_time = now - timedelta(days=3)
        elif time_range == '7d':
            cutoff_time = now - timedelta(days=7)
        elif time_range == '14d':
            cutoff_time = now - timedelta(days=14)
        elif time_range == '30d':
            cutoff_time = now - timedelta(days=30)
        else:
            cutoff_time = now - timedelta(hours=24)  # 默认24小时
        
        # 获取爬取的数据
        articles = []
        logger.info(f"准备从 {len(crawler_ids)} 个数据源获取数据，时间范围: {time_range}")
        logger.info(f"时间过滤截止点: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        for crawler_id in crawler_ids:
            # 按发布时间过滤（而不是爬取时间）
            records = CrawlRecord.query.filter(
                CrawlRecord.crawler_config_id == crawler_id,
                CrawlRecord.status == 'success',
                CrawlRecord.publish_date.isnot(None),  # 确保有发布时间
                CrawlRecord.publish_date >= cutoff_time  # 按发布时间过滤
            ).order_by(
                CrawlRecord.publish_date.desc()
            ).limit(100).all()
            
            if records:
                latest_date = max(r.publish_date for r in records if r.publish_date)
                earliest_date = min(r.publish_date for r in records if r.publish_date)
                logger.info(f"数据源 {crawler_id} 获取到 {len(records)} 条记录，时间范围: {earliest_date.strftime('%Y-%m-%d')} 到 {latest_date.strftime('%Y-%m-%d')}")
            else:
                logger.info(f"数据源 {crawler_id} 获取到 0 条记录")
            
            for record in records:
                articles.append({
                    'title': record.title,
                    'content': record.content,
                    'author': record.author,
                    'url': record.url,
                    'date': record.publish_date.isoformat() if record.publish_date else ''
                })
        
        logger.info(f"总共获取到 {len(articles)} 篇文章")
        
        # 过滤文章
        if report.filter_keywords:
            before_filter = len(articles)
            articles = llm_service.filter_articles_by_keywords(articles, report.filter_keywords)
            logger.info(f"关键词过滤: {before_filter} -> {len(articles)} 篇文章，关键词: {report.filter_keywords}")
        
        # 生成报告
        if report.enable_deep_research:
            # 使用优化后的深度研究服务
            # 获取全局设置
            settings = GlobalSettings.query.first()
            if not settings:
                raise Exception("未找到全局设置")
            
            # 确保LLM服务配置正确
            llm_service.update_settings(settings)
            
            # 执行深度研究
            result = asyncio.run(deep_research_service.conduct_deep_research(report, settings))
            
            if result['success']:
                content = result['report']
                
                # 保存详细的研究日志
                research_log = result.get('research_log', [])
                iterations = result.get('iterations', 0)
                knowledge_base_size = result.get('knowledge_base_size', 0)
                
                logger.info(f"深度研究完成: {iterations}轮迭代, {knowledge_base_size}篇文章, {len(research_log)}条日志")
            else:
                raise Exception(f"深度研究失败: {result['message']}")
        else:
            logger.info(f"生成常规报告，使用 {len(articles)} 篇文章")
            # 确保LLM服务配置正确
            settings = GlobalSettings.query.first()
            if not settings:
                raise Exception("未找到全局设置")
            
            llm_service.update_settings(settings)
            content = llm_service.generate_simple_report(articles, report)
            logger.info(f"常规报告生成完成，长度: {len(content)} 字符")
        
        # 保存报告记录
        record = ReportRecord(
            report_config_id=report.id,
            title=f"{report.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            content=content,
            summary=content[:200] + '...' if len(content) > 200 else content,
            status='success'
        )
        db.session.add(record)
        
        # 发送通知
        logger.info(f"检查推送配置 - webhook_url: {bool(report.webhook_url)}, notification_type: {report.notification_type}")
        
        if report.webhook_url:
            logger.info(f"开始推送通知到 {report.notification_type}")
            
            if report.enable_deep_research:
                notification_content = notification_service.format_deep_research_for_notification(content)
            else:
                notification_content = notification_service.format_simple_report_for_notification(content)
            
            success = notification_service.send_notification(
                report.notification_type,
                report.webhook_url,
                notification_content,
                record.title
            )
            record.notification_sent = success
            logger.info(f"推送结果: {'成功' if success else '失败'}")
        else:
            logger.info("未配置 webhook_url，跳过推送")
            record.notification_sent = False
        
        report.last_run = datetime.utcnow()
        db.session.commit()
        
    except Exception as e:
        logger.error(f"生成报告任务失败: {e}")
        # 保存失败记录
        record = ReportRecord(
            report_config_id=report.id,
            title=f"{report.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')} (失败)",
            status='failed',
            error_message=str(e)
        )
        db.session.add(record)
        db.session.commit()
        raise

def setup_report_scheduler():
    """设置报告定时推送任务"""
    try:
        logger.info("正在设置报告定时推送任务...")
        
        reports = ReportConfig.query.filter_by(is_active=True, enable_scheduled_push=True).all()
        logger.info(f"发现 {len(reports)} 个启用定时推送的报告配置")
        
        for report in reports:
            update_report_job(report)
        
        # 显示所有任务
        jobs = scheduler.get_jobs()
        report_jobs = [job for job in jobs if job.id.startswith('report_')]
        logger.info(f"当前报告定时任务数量: {len(report_jobs)}")
        for job in report_jobs:
            logger.info(f"报告定时任务: {job.name} (ID: {job.id})")
            
    except Exception as e:
        logger.error(f"设置报告定时任务失败: {e}")

def create_tables():
    """创建数据库表"""
    db.create_all()
    
    # 初始化默认用户
    logger.info("正在检查默认用户...")
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(username='admin')
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        logger.info("已创建默认管理员用户: admin/admin123")
    else:
        logger.info("默认管理员用户已存在")
    
    # 初始化默认配置
    logger.info("正在初始化默认配置...")
    DefaultConfigService.init_default_configs()
    logger.info("默认配置初始化完成")
    
    # 设置爬虫自动调度
    setup_crawler_scheduler()
    
    # 设置报告定时推送
    setup_report_scheduler()

# 认证装饰器
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 路由定义
@app.route('/')
def index():
    """首页重定向到登录页"""
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 查找用户
        user = User.query.filter_by(username=username, is_active=True).first()
        
        if user and user.check_password(password):
            session['logged_in'] = True
            session['username'] = username
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """退出登录"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/change-password')
@login_required
def change_password_page():
    """修改密码页面"""
    return render_template('change_password.html')

@app.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    """修改密码API"""
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # 验证输入
        if not current_password or not new_password or not confirm_password:
            return jsonify({'success': False, 'message': '所有字段都必须填写'})
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': '新密码和确认密码不匹配'})
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': '新密码长度至少6位'})
        
        # 获取当前用户
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        # 验证当前密码
        if not user.check_password(current_password):
            return jsonify({'success': False, 'message': '当前密码错误'})
        
        # 更新密码
        user.set_password(new_password)
        db.session.commit()
        
        logger.info(f"用户 {user.username} 成功修改密码")
        
        return jsonify({'success': True, 'message': '密码修改成功'})
    
    except Exception as e:
        logger.error(f"修改密码失败: {e}")
        return jsonify({'success': False, 'message': '修改密码失败，请重试'}), 500

@app.route('/dashboard')
@login_required
def dashboard():
    """系统主页面"""
    return render_template('dashboard.html')

@app.route('/global-settings', methods=['GET', 'POST'])
@login_required
def global_settings():
    """全局设置页面"""
    settings = GlobalSettings.query.first()
    
    if request.method == 'POST':
        if not settings:
            settings = GlobalSettings()
        
        settings.serp_api_key = request.form.get('serp_api_key', '')
        settings.llm_provider = request.form.get('llm_provider', 'qwen')
        settings.llm_base_url = request.form.get('llm_base_url', '')
        settings.llm_api_key = request.form.get('llm_api_key', '')
        settings.llm_model_name = request.form.get('llm_model_name', '')
        
        if not settings.id:
            db.session.add(settings)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '设置已成功保存'})
    
    return render_template('global_settings.html', settings=settings)

@app.route('/api/test-llm-connection', methods=['POST'])
@login_required
def test_llm_connection():
    """测试LLM连接"""
    try:
        # 从表单获取测试参数
        llm_provider = request.form.get('llm_provider', 'qwen')
        llm_base_url = request.form.get('llm_base_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        llm_api_key = request.form.get('llm_api_key', '')
        llm_model_name = request.form.get('llm_model_name', 'qwen-plus')
        
        if not llm_api_key:
            return jsonify({
                'success': False,
                'message': '请先填写API Key'
            })
        
        # 创建临时设置对象用于测试
        class TempSettings:
            def __init__(self):
                self.llm_provider = llm_provider
                self.llm_base_url = llm_base_url
                self.llm_api_key = llm_api_key
                self.llm_model_name = llm_model_name
        
        temp_settings = TempSettings()
        
        # 使用LLM服务进行连接测试
        result = llm_service.test_connection(temp_settings)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"测试LLM连接失败: {e}")
        return jsonify({
            'success': False,
            'message': f'测试失败: {str(e)}'
        })

@app.route('/crawler-config')
@login_required
def crawler_config_list():
    """爬虫配置列表页"""
    # 如果是Dashboard请求，返回页面内容
    if request.args.get('dashboard') == '1':
        crawlers = CrawlerConfig.query.order_by(CrawlerConfig.created_at.desc()).all()
        return render_template('crawler_config_list.html', crawlers=crawlers)
    # 否则重定向到 Dashboard
    return redirect('/dashboard#crawler-config')

@app.route('/crawler-config/new')
@login_required
def crawler_config_new():
    """新建爬虫配置页 - 重定向到Dashboard"""
    return redirect('/dashboard#crawler-config-new')

@app.route('/crawler-config/<int:crawler_id>')
@login_required
def crawler_config_detail(crawler_id):
    """编辑爬虫配置页 - 重定向到Dashboard"""
    return redirect(f'/dashboard#crawler-config-edit-{crawler_id}')

@app.route('/crawler-config/<int:crawler_id>/edit')
@login_required
def crawler_config_edit(crawler_id):
    """编辑爬虫配置页 - 重定向到Dashboard"""
    return redirect(f'/dashboard#crawler-config-edit-{crawler_id}')

@app.route('/crawler-config/<int:crawler_id>/results')
@login_required
def crawler_results(crawler_id):
    """查看爬虫抓取结果"""
    crawler = CrawlerConfig.query.get_or_404(crawler_id)
    # 获取最近的抓取记录，按发布时间倒序（最新的文章在前面）
    records = CrawlRecord.query.filter_by(crawler_config_id=crawler_id)\
                              .order_by(
                                  CrawlRecord.publish_date.desc().nulls_last(),
                                  CrawlRecord.created_at.desc()
                              )\
                              .limit(50).all()
    
    # 检查是否是 Dashboard 内的 AJAX 请求
    if request.args.get('dashboard') == '1':
        # 返回 Dashboard 内嵌版本（只有内容部分）
        return render_template('crawler_results_dashboard.html', crawler=crawler, records=records)
    else:
        # 直接访问时，重定向到 Dashboard 并设置正确的 hash
        return redirect(f'/dashboard#crawler-results-{crawler_id}')

@app.route('/api/crawler-config/new-form')
@login_required
def crawler_config_new_form():
    """获取新建爬虫配置表单"""
    return render_template('crawler_config_detail.html', crawler=None)

@app.route('/api/crawler-config/<int:crawler_id>/edit-form')
@login_required
def crawler_config_edit_form(crawler_id):
    """获取编辑爬虫配置表单"""
    crawler = CrawlerConfig.query.get_or_404(crawler_id)
    return render_template('crawler_config_detail.html', crawler=crawler)

def update_crawler_job(crawler):
    """更新单个爬虫的调度任务"""
    try:
        job_id = f"crawler_{crawler.id}"
        
        # 删除旧任务
        existing_job = scheduler.get_job(job_id)
        if existing_job:
            scheduler.remove_job(job_id)
            logger.info(f"已删除旧调度任务: {crawler.name}")
        
        # 如果爬虫处于激活状态，添加新任务
        if crawler.is_active:
            scheduler.add_job(
                func=crawler_job_wrapper,
                args=[crawler.id],
                trigger='interval',
                seconds=crawler.frequency_seconds,
                id=job_id,
                name=f"爬虫-{crawler.name}",
                replace_existing=True,
                max_instances=1
            )
            logger.info(f"已更新调度任务: {crawler.name} (每 {crawler.frequency_seconds//3600} 小时)")
        else:
            logger.info(f"爬虫已禁用，不添加调度任务: {crawler.name}")
            
    except Exception as e:
        logger.error(f"更新爬虫调度任务失败: {crawler.name}, 错误: {e}")

@app.route('/api/crawler-config', methods=['POST'])
@login_required
def save_crawler_config():
    """保存爬虫配置"""
    try:
        data = request.get_json()
        
        crawler_id = data.get('id')
        if crawler_id:
            crawler = CrawlerConfig.query.get(crawler_id)
        else:
            crawler = CrawlerConfig()
        
        crawler.name = data.get('name')
        crawler.list_url = data.get('list_url')
        crawler.url_regex = data.get('url_regex')
        crawler.frequency_seconds = int(data.get('frequency_seconds', 3600))
        
        if not crawler.id:
            db.session.add(crawler)
        
        db.session.commit()
        
        # 更新调度任务
        update_crawler_job(crawler)
        
        return jsonify({'success': True, 'message': '保存成功', 'id': crawler.id})
    
    except Exception as e:
        logger.error(f"保存爬虫配置失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/crawler-config/<int:crawler_id>/test-connection', methods=['POST'])
@login_required
def test_crawler_connection(crawler_id):
    """测试爬虫连接"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        # 使用爬虫服务测试连接
        result = asyncio.run(crawler_service.test_connection(url))
        
        return jsonify({
            'success': True,
            'content': result['content'],  # 返回完整内容
            'links': result['links'][:50]  # 限制链接数量
        })
    
    except Exception as e:
        logger.error(f"测试连接失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/crawler-config/preview-urls', methods=['POST'])
@login_required
def preview_urls():
    """预览URL列表"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        regex = data.get('regex', '')
        
        if not regex:
            return jsonify({'success': True, 'urls': []})
        
        # 验证并使用正则表达式匹配URL
        try:
            pattern = re.compile(regex)
            matches = pattern.findall(content)
            
            # 调试信息
            logger.info(f"正则表达式: {regex}")
            logger.info(f"匹配到 {len(matches)} 个结果")
            
            # 去重并限制数量
            urls = list(set(matches))[:50]  # 增加到50个
            
        except re.error as e:
            logger.error(f"正则表达式语法错误: {e}, 正则表达式: {regex}")
            return jsonify({
                'success': False, 
                'message': f'正则表达式语法错误: {str(e)}'
            })
        
        return jsonify({'success': True, 'urls': urls})
    
    except Exception as e:
        logger.error(f"预览URL失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/crawler-config/generate-regex', methods=['POST'])
@login_required
def generate_regex_with_ai():
    """使用AI生成正则表达式"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        url = data.get('url', '')
        requirement = data.get('requirement', '匹配文章详情页链接')
        
        if not content:
            return jsonify({'success': False, 'message': '页面内容为空'})
        
        # 获取全局设置
        settings = GlobalSettings.query.first()
        if not settings or not settings.llm_api_key:
            return jsonify({'success': False, 'message': '请先配置LLM设置'})
        
        # 使用LLM服务生成正则表达式
        result = llm_service.generate_url_regex(settings, content, url, requirement)
        
        if result['success']:
            # 在返回前再次验证正则表达式
            try:
                import re
                re.compile(result['regex'])
                return jsonify({
                    'success': True,
                    'regex': result['regex'],
                    'explanation': result.get('explanation', '')
                })
            except re.error as e:
                logger.error(f"最终正则表达式验证失败: {e}")
                return jsonify({
                    'success': False, 
                    'message': f'AI生成的正则表达式语法错误: {str(e)}，请手动输入或重新生成'
                })
        else:
            return jsonify({'success': False, 'message': result['message']})
    
    except Exception as e:
        logger.error(f"AI生成正则表达式失败: {e}")
        return jsonify({'success': False, 'message': f'生成失败: {str(e)}'}), 500

@app.route('/api/crawler-config/test-crawling', methods=['POST'])
@login_required
def test_crawling():
    """测试抓取URL内容"""
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        base_url = data.get('base_url', '')
        
        if not urls:
            return jsonify({'success': False, 'message': '没有要测试的URL'})
        
        # 限制测试数量，避免超时
        test_urls = urls[:5]
        results = []
        
        for url in test_urls:
            try:
                # 如果URL是相对路径，转换为绝对路径
                if url.startswith('/'):
                    from urllib.parse import urljoin
                    full_url = urljoin(base_url, url)
                else:
                    full_url = url
                
                # 使用爬虫服务抓取内容
                result = asyncio.run(crawler_service.crawl_article_content(full_url))
                
                if result['success']:
                    results.append({
                        'url': full_url,
                        'success': True,
                        'title': result.get('title', ''),
                        'content': result.get('content', ''),
                        'author': result.get('author', ''),
                        'date': result.get('date', '')
                    })
                else:
                    results.append({
                        'url': full_url,
                        'success': False,
                        'error': result.get('error', '抓取失败')
                    })
                    
            except Exception as e:
                logger.error(f"测试抓取URL {url} 失败: {e}")
                results.append({
                    'url': url,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        logger.error(f"测试抓取失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/report-config')
@login_required
def report_config_list():
    """报告配置列表页"""
    # 如果是Dashboard请求，返回页面内容
    if request.args.get('dashboard') == '1':
        reports = ReportConfig.query.order_by(ReportConfig.created_at.desc()).all()
        return render_template('report_config_list.html', reports=reports)
    # 否则重定向到 Dashboard
    return redirect('/dashboard#report-config')

@app.route('/report-config/new')
@login_required
def report_config_new():
    """新建报告配置页 - 重定向到Dashboard"""
    return redirect('/dashboard#report-config-new')

@app.route('/report-config/<int:report_id>')
@login_required
def report_config_detail(report_id):
    """编辑报告配置页 - 重定向到Dashboard"""
    return redirect(f'/dashboard#report-config-edit-{report_id}')

@app.route('/api/report-config/new-form')
@login_required
def report_config_new_form():
    """获取新建报告配置表单"""
    crawlers = CrawlerConfig.query.all()
    return render_template('report_config_detail.html', report=None, crawlers=crawlers)

@app.route('/api/report-config/<int:report_id>/edit-form')
@login_required
def report_config_edit_form(report_id):
    """获取编辑报告配置表单"""
    report = ReportConfig.query.get_or_404(report_id)
    crawlers = CrawlerConfig.query.all()
    return render_template('report_config_detail.html', report=report, crawlers=crawlers)

def update_report_job(report):
    """更新单个报告的定时推送任务"""
    try:
        job_id = f"report_{report.id}"
        
        # 删除旧任务
        existing_job = scheduler.get_job(job_id)
        if existing_job:
            scheduler.remove_job(job_id)
            logger.info(f"已删除旧的报告定时任务: {report.name}")
        
        # 如果启用了定时推送，添加新任务
        if report.is_active and report.enable_scheduled_push and report.schedule_weekdays and report.schedule_time:
            # 解析工作日配置
            weekdays = [int(day.strip()) for day in report.schedule_weekdays.split(',') if day.strip()]
            # 转换为cron格式的星期（0=周日，1=周一...6=周六）
            cron_weekdays = [(day % 7) for day in weekdays]
            
            # 解析时间
            try:
                hour, minute = map(int, report.schedule_time.split(':'))
            except ValueError:
                logger.error(f"报告 {report.name} 的时间格式错误: {report.schedule_time}")
                return
            
            scheduler.add_job(
                func=report_job_wrapper,
                args=[report.id],
                trigger='cron',
                hour=hour,
                minute=minute,
                day_of_week=','.join(map(str, cron_weekdays)),
                timezone='Asia/Shanghai',  # 使用+8时区
                id=job_id,
                name=f"报告-{report.name}",
                replace_existing=True,
                max_instances=1
            )
            
            weekday_names = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
            selected_days = [weekday_names[day % 7] for day in weekdays]
            logger.info(f"已添加报告定时任务: {report.name} ({','.join(selected_days)} {report.schedule_time})")
        else:
            logger.info(f"报告定时推送已禁用或配置不完整: {report.name}")
            
    except Exception as e:
        logger.error(f"更新报告定时任务失败: {report.name}, 错误: {e}")

@app.route('/api/report-config', methods=['POST'])
@login_required
def save_report_config():
    """保存报告配置"""
    try:
        data = request.get_json()
        
        report_id = data.get('id')
        if report_id:
            report = ReportConfig.query.get(report_id)
        else:
            report = ReportConfig()
        
        report.name = data.get('name')
        report.data_sources = ','.join(map(str, data.get('data_sources', [])))
        report.filter_keywords = data.get('filter_keywords', '')
        report.time_range = data.get('time_range', '24h')
        report.purpose = data.get('purpose', '')
        report.enable_deep_research = data.get('enable_deep_research', False)
        report.research_focus = data.get('research_focus', '')
        report.notification_type = data.get('notification_type', 'wechat')
        report.webhook_url = data.get('webhook_url', '')
        
        # 定时推送配置
        report.enable_scheduled_push = data.get('enable_scheduled_push', False)
        report.schedule_weekdays = data.get('schedule_weekdays', '1,2,3,4,5')
        report.schedule_time = data.get('schedule_time', '09:00')
        report.timezone = data.get('timezone', 'Asia/Shanghai')
        
        if not report.id:
            db.session.add(report)
        
        db.session.commit()
        
        # 更新定时任务
        update_report_job(report)
        
        return jsonify({'success': True, 'message': '保存成功', 'id': report.id})
    
    except Exception as e:
        logger.error(f"保存报告配置失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/crawler-config/<int:crawler_id>/toggle', methods=['POST'])
@login_required
def toggle_crawler_status(crawler_id):
    """切换爬虫状态"""
    try:
        data = request.get_json()
        is_active = data.get('is_active', False)
        
        crawler = CrawlerConfig.query.get_or_404(crawler_id)
        crawler.is_active = is_active
        db.session.commit()
        
        # 更新调度任务
        update_crawler_job(crawler)
        
        return jsonify({'success': True, 'message': '状态更新成功'})
    
    except Exception as e:
        logger.error(f"切换爬虫状态失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/crawler-config/<int:crawler_id>/run-once', methods=['POST'])
@login_required
def run_crawler_once(crawler_id):
    """立即执行一次爬虫"""
    try:
        crawler = CrawlerConfig.query.get_or_404(crawler_id)
        
        # 立即更新开始执行时间
        crawler.last_run = datetime.utcnow()
        db.session.commit()
        logger.info(f"✅ 已更新爬虫 {crawler.name} 的开始执行时间")
        
        # 在后台执行爬虫任务
        def run_crawler_task():
            try:
                logger.info(f"开始启动爬虫线程: {crawler.name}")
                
                with app.app_context():
                    try:
                        # 重新获取爬虫配置（避免会话问题）
                        current_crawler = CrawlerConfig.query.get(crawler_id)
                        if not current_crawler:
                            logger.error(f"线程中未找到爬虫配置，ID: {crawler_id}")
                            return
                        
                        logger.info(f"线程中执行爬虫任务: {current_crawler.name}")
                        results = asyncio.run(crawler_service.run_crawler_task(current_crawler))
                        
                        # 新的爬虫服务已经在爬取过程中边爬边存了
                        if isinstance(results, dict) and results.get('success'):
                            logger.info(f"爬虫任务完成: 成功保存 {results.get('saved_count', 0)} 条记录，失败 {results.get('failed_count', 0)} 条")
                        else:
                            # 兼容旧的返回格式（如果有的话）
                            logger.info(f"爬虫任务完成，结果格式: {type(results)}")
                        
                    except Exception as e:
                        logger.error(f"执行爬虫任务失败: {e}")
                        logger.exception("详细错误信息:")
                        # 即使失败也要确保有执行时间记录
                        try:
                            with app.app_context():
                                failed_crawler = CrawlerConfig.query.get(crawler_id)
                                if failed_crawler:
                                    failed_crawler.last_run = datetime.utcnow()
                                    db.session.commit()
                                    logger.info(f"✅ 已更新失败爬虫 {failed_crawler.name} 的执行时间")
                        except Exception as update_e:
                            logger.error(f"更新失败爬虫执行时间失败: {update_e}")
                        
            except Exception as e:
                logger.error(f"爬虫线程启动失败: {e}")
                logger.exception("线程错误详情:")
        
        # 使用线程执行任务
        import threading
        thread = threading.Thread(target=run_crawler_task)
        thread.start()
        
        return jsonify({'success': True, 'message': '爬虫任务已启动'})
    
    except Exception as e:
        logger.error(f"启动爬虫任务失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/crawler-config/<int:crawler_id>', methods=['DELETE'])
@login_required
def delete_crawler_config(crawler_id):
    """删除爬虫配置"""
    try:
        crawler = CrawlerConfig.query.get_or_404(crawler_id)
        
        # 先删除调度任务
        job_id = f"crawler_{crawler_id}"
        existing_job = scheduler.get_job(job_id)
        if existing_job:
            scheduler.remove_job(job_id)
            logger.info(f"已删除调度任务: {crawler.name}")
        
        db.session.delete(crawler)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '删除成功'})
    
    except Exception as e:
        logger.error(f"删除爬虫配置失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/report-config/<int:report_id>/toggle', methods=['POST'])
@login_required
def toggle_report_status(report_id):
    """切换报告状态"""
    try:
        data = request.get_json()
        is_active = data.get('is_active', False)
        
        report = ReportConfig.query.get_or_404(report_id)
        report.is_active = is_active
        db.session.commit()
        
        # 更新定时任务
        update_report_job(report)
        
        return jsonify({'success': True, 'message': '状态更新成功'})
    
    except Exception as e:
        logger.error(f"切换报告状态失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/report-config/<int:report_id>/generate-once', methods=['POST'])
@login_required
def generate_report_once(report_id):
    """立即生成一次报告"""
    try:
        report = ReportConfig.query.get_or_404(report_id)
        
        # 在后台执行报告生成任务
        def generate_report_task():
            try:
                with app.app_context():
                    # 获取数据源
                    if not report.data_sources:
                        return
                    
                    crawler_ids = [int(x) for x in report.data_sources.split(',') if x.strip()]
                    
                    # 计算时间范围
                    from datetime import datetime, timedelta
                    now = datetime.utcnow()
                    time_range = report.time_range
                    
                    if time_range == '24h':
                        cutoff_time = now - timedelta(hours=24)
                    elif time_range == '2d':
                        cutoff_time = now - timedelta(days=2)
                    elif time_range == '3d':
                        cutoff_time = now - timedelta(days=3)
                    elif time_range == '7d':
                        cutoff_time = now - timedelta(days=7)
                    elif time_range == '14d':
                        cutoff_time = now - timedelta(days=14)
                    elif time_range == '30d':
                        cutoff_time = now - timedelta(days=30)
                    else:
                        cutoff_time = now - timedelta(hours=24)  # 默认24小时
                    
                    # 获取爬取的数据
                    articles = []
                    logger.info(f"准备从 {len(crawler_ids)} 个数据源获取数据，时间范围: {time_range}")
                    logger.info(f"时间过滤截止点: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    for crawler_id in crawler_ids:
                        # 按发布时间过滤（而不是爬取时间）
                        records = CrawlRecord.query.filter(
                            CrawlRecord.crawler_config_id == crawler_id,
                            CrawlRecord.status == 'success',
                            CrawlRecord.publish_date.isnot(None),  # 确保有发布时间
                            CrawlRecord.publish_date >= cutoff_time  # 按发布时间过滤
                        ).order_by(
                            CrawlRecord.publish_date.desc()
                        ).limit(100).all()
                        
                        if records:
                            latest_date = max(r.publish_date for r in records if r.publish_date)
                            earliest_date = min(r.publish_date for r in records if r.publish_date)
                            logger.info(f"数据源 {crawler_id} 获取到 {len(records)} 条记录，时间范围: {earliest_date.strftime('%Y-%m-%d')} 到 {latest_date.strftime('%Y-%m-%d')}")
                        else:
                            logger.info(f"数据源 {crawler_id} 获取到 0 条记录")
                        
                        for record in records:
                            articles.append({
                                'title': record.title,
                                'content': record.content,
                                'author': record.author,
                                'url': record.url,
                                'date': record.publish_date.isoformat() if record.publish_date else ''
                            })
                    
                    logger.info(f"总共获取到 {len(articles)} 篇文章")
                    
                    # 过滤文章
                    if report.filter_keywords:
                        before_filter = len(articles)
                        articles = llm_service.filter_articles_by_keywords(articles, report.filter_keywords)
                        logger.info(f"关键词过滤: {before_filter} -> {len(articles)} 篇文章，关键词: {report.filter_keywords}")
                    
                    # 生成报告
                    if report.enable_deep_research:
                        # 使用优化后的深度研究服务
                        # 获取全局设置
                        settings = GlobalSettings.query.first()
                        if not settings:
                            raise Exception("未找到全局设置")
                        
                        # 确保LLM服务配置正确
                        llm_service.update_settings(settings)
                        
                        # 执行深度研究
                        result = asyncio.run(deep_research_service.conduct_deep_research(report, settings))
                        
                        if result['success']:
                            content = result['report']
                            
                            # 保存详细的研究日志
                            research_log = result.get('research_log', [])
                            iterations = result.get('iterations', 0)
                            knowledge_base_size = result.get('knowledge_base_size', 0)
                            
                            logger.info(f"深度研究完成: {iterations}轮迭代, {knowledge_base_size}篇文章, {len(research_log)}条日志")
                        else:
                            raise Exception(f"深度研究失败: {result['message']}")
                    else:
                        logger.info(f"生成常规报告，使用 {len(articles)} 篇文章")
                        # 确保LLM服务配置正确
                        settings = GlobalSettings.query.first()
                        if not settings:
                            raise Exception("未找到全局设置")
                        
                        llm_service.update_settings(settings)
                        content = llm_service.generate_simple_report(articles, report)
                        logger.info(f"常规报告生成完成，长度: {len(content)} 字符")
                    
                    # 保存报告记录
                    record = ReportRecord(
                        report_config_id=report.id,
                        title=f"{report.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        content=content,
                        summary=content[:200] + '...' if len(content) > 200 else content,
                        status='success'
                    )
                    db.session.add(record)
                    
                    # 发送通知
                    logger.info(f"检查推送配置 - webhook_url: {bool(report.webhook_url)}, notification_type: {report.notification_type}")
                    
                    if report.webhook_url:
                        logger.info(f"开始推送通知到 {report.notification_type}")
                        
                        if report.enable_deep_research:
                            notification_content = notification_service.format_deep_research_for_notification(content)
                        else:
                            notification_content = notification_service.format_simple_report_for_notification(content)
                        
                        success = notification_service.send_notification(
                            report.notification_type,
                            report.webhook_url,
                            notification_content,
                            record.title
                        )
                        record.notification_sent = success
                        logger.info(f"推送结果: {'成功' if success else '失败'}")
                    else:
                        logger.info("未配置 webhook_url，跳过推送")
                        record.notification_sent = False
                    
                    report.last_run = datetime.utcnow()
                    db.session.commit()
                
            except Exception as e:
                logger.error(f"生成报告任务失败: {e}")
                with app.app_context():
                    # 保存失败记录
                    record = ReportRecord(
                        report_config_id=report.id,
                        title=f"{report.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')} (失败)",
                        status='failed',
                        error_message=str(e)
                    )
                    db.session.add(record)
                    db.session.commit()
        
        # 使用线程执行任务
        import threading
        thread = threading.Thread(target=generate_report_task)
        thread.start()
        
        return jsonify({'success': True, 'message': '报告生成任务已启动'})
    
    except Exception as e:
        logger.error(f"启动报告生成任务失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/report-config/<int:report_id>', methods=['DELETE'])
@login_required
def delete_report_config(report_id):
    """删除报告配置"""
    try:
        report = ReportConfig.query.get_or_404(report_id)
        
        # 先删除定时任务
        job_id = f"report_{report_id}"
        existing_job = scheduler.get_job(job_id)
        if existing_job:
            scheduler.remove_job(job_id)
            logger.info(f"已删除报告定时任务: {report.name}")
        
        db.session.delete(report)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '删除成功'})
    
    except Exception as e:
        logger.error(f"删除报告配置失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/report-config/<int:report_id>/copy', methods=['POST'])
@login_required
def copy_report_config(report_id):
    """复制报告配置"""
    try:
        # 获取原始报告配置
        original_report = ReportConfig.query.get_or_404(report_id)
        
        # 创建新的报告配置
        copied_report = ReportConfig(
            name=f"{original_report.name} - 副本",
            data_sources=original_report.data_sources,
            filter_keywords=original_report.filter_keywords,
            time_range=original_report.time_range,
            purpose=original_report.purpose,
            enable_deep_research=original_report.enable_deep_research,
            research_focus=original_report.research_focus,
            notification_type=original_report.notification_type,
            webhook_url=original_report.webhook_url,
            is_active=False,  # 复制的配置默认为非激活状态
            enable_scheduled_push=original_report.enable_scheduled_push,
            schedule_weekdays=original_report.schedule_weekdays,
            schedule_time=original_report.schedule_time,
            timezone=original_report.timezone
        )
        
        db.session.add(copied_report)
        db.session.commit()
        
        logger.info(f"成功复制报告配置: {original_report.name} -> {copied_report.name}")
        
        return jsonify({
            'success': True, 
            'message': '复制成功', 
            'id': copied_report.id,
            'name': copied_report.name
        })
    
    except Exception as e:
        logger.error(f"复制报告配置失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/report-config/<int:report_id>/history')
@login_required
def get_report_history(report_id):
    """获取报告历史记录"""
    try:
        records = ReportRecord.query.filter_by(report_config_id=report_id)\
                                  .order_by(ReportRecord.generated_at.desc())\
                                  .limit(20).all()
        
        history = []
        for record in records:
            history.append({
                'id': record.id,
                'title': record.title,
                'summary': record.summary,
                'content': record.content,
                'status': record.status,
                'generated_at': record.generated_at.strftime('%Y-%m-%d %H:%M:%S'),
                'notification_sent': record.notification_sent
            })
        
        return jsonify({'success': True, 'records': history})
    
    except Exception as e:
        logger.error(f"获取报告历史失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/test-webhook', methods=['POST'])
@login_required
def test_webhook():
    """测试Webhook"""
    try:
        data = request.get_json()
        notification_type = data.get('notification_type')
        webhook_url = data.get('webhook_url')
        
        result = notification_service.test_webhook(notification_type, webhook_url)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"测试Webhook失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/restore-default-configs', methods=['POST'])
@login_required
def restore_default_configs():
    """恢复默认配置"""
    try:
        config_type = request.json.get('config_type', 'all')
        
        logger.info(f"开始恢复默认配置: {config_type}")
        
        success = DefaultConfigService.restore_default_configs(config_type)
        
        if success:
            message = f"成功恢复{config_type}默认配置"
            if config_type == 'all':
                message = "成功恢复所有默认配置"
            elif config_type == 'crawler':
                message = "成功恢复爬虫默认配置"
            elif config_type == 'report':
                message = "成功恢复报告默认配置"
            
            logger.info(message)
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': '恢复默认配置失败，请查看日志'}), 500
            
    except Exception as e:
        logger.error(f"恢复默认配置失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        create_tables()
    
    # 启动调度器
    scheduler.start()
    
    # 启动Flask应用
    app.run(debug=True, host='0.0.0.0', port=8866)
