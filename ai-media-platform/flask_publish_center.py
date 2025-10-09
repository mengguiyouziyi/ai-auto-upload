#!/usr/bin/env python3
"""
AI媒体平台发布中心 - 基于social-auto-upload的Flask实现
端口：5174
"""

import asyncio
import os
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from queue import Queue
from flask import Flask, request, jsonify, Response, render_template, send_from_directory

# 复用social-auto-upload的配置和工具
try:
    from conf import BASE_DIR
    from myUtils.auth import check_cookie
    from myUtils.login import get_tencent_cookie, douyin_cookie_gen, get_ks_cookie, xiaohongshu_cookie_gen
    from myUtils.postVideo import post_video_tencent, post_video_DouYin, post_video_ks, post_video_xhs
    SOCIAL_AUTO_UPLOAD_AVAILABLE = True
    print("✅ social-auto-upload模块导入成功")
except ImportError as exc:
    print(f"⚠️ social-auto-upload模块导入失败: {exc}")
    print("🔄 使用备用配置...")
    # 备用配置
    CURRENT_DIR = Path(__file__).resolve()
    BASE_DIR = CURRENT_DIR.parents[1] / "social-auto-upload"
    SOCIAL_AUTO_UPLOAD_AVAILABLE = False

app = Flask(__name__)

# 添加CORS支持
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# 限制上传文件大小为160MB
app.config['MAX_CONTENT_LENGTH'] = 160 * 1024 * 1024

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 确保必要的目录存在
(BASE_DIR / "videoFile").mkdir(exist_ok=True)
(BASE_DIR / "cookiesFile").mkdir(exist_ok=True)

# 活跃队列字典
active_queues = {}

# 处理 favicon.ico 静态资源
@app.route('/favicon.ico')
def favicon():
    frontend_dist_path = os.path.join(current_dir, 'frontend', 'dist')
    favicon_path = os.path.join(frontend_dist_path, 'vite.svg')
    if os.path.exists(favicon_path):
        return send_from_directory(frontend_dist_path, 'vite.svg')
    else:
        return send_from_directory(os.path.join(current_dir, 'assets'), 'favicon.ico')

# 主页路由 - 使用原始的Vite构建界面
@app.route('/')
def hello_world():
    # 使用原始的Vite构建的完整前端界面
    frontend_dist_path = os.path.join(current_dir, 'frontend', 'dist')
    index_path = os.path.join(frontend_dist_path, 'index.html')

    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    else:
        return "<h1>前端文件未找到，请先构建前端项目</h1><p>运行: cd frontend && npm run build</p>"

@app.route('/upload', methods=['POST'])
def upload_file():
    """上传文件接口"""
    if 'file' not in request.files:
        return jsonify({
            "code": 200,
            "data": None,
            "msg": "No file part in the request"
        }), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "code": 200,
            "data": None,
            "msg": "No selected file"
        }), 400
    try:
        # 保存文件到指定位置
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        filepath = Path(BASE_DIR / "videoFile" / f"{uuid_v1}_{file.filename}")
        file.save(filepath)
        return jsonify({"code":200,"msg": "File uploaded successfully", "data": f"{uuid_v1}_{file.filename}"}), 200
    except Exception as e:
        return jsonify({"code":200,"msg": str(e),"data":None}), 500

@app.route('/getFile', methods=['GET'])
def get_file():
    """获取文件接口"""
    filename = request.args.get('filename')

    if not filename:
        return {"error": "filename is required"}, 400

    # 防止路径穿越攻击
    if '..' in filename or filename.startswith('/'):
        return {"error": "Invalid filename"}, 400

    # 拼接完整路径
    file_path = str(Path(BASE_DIR / "videoFile"))

    # 返回文件
    return send_from_directory(file_path, filename)

