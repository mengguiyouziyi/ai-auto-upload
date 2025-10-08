#!/usr/bin/env python3
"""
上传优化工作流到ComfyUI服务器
"""

import requests
import json
import os
from pathlib import Path

def upload_workflow_to_comfyui():
    """上传优化工作流到ComfyUI服务器"""
    comfyui_url = "http://192.168.1.246:8188"
    workflow_path = "optimized_video_workflow.json"

    if not os.path.exists(workflow_path):
        print(f"❌ 工作流文件不存在: {workflow_path}")
        return False

    print(f"🚀 开始上传工作流文件: {workflow_path}")
    print(f"📡 目标服务器: {comfyui_url}")

    try:
        # 读取工作流文件
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)

        print(f"📖 工作流文件读取成功，节点数量: {len(workflow_data)}")

        # 使用ComfyUI的API保存工作流
        save_url = f"{comfyui_url}/workflow"

        response = requests.post(
            save_url,
            json=workflow_data,
            headers={'Content-Type': 'application/json'},
            timeout=30.0
        )

        if response.status_code == 200:
            print(f"✅ 工作流上传成功！")
            print(f"📂 请在ComfyUI界面中保存为 'optimized_video_workflow.json'")
            return True
        else:
            print(f"❌ 工作流上传失败: {response.status_code}")
            print(f"📄 响应内容: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 上传过程出错: {str(e)}")
        return False

def verify_workflow_exists():
    """验证工作流是否存在于ComfyUI服务器"""
    comfyui_url = "http://192.168.1.246:8188"
    workflow_filename = "user/default/workflows/optimized_video_workflow.json"

    print(f"🔍 验证工作流是否存在: {workflow_filename}")

    try:
        response = requests.get(f"{comfyui_url}/view", params={
            "filename": workflow_filename
        }, timeout=10.0)

        if response.status_code == 200:
            workflow_data = response.json()
            print(f"✅ 工作流存在且可访问，节点数量: {len(workflow_data)}")
            return True
        else:
            print(f"❌ 工作流不存在或无法访问: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 验证过程出错: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎯 ComfyUI工作流上传工具")
    print("=" * 50)

    # 首先检查工作流是否已存在
    if verify_workflow_exists():
        print("🎉 优化工作流已存在于服务器上，无需重复上传")
    else:
        print("📤 工作流不存在，开始上传...")
        success = upload_workflow_to_comfyui()
        if success:
            print("🎉 工作流上传成功！")
        else:
            print("⚠️ 工作流上传失败，请检查网络连接和ComfyUI服务状态")

    print("\n📋 后续步骤:")
    print("1. 重启AI媒体平台后端服务")
    print("2. 测试视频生成功能")
    print("3. 检查是否使用了优化工作流")