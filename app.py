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
from models import GlobalSettings, CrawlerConfig, CrawlRecord, ReportConfig, ReportRecord, TaskLog

# 创建服务实例
from services.crawler_service import CrawlerService
from services.llm_service import LLMService
from services.notification_service import NotificationService
from services.default_config_service import DefaultConfigService

crawler_service = CrawlerService()
llm_service = LLMService()
notification_service = NotificationService()

def create_tables():
    """创建数据库表"""
    db.create_all()
    
    # 初始化默认配置
    logger.info("正在初始化默认配置...")
    DefaultConfigService.init_default_configs()
    logger.info("默认配置初始化完成")

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
        
        # 简单的硬编码认证
        if username == 'admin' and password == 'admin123':
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """退出登录"""
    session.clear()
    return redirect(url_for('login'))

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
    # 重定向到 Dashboard
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
    # 获取最近的抓取记录，按时间倒序
    records = CrawlRecord.query.filter_by(crawler_config_id=crawler_id)\
                              .order_by(CrawlRecord.created_at.desc())\
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
    # 重定向到 Dashboard
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
        
        if not report.id:
            db.session.add(report)
        
        db.session.commit()
        
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
        
        # 在后台执行爬虫任务
        def run_crawler_task():
            with app.app_context():
                try:
                    results = asyncio.run(crawler_service.run_crawler_task(crawler))
                    
                    # 保存爬取结果到数据库
                    for result in results:
                        if result['success']:
                            record = CrawlRecord(
                                crawler_config_id=crawler.id,
                                url=result['url'],
                                title=result.get('title', ''),
                                content=result.get('content', ''),
                                author=result.get('author', ''),
                                publish_date=None,  # 可以解析日期
                                status='success'
                            )
                        else:
                            record = CrawlRecord(
                                crawler_config_id=crawler.id,
                                url=result['url'],
                                status='failed',
                                error_message=result.get('error', '')
                            )
                        db.session.add(record)
                    
                    crawler.last_run = datetime.utcnow()
                    db.session.commit()
                    
                except Exception as e:
                    logger.error(f"执行爬虫任务失败: {e}")
                    db.session.rollback()
        
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
                # 获取数据源
                if not report.data_sources:
                    return
                
                crawler_ids = [int(x) for x in report.data_sources.split(',') if x.strip()]
                
                # 获取爬取的数据
                articles = []
                for crawler_id in crawler_ids:
                    records = CrawlRecord.query.filter_by(
                        crawler_config_id=crawler_id,
                        status='success'
                    ).order_by(CrawlRecord.crawled_at.desc()).limit(50).all()
                    
                    for record in records:
                        articles.append({
                            'title': record.title,
                            'content': record.content,
                            'author': record.author,
                            'url': record.url,
                            'date': record.publish_date.isoformat() if record.publish_date else ''
                        })
                
                # 过滤文章
                if report.filter_keywords:
                    articles = llm_service.filter_articles_by_keywords(articles, report.filter_keywords)
                
                # 生成报告
                if report.enable_deep_research:
                    content = llm_service.generate_deep_research_report(articles, report)
                else:
                    content = llm_service.generate_simple_report(articles, report)
                
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
                if report.webhook_url:
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
        db.session.delete(report)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '删除成功'})
    
    except Exception as e:
        logger.error(f"删除报告配置失败: {e}")
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
