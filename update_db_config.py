#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新数据库配置为可控生图研究主题
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import ReportConfig

def update_report_config_for_controllable_image_generation():
    """更新报告配置为可控生图研究"""
    print("🔧 更新数据库配置为可控生图研究主题...")
    
    with app.app_context():
        # 查找现有的深度研究配置
        config = ReportConfig.query.filter_by(enable_deep_research=True).first()
        
        if config:
            print(f"✅ 找到现有配置: {config.name}")
            
            # 备份原始配置信息
            original_config = {
                'name': config.name,
                'purpose': config.purpose,
                'research_focus': config.research_focus,
                'filter_keywords': config.filter_keywords,
                'time_range': config.time_range
            }
            
            print(f"📋 原始配置:")
            print(f"   名称: {original_config['name']}")
            print(f"   关键词: {original_config['filter_keywords']}")
            print(f"   目的: {original_config['purpose']}")
            
            # 更新为可控生图研究配置
            config.name = "可控生图技术深度研究"
            config.purpose = "深入研究最近一周可控生图技术的最新进展和突破"
            config.research_focus = "重点关注：1) Nano Banana技术特点和应用场景；2) 即梦4.0的技术创新和性能提升；3) 这些模型的实际测评效果和用户反馈；4) 可控生图技术的发展趋势和市场前景分析"
            config.filter_keywords = "可控生图,Nano Banana,即梦,图像生成,AI绘画,文生图,图像编辑,Stable Diffusion,Midjourney"
            config.time_range = "7d"  # 保持一周的时间范围
            
            try:
                db.session.commit()
                
                print(f"\n✅ 配置更新成功!")
                print(f"📋 新配置:")
                print(f"   名称: {config.name}")
                print(f"   关键词: {config.filter_keywords}")
                print(f"   目的: {config.purpose}")
                print(f"   研究重点: {config.research_focus}")
                print(f"   时间范围: {config.time_range}")
                
                # 保存原始配置到文件，方便后续恢复
                import json
                with open('original_config_backup.json', 'w', encoding='utf-8') as f:
                    json.dump(original_config, f, ensure_ascii=False, indent=2)
                
                print(f"\n💾 原始配置已备份到: original_config_backup.json")
                print(f"🔄 稍后可以使用 restore_original_config.py 恢复原始配置")
                
                return True
                
            except Exception as e:
                print(f"❌ 更新配置失败: {e}")
                return False
                
        else:
            print("❌ 未找到启用深度研究的配置")
            
            # 创建新的可控生图配置
            print("🆕 创建新的可控生图研究配置...")
            
            new_config = ReportConfig(
                name="可控生图技术深度研究",
                data_sources="1,2,3",  # 使用前3个爬虫
                filter_keywords="可控生图,Nano Banana,即梦,图像生成,AI绘画,文生图,图像编辑,Stable Diffusion,Midjourney",
                time_range="7d",
                purpose="深入研究最近一周可控生图技术的最新进展和突破",
                research_focus="重点关注：1) Nano Banana技术特点和应用场景；2) 即梦4.0的技术创新和性能提升；3) 这些模型的实际测评效果和用户反馈；4) 可控生图技术的发展趋势和市场前景分析",
                enable_deep_research=True,
                notification_type="wechat",
                is_active=True
            )
            
            try:
                db.session.add(new_config)
                db.session.commit()
                
                print(f"✅ 新配置创建成功! ID: {new_config.id}")
                return True
                
            except Exception as e:
                print(f"❌ 创建配置失败: {e}")
                return False

def create_restore_script():
    """创建恢复脚本"""
    restore_script = '''#!/usr/bin/env python3
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
'''
    
    with open('restore_original_config.py', 'w', encoding='utf-8') as f:
        f.write(restore_script)
    
    print("📝 创建了恢复脚本: restore_original_config.py")

def main():
    """主函数"""
    print("🚀 数据库配置更新工具")
    print("="*50)
    
    success = update_report_config_for_controllable_image_generation()
    
    if success:
        create_restore_script()
        print(f"\n🎯 现在可以运行测试:")
        print(f"   python3.11 test_v3_deep_research.py")
        print(f"\n🔄 测试完成后恢复原始配置:")
        print(f"   python3.11 restore_original_config.py")
    else:
        print(f"\n❌ 配置更新失败，请检查数据库连接")

if __name__ == "__main__":
    main()