@app.route('/uploadSave', methods=['POST'])
def upload_save():
    """上传并保存文件到数据库"""
    if 'file' not in request.files:
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No file part in the request"
        }), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No selected file"
        }), 400

    # 获取表单中的自定义文件名（可选）
    custom_filename = request.form.get('filename', None)
    if custom_filename:
        filename = custom_filename + "." + file.filename.split('.')[-1]
    else:
        filename = file.filename

    try:
        # 生成 UUID v1
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")

        # 构造文件名和路径
        final_filename = f"{uuid_v1}_{filename}"
        filepath = Path(BASE_DIR / "videoFile" / f"{uuid_v1}_{filename}")

        # 保存文件
        file.save(filepath)

        # 保存到数据库
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                                INSERT INTO file_records (filename, filesize, file_path)
            VALUES (?, ?, ?)
                                ''', (filename, round(float(os.path.getsize(filepath)) / (1024 * 1024),2), final_filename))
            conn.commit()
            print("✅ 上传文件已记录")

        return jsonify({
            "code": 200,
            "msg": "File uploaded and saved successfully",
            "data": {
                "filename": filename,
                "filepath": final_filename
            }
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("upload failed!"),
            "data": None
        }), 500

@app.route('/getFiles', methods=['GET'])
def get_all_files():
    """获取所有文件记录"""
    try:
        # 使用 with 自动管理数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row  # 允许通过列名访问结果
            cursor = conn.cursor()

            # 查询所有记录
            cursor.execute("SELECT * FROM file_records")
            rows = cursor.fetchall()

            # 将结果转为字典列表
            data = [dict(row) for row in rows]

        return jsonify({
            "code": 200,
            "msg": "success",
            "data": data
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("get file failed!"),
            "data": None
        }), 500

@app.route("/getValidAccounts", methods=['GET'])
def getValidAccounts():
    """获取有效账号列表"""
    with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT * FROM user_info''')
        rows = cursor.fetchall()
        rows_list = [list(row) for row in rows]
        print("\n📋 当前数据表内容：")
        for row in rows:
            print(row)

        # 简化验证逻辑，暂时跳过Cookie验证
        print("⚠️ 简化版本，跳过Cookie验证")

        for row in rows:
            print(row)
        return jsonify(
                        {
                            "code": 200,
                            "msg": None,
                            "data": rows_list
                        }),200

@app.route('/deleteFile', methods=['GET'])
def delete_file():
    """删除文件记录"""
    file_id = request.args.get('id')

    if not file_id or not file_id.isdigit():
        return jsonify({
            "code": 400,
            "msg": "Invalid or missing file ID",
            "data": None
        }), 400

    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM file_records WHERE id = ?", (file_id,))
            record = cursor.fetchone()

            if not record:
                return jsonify({
                    "code": 404,
                    "msg": "File not found",
                    "data": None
                }), 404

            record = dict(record)

            # 删除数据库记录
            cursor.execute("DELETE FROM file_records WHERE id = ?", (file_id,))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "File deleted successfully",
            "data": {
                "id": record['id'],
                "filename": record['filename']
            }
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("delete failed!"),
            "data": None
        }), 500

@app.route('/deleteAccount', methods=['GET'])
def delete_account():
    """删除账号记录"""
    account_id = int(request.args.get('id'))

    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM user_info WHERE id = ?", (account_id,))
            record = cursor.fetchone()

            if not record:
                return jsonify({
                    "code": 404,
                    "msg": "account not found",
                    "data": None
                }), 404

            record = dict(record)

            # 删除数据库记录
            cursor.execute("DELETE FROM user_info WHERE id = ?", (account_id,))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "account deleted successfully",
            "data": None
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("delete failed!"),
            "data": None
        }), 500

