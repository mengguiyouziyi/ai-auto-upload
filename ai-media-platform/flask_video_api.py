#!/usr/bin/env python3
"""
Flask REST API for ComfyUI Wan 2.2 Video Generation
基于您提供的Flask REST API + 客户端SDK方案
"""

import asyncio
import json
import time
import uuid
import threading
from typing import Dict, List, Optional
from pathlib import Path

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("⚠️ httpx库未安装，请运行: pip install httpx")

try:
    from flask import Flask, request, jsonify, send_file
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("⚠️ Flask库未安装，请运行: pip install flask flask-cors")

try:
    import requests
    import io
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️ requests库未安装，请运行: pip install requests")

class WanVideoGenerator:
    """ComfyUI Wan 2.2 视频生成器"""

    def __init__(self, comfyui_url="http://192.168.1.246:8188"):
        self.comfyui_url = comfyui_url
        self.task_queue = {}  # 任务队列
        self.task_status = {}  # 任务状态

    def get_standard_workflow(self) -> Dict:
        """获取标准工作流配置"""
        return {
            "workflow": {
                "1": {
                    "inputs": {
                        "ckpt_name": "wan2_1_14B_fp16.safetensors",
                        "lora_name": "wan2_1_14B_fp16_lora.safetensors",
                        "use_lora": True,
                        "prompt": "美丽风景，高清画质",
                        "negative_prompt": "模糊,低质量,失真",
                        "width": 640,
                        "height": 640,
                        "steps": 4,
                        "cfg": 2.5,
                        "seed": -1
                    },
                    "class_type": "WanVideoLoader"
                },
                "2": {
                    "inputs": {
                        "samples": ["1", 0],
                        "vae_name": "wan2_1_vae_fp16.safetensors"
                    },
                    "class_type": "WanVideoVAE"
                },
                "3": {
                    "inputs": {
                        "filename_prefix": "api_video",
                        "images": ["2", 0],
                        "fps": 8.0,
                        "lossless": False,
                        "quality": 85
                    },
                    "class_type": "SaveAnimatedWEBP"
                }
            }
        }

    def create_workflow(self, prompt: str, width: int = 640, height: int = 640,
                       steps: int = 4, cfg: float = 2.5, use_lora: bool = True,
                       seed: int = -1) -> Dict:
        """创建工作流配置"""
        workflow = self.get_standard_workflow()

        # 修改参数
        if "1" in workflow["workflow"]:
            inputs = workflow["workflow"]["1"]["inputs"]
            inputs["prompt"] = prompt
            inputs["width"] = width
            inputs["height"] = height
            inputs["steps"] = steps
            inputs["cfg"] = cfg
            inputs["seed"] = seed
            inputs["use_lora"] = use_lora

        return workflow

    async def generate_video(self, prompt: str, **kwargs) -> Dict:
        """异步生成视频"""
        if not HTTPX_AVAILABLE:
            raise Exception("httpx库未安装，无法进行HTTP请求")

        task_id = str(uuid.uuid4())

        try:
            # 创建工作流
            workflow = self.create_workflow(prompt, **kwargs)

            # 提交任务到ComfyUI
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.comfyui_url}/prompt",
                    json={"prompt": workflow}
                )
                response.raise_for_status()
                prompt_id = response.json().get("prompt_id")

            if not prompt_id:
                raise Exception("提交ComfyUI任务失败")

            # 监控任务
            result = await self.monitor_task(prompt_id)
            result["task_id"] = task_id
            result["parameters"] = {
                "prompt": prompt,
                **kwargs
            }

            return result

        except Exception as e:
            return {
                "task_id": task_id,
                "success": False,
                "error": str(e)
            }

    async def monitor_task(self, prompt_id: str, max_wait_time: int = 300) -> Dict:
        """监控ComfyUI任务"""
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{self.comfyui_url}/history/{prompt_id}")
                    response.raise_for_status()

                    history = response.json()
                    if prompt_id in history:
                        task_data = history[prompt_id]
                        status_info = task_data.get("status", {})

                        if status_info.get("status_str") == "success":
                            outputs = task_data.get("outputs", {})
                            files = []

                            for node_id, node_output in outputs.items():
                                if "images" in node_output:
                                    for img in node_output["images"]:
                                        files.append({
                                            "filename": img.get("filename"),
                                            "url": f"{self.comfyui_url}/view?filename={img.get('filename')}"
                                        })
                                elif "videos" in node_output:
                                    for vid in node_output["videos"]:
                                        files.append({
                                            "filename": vid.get("filename"),
                                            "url": f"{self.comfyui_url}/view?filename={vid.get('filename')}"
                                        })

                            generation_time = time.time() - start_time

                            return {
                                "success": True,
                                "generation_time": generation_time,
                                "output_files": files
                            }

                        elif status_info.get("status_str") == "error":
                            error_msg = task_data.get("error", "未知错误")
                            return {
                                "success": False,
                                "error": error_msg
                            }

                await asyncio.sleep(2)

            except Exception as e:
                print(f"监控任务异常: {e}")
                await asyncio.sleep(2)

        return {
            "success": False,
            "error": "任务超时"
        }

