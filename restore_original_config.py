#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恢复原始配置
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import ReportConfig

def restore_original_config():
    """恢复原始配置"""
    try:
        with open('original_config_backup.json', 'r', encoding='utf-8') as f:
            original_config = json.load(f)
        
        with app.app_context():
            config = ReportConfig.query.filter_by(enable_deep_research=True).first()
            
            if config:
                config.name = original_config['name']
                config.purpose = original_config['purpose']
                config.research_focus = original_config['research_focus']
                config.filter_keywords = original_config['filter_keywords']
                config.time_range = original_config['time_range']
                
                db.session.commit()
                print("✅ 原始配置已恢复")
            else:
                print("❌ 未找到配置")
                
    except Exception as e:
        print(f"❌ 恢复失败: {e}")

if __name__ == "__main__":
    restore_original_config()