# SSE 登录接口
@app.route('/account', methods=['POST'])
def add_account():
    """添加账号接口 - 用于前端添加新账号"""
    data = request.get_json()

    # 获取平台类型和用户名
    platform_type = data.get('type')  # 1: 小红书, 2: 视频号, 3: 抖音, 4: 快手
    username = data.get('userName', '')

    if not platform_type or not username:
        return jsonify({
            "code": 400,
            "msg": "平台类型和用户名不能为空",
            "data": None
        }), 400

    try:
        # 生成唯一ID用于账号标识
        import uuid
        account_id = str(uuid.uuid4())

        # 插入数据库
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_info (type, filePath, userName, status)
                VALUES (?, ?, ?, ?)
            ''', (platform_type, f"{account_id}.json", username, 0))  # 0表示待登录
            conn.commit()

            # 获取插入的记录ID
            record_id = cursor.lastrowid

        print(f"✅ 添加账号成功: {username} (平台类型: {platform_type}, 账号ID: {account_id})")

        return jsonify({
            "code": 200,
            "msg": "账号添加成功",
            "data": {
                "id": record_id,
                "accountId": account_id,
                "type": platform_type,
                "userName": username,
                "status": 0  # 待登录
            }
        }), 200

    except Exception as e:
        print(f"❌ 添加账号失败: {e}")
        return jsonify({
            "code": 500,
            "msg": f"添加账号失败: {str(e)}",
            "data": None
        }), 500

@app.route('/login')
def login():
    """SSE登录接口"""
    # 1 小红书 2 视频号 3 抖音 4 快手
    type = request.args.get('type')
    # 账号名
    id = request.args.get('id')

    # 模拟一个用于异步通信的队列
    status_queue = Queue()
    active_queues[id] = status_queue

    def on_close():
        print(f"清理队列: {id}")
        del active_queues[id]

    # 启动异步任务线程
    if SOCIAL_AUTO_UPLOAD_AVAILABLE:
        thread = threading.Thread(target=run_async_function, args=(type, id, status_queue), daemon=True)
        thread.start()
    else:
        # 使用我们的备用实现
        thread = threading.Thread(target=run_backup_login, args=(type, id, status_queue), daemon=True)
        thread.start()

    response = Response(sse_stream(status_queue,), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'  # 关键：禁用 Nginx 缓冲
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Connection'] = 'keep-alive'
    return response

@app.route('/postVideo', methods=['POST'])
def postVideo():
    """发布视频接口"""
    # 获取JSON数据
    data = request.get_json()

    # 从JSON数据中提取fileList和accountList
    file_list = data.get('fileList', [])
    account_list = data.get('accountList', [])
    type = data.get('type')
    title = data.get('title')
    tags = data.get('tags')
    category = data.get('category')
    enableTimer = data.get('enableTimer')
    if category == 0:
        category = None

    videos_per_day = data.get('videosPerDay')
    daily_times = data.get('dailyTimes')
    start_days = data.get('startDays')

    # 打印获取到的数据（仅作为示例）
    print("File List:", file_list)
    print("Account List:", account_list)

    if SOCIAL_AUTO_UPLOAD_AVAILABLE:
        match type:
            case 1:
                post_video_xhs(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                                   start_days)
            case 2:
                post_video_tencent(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                                   start_days)
            case 3:
                post_video_DouYin(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                          start_days)
            case 4:
                post_video_ks(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                      start_days)
    else:
        print("⚠️ social-auto-upload模块不可用，无法执行发布")
        # 尝试使用备用实现
        try:
            from backend.routes.douyin_upload import upload_douyin_video
            if type == 3:  # 抖音
                success = asyncio.run(upload_douyin_video(
                    title=title,
                    file_list=file_list,
                    tags=tags or [],
                    account_list=account_list,
                    category=category or 0,
                    enable_timer=bool(enableTimer),
                    videos_per_day=videos_per_day or 1,
                    daily_times=daily_times or ["10:00"],
                    start_days=start_days or 0,
                    auto_login=False
                ))
                if success:
                    print("✅ 使用备用实现发布成功")
                else:
                    print("❌ 使用备用实现发布失败")
        except Exception as e:
            print(f"❌ 备用实现出错: {e}")

    # 返回响应给客户端
    return jsonify(
        {
            "code": 200,
            "msg": None,
            "data": None
        }), 200

@app.route('/updateUserinfo', methods=['POST'])
def updateUserinfo():
    """更新用户信息"""
    # 获取JSON数据
    data = request.get_json()

    # 从JSON数据中提取 type 和 userName
    user_id = data.get('id')
    type = data.get('type')
    userName = data.get('userName')
    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 更新数据库记录
            cursor.execute('''
                           UPDATE user_info
                           SET type     = ?,
                               userName = ?
                           WHERE id = ?;
                           ''', (type, userName, user_id))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "account update successfully",
            "data": None
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("update failed!"),
            "data": None
        }), 500

@app.route('/postVideoBatch', methods=['POST'])
def postVideoBatch():
    """批量发布视频"""
    data_list = request.get_json()

    if not isinstance(data_list, list):
        return jsonify({"error": "Expected a JSON array"}), 400

    for data in data_list:
        # 从JSON数据中提取fileList和accountList
        file_list = data.get('fileList', [])
        account_list = data.get('accountList', [])
        type = data.get('type')
        title = data.get('title')
        tags = data.get('tags')
        category = data.get('category')
        enableTimer = data.get('enableTimer')
        if category == 0:
            category = None

        videos_per_day = data.get('videosPerDay')
        daily_times = data.get('dailyTimes')
        start_days = data.get('startDays')
        # 打印获取到的数据（仅作为示例）
        print("File List:", file_list)
        print("Account List:", account_list)

        if SOCIAL_AUTO_UPLOAD_AVAILABLE:
            match type:
                case 1:
                    return
                case 2:
                    post_video_tencent(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                                       start_days)
                case 3:
                    post_video_DouYin(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                              start_days)
                case 4:
                    post_video_ks(title, file_list, tags, account_list, category, enableTimer, videos_per_day, daily_times,
                          start_days)
        else:
            print("⚠️ social-auto-upload模块不可用，批量发布功能受限")

    # 返回响应给客户端
    return jsonify(
        {
            "code": 200,
            "msg": None,
            "data": None
        }), 200

# 包装函数：在线程中运行异步函数
def run_async_function(type, id, status_queue):
    """在线程中运行异步函数"""
    if not SOCIAL_AUTO_UPLOAD_AVAILABLE:
        status_queue.put("500")  # 错误状态
        return

    match type:
        case '1':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(xiaohongshu_cookie_gen(id, status_queue))
            loop.close()
        case '2':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(get_tencent_cookie(id, status_queue))
            loop.close()
        case '3':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(douyin_cookie_gen(id, status_queue))
            loop.close()
        case '4':
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(get_ks_cookie(id, status_queue))
            loop.close()

# 备用登录函数 - 使用我们的独立模块
def run_backup_login(type, id, status_queue):
    """备用登录函数，使用独立模块"""
    try:
        import asyncio
        from backend.routes.douyin_upload import generate_douyin_cookie

        # 获取Cookie文件路径
        cookie_file = Path(BASE_DIR / "cookiesFile" / f"{id}.json")

        # 确保cookiesFile目录存在
        Path(BASE_DIR / "cookiesFile").mkdir(exist_ok=True)

        status_queue.put("200")  # 开始登录

        if type == '3':  # 抖音
            # 在新的事件循环中运行异步函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success = loop.run_until_complete(generate_douyin_cookie(str(cookie_file)))
                if success:
                    # 更新数据库状态为已登录
                    with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
                        cursor = conn.cursor()
                        cursor.execute("UPDATE user_info SET status = 1 WHERE filePath = ?", (f"{id}.json",))
                        conn.commit()

                    status_queue.put("201")  # 登录成功
                    print(f"✅ 抖音账号 {id} 登录成功")
                else:
                    status_queue.put("500")  # 登录失败
                    print(f"❌ 抖音账号 {id} 登录失败")
            except Exception as e:
                print(f"❌ 抖音登录异常: {e}")
                status_queue.put("500")  # 登录失败
            finally:
                loop.close()
        else:
            # 其他平台暂时不支持
            status_queue.put("500")  # 暂不支持
            print(f"⚠️ 平台 {type} 暂不支持登录")

    except Exception as e:
        print(f"❌ 备用登录异常: {e}")
        status_queue.put("500")  # 错误状态

# SSE 流生成器函数
def sse_stream(status_queue):
    """SSE流生成器函数"""
    while True:
        if not status_queue.empty():
            msg = status_queue.get()
            yield f"data: {msg}\n\n"
        else:
            # 避免 CPU 占满
            time.sleep(0.1)

# 在所有API路由之后添加静态资源路由
@app.route('/assets/<path:filename>')
def frontend_static(filename):
    """前端静态资源路由"""
    frontend_dist_path = os.path.join(current_dir, 'frontend', 'dist')
    assets_path = os.path.join(frontend_dist_path, 'assets')
    return send_from_directory(assets_path, filename)

# 兜底路由：处理前端路由
@app.route('/<path:filename>')
def static_files(filename):
    """处理前端静态文件和SPA路由"""
    frontend_dist_path = os.path.join(current_dir, 'frontend', 'dist')
    file_path = os.path.join(frontend_dist_path, filename)

    # 如果文件存在，直接返回
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(frontend_dist_path, filename)

    # 否则返回index.html（用于SPA路由）
    index_path = os.path.join(frontend_dist_path, 'index.html')
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content

    return "File not found", 404

if __name__ == '__main__':
    print(f"🚀 启动AI媒体平台 (完整版本)")
    print(f"📁 基础目录: {BASE_DIR}")
    print(f"🌐 访问地址: http://localhost:5174")
    print(f"📡 API后端: Flask + social-auto-upload功能")
    print(f"🎨 前端界面: Vite构建的完整AI媒体平台")
    print(f"🔧 social-auto-upload模块: {'✅ 可用' if SOCIAL_AUTO_UPLOAD_AVAILABLE else '⚠️ 不可用'}")
    app.run(host='0.0.0.0', port=9001, debug=True)