# 创建Flask应用
if FLASK_AVAILABLE:
    app = Flask(__name__)
    CORS(app)  # 启用CORS

    # 初始化生成器
    generator = WanVideoGenerator()

    @app.route('/health')
    def health():
        """健康检查"""
        return jsonify({
            "status": "healthy",
            "timestamp": time.time(),
            "services": {
                "video": "active",
                "api": "active"
            }
        })

    @app.route('/models')
    def get_models():
        """获取可用模型"""
        return jsonify({
            "models": [
                {
                    "name": "wan2_1_14B_fp16.safetensors",
                    "description": "Wan 2.1 14B 主模型",
                    "type": "main"
                },
                {
                    "name": "wan2_1_14B_fp16_lora.safetensors",
                    "description": "Wan 2.1 14B LoRA加速器",
                    "type": "lora"
                }
            ]
        })

    @app.route('/generate', methods=['POST'])
    def generate_video():
        """生成视频接口"""
        try:
            data = request.get_json()
            if not data or 'prompt' not in data:
                return jsonify({
                    "success": False,
                    "error": "缺少prompt参数"
                }), 400

            prompt = data['prompt']
            width = data.get('width', 640)
            height = data.get('height', 640)
            steps = data.get('steps', 4)
            cfg = data.get('cfg', 2.5)
            use_lora = data.get('use_lora', True)
            seed = data.get('seed', -1)

            print(f"🎬 开始生成视频: {prompt}")
            print(f"   尺寸: {width}x{height}")
            print(f"   步数: {steps}")
            print(f"   LoRA: {use_lora}")

            # 异步生成视频
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(
                generator.generate_video(
                    prompt=prompt,
                    width=width,
                    height=height,
                    steps=steps,
                    cfg=cfg,
                    use_lora=use_lora,
                    seed=seed
                )
            )

            return jsonify(result)

        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.route('/download/<filename>')
    def download_file(filename):
        """下载文件"""
        try:
            url = f"{generator.comfyui_url}/view?filename={filename}"

            # 获取文件
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                return send_file(
                    io.BytesIO(response.content),
                    as_attachment=True,
                    download_name=filename,
                    mimetype=response.headers.get('content-type', 'application/octet-stream')
                )
            else:
                return jsonify({"error": "文件不存在"}), 404

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/status/<task_id>')
    def get_task_status(task_id):
        """获取任务状态"""
        # 这里可以实现任务状态查询逻辑
        return jsonify({
            "task_id": task_id,
            "status": "completed",
            "progress": 100
        })

    @app.route('/')
    def api_docs():
        """API文档"""
        return jsonify({
            "name": "ComfyUI Wan 2.2 Video Generation API",
            "version": "1.0.0",
            "endpoints": {
                "/health": "GET - 健康检查",
                "/models": "GET - 获取可用模型",
                "/generate": "POST - 生成视频",
                "/download/<filename>": "GET - 下载文件",
                "/status/<task_id>": "GET - 查询任务状态"
            },
            "example": {
                "generate": {
                    "method": "POST",
                    "url": "/generate",
                    "data": {
                        "prompt": "美丽的日落海景",
                        "width": 640,
                        "height": 640,
                        "steps": 4,
                        "cfg": 2.5,
                        "use_lora": True
                    }
                }
            }
        })

    def run_server(host='0.0.0.0', port=5000, debug=False):
        """启动Flask服务器"""
        print(f"🚀 启动Flask视频生成API服务器")
        print(f"   地址: http://{host}:{port}")
        print(f"   文档: http://{host}:{port}/")
        print(f"   ComfyUI: {generator.comfyui_url}")
        print("="*50)
        app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    if not FLASK_AVAILABLE:
        print("❌ 请先安装Flask: pip install flask flask-cors httpx")
        exit(1)

    if not HTTPX_AVAILABLE:
        print("❌ 请先安装httpx: pip install httpx")
        exit(1)

    run_server()