#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试LLM流式返回功能
"""

import asyncio
import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from services.llm_service import LLMService
from models import GlobalSettings

def test_stream_vs_normal():
    """测试流式返回 vs 普通返回"""
    print("🚀 LLM流式返回功能测试")
    print("="*60)
    
    try:
        with app.app_context():
            # 获取LLM设置
            settings = GlobalSettings.query.first()
            if not settings or not settings.llm_api_key:
                print("❌ LLM配置未找到")
                return False
            
            llm_service = LLMService()
            llm_service.update_settings(settings)
            
            # 准备测试消息
            test_messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的AI技术分析师。请生成详细的技术分析报告。"
                },
                {
                    "role": "user", 
                    "content": """请分析人工智能技术在2025年的发展趋势，包括：
1. 大模型技术的最新进展
2. AI在各行业的应用现状
3. 技术挑战和发展机遇
4. 未来发展预测

请生成一个约1000字的详细分析报告。"""
                }
            ]
            
            print(f"🔧 LLM配置: {settings.llm_provider} ({settings.llm_model_name})")
            print(f"🎯 测试任务: 生成约1000字的AI技术分析报告")
            
            # 测试普通返回
            print(f"\n📝 测试1: 普通返回模式")
            start_time = time.time()
            try:
                normal_result = llm_service._make_request(test_messages, temperature=0.7, stream=False)
                normal_time = time.time() - start_time
                
                print(f"✅ 普通返回完成")
                print(f"   耗时: {normal_time:.2f}秒")
                print(f"   内容长度: {len(normal_result)}字符")
                print(f"   预览: {normal_result[:150]}...")
                
            except Exception as e:
                print(f"❌ 普通返回失败: {e}")
                normal_result = None
                normal_time = 0
            
            # 测试流式返回
            print(f"\n📡 测试2: 流式返回模式")
            start_time = time.time()
            try:
                print("流式输出开始:")
                print("-" * 50)
                stream_result = llm_service._make_request(test_messages, temperature=0.7, stream=True)
                stream_time = time.time() - start_time
                
                print("\n" + "-" * 50)
                print(f"✅ 流式返回完成")
                print(f"   耗时: {stream_time:.2f}秒") 
                print(f"   内容长度: {len(stream_result)}字符")
                
            except Exception as e:
                print(f"❌ 流式返回失败: {e}")
                stream_result = None
                stream_time = 0
            
            # 对比结果
            print(f"\n📊 性能对比:")
            if normal_result and stream_result:
                print(f"   普通模式: {normal_time:.2f}秒 ({len(normal_result)}字符)")
                print(f"   流式模式: {stream_time:.2f}秒 ({len(stream_result)}字符)")
                
                if stream_time > 0 and normal_time > 0:
                    improvement = ((normal_time - stream_time) / normal_time) * 100
                    print(f"   流式模式用户体验提升: {improvement:.1f}%")
                
                # 检查内容质量
                if abs(len(normal_result) - len(stream_result)) / max(len(normal_result), len(stream_result)) < 0.1:
                    print(f"   内容质量: ✅ 两种模式内容长度接近")
                else:
                    print(f"   内容质量: ⚠️ 两种模式内容长度差异较大")
            
            return normal_result is not None and stream_result is not None
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

def test_timeout_resistance():
    """测试流式返回的超时抗性"""
    print(f"\n🕐 流式返回超时抗性测试")
    print("="*50)
    
    try:
        with app.app_context():
            settings = GlobalSettings.query.first()
            if not settings or not settings.llm_api_key:
                print("❌ LLM配置未找到")
                return False
            
            llm_service = LLMService()
            llm_service.update_settings(settings)
            
            # 准备更复杂的任务（可能需要更长时间）
            complex_messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的深度研究分析师。请生成详细、深入的研究报告。"
                },
                {
                    "role": "user",
                    "content": """请生成一份关于"AI技术发展趋势与产业化应用"的深度研究报告，包括：

1. 技术发展历程回顾
2. 当前技术热点分析 
3. 主要厂商竞争格局
4. 行业应用案例研究
5. 技术挑战与解决方案
6. 市场规模与投资趋势
7. 政策法规影响分析
8. 未来5年发展预测
9. 风险评估与机遇分析
10. 战略建议与行动计划

请确保报告内容详实、逻辑清晰、数据支撑充分，目标长度2000-3000字。"""
                }
            ]
            
            print(f"🎯 复杂任务: 生成2000-3000字深度研究报告")
            
            start_time = time.time()
            try:
                print("开始流式生成复杂报告...")
                print("-" * 50)
                
                result = llm_service._make_request(complex_messages, temperature=0.7, stream=True)
                end_time = time.time()
                
                print("\n" + "-" * 50)
                print(f"✅ 复杂任务流式返回成功")
                print(f"   耗时: {end_time - start_time:.2f}秒")
                print(f"   内容长度: {len(result)}字符")
                print(f"   是否达到目标长度: {'✅ 是' if len(result) >= 2000 else '❌ 否'}")
                
                return True
                
            except Exception as e:
                print(f"❌ 复杂任务失败: {e}")
                return False
                
    except Exception as e:
        print(f"❌ 超时抗性测试发生错误: {e}")
        return False

def main():
    """主测试函数"""
    print("🎯 启动LLM流式返回测试...")
    
    results = {}
    
    # 测试基本流式功能
    basic_success = test_stream_vs_normal()
    results["基本流式功能"] = basic_success
    
    # 测试超时抗性
    timeout_success = test_timeout_resistance()
    results["超时抗性"] = timeout_success
    
    # 总结
    print("\n" + "="*60)
    print("📋 LLM流式返回测试总结")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed_tests}/{total_tests} 项测试通过")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！LLM流式返回功能正常")
        print("💡 优势:")
        print("   ✅ 解决超时问题 - 流式返回可以处理长时间生成任务")
        print("   ✅ 提升用户体验 - 实时显示生成进度")
        print("   ✅ 更好的稳定性 - 减少网络超时风险")
        return True
    else:
        print("⚠️ 部分测试失败，请检查流式返回实现")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
