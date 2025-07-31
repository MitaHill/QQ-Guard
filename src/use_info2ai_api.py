import requests
import subprocess
import sys
import os
import time
import threading
import urllib.parse


class AI_API:
    def __init__(self):
        self.ai_api_url = "http://127.0.0.1:7000/info2ai/api/"
        self.ai_process = None
        self.is_ready = False

    def start_service(self):
        """启动AI服务并等待就绪"""
        ai_script = os.path.join("info2ai", "app.py")
        print(f"检查AI服务脚本: {ai_script}")

        if not os.path.exists(ai_script):
            print(f"❌ 未找到AI服务脚本: {ai_script}")
            return

        try:
            print("启动AI服务...")
            ai_dir = os.path.join(os.getcwd(), "info2ai")
            ai_file = os.path.join(ai_dir, "app.py")

            print(f"AI工作目录: {ai_dir}")
            print(f"AI脚本路径: {ai_file}")

            self.ai_process = subprocess.Popen(
                [sys.executable, ai_file],
                cwd=ai_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='ignore'
            )
            print(f"AI进程PID: {self.ai_process.pid}")

            # 启动输出监控线程
            def output_monitor():
                try:
                    if self.ai_process.stdout:
                        for line in iter(self.ai_process.stdout.readline, ''):
                            if line:
                                print(f"[AI服务] {line.rstrip()}")
                                # 检测Flask启动完成标志
                                if "Running on http://127.0.0.1:7000" in line:
                                    self.is_ready = True
                                    print("✅ AI服务就绪，继续启动主程序")
                except Exception as e:
                    print(f"[AI服务] 输出监控异常: {e}")

            output_thread = threading.Thread(target=output_monitor, daemon=True)
            output_thread.start()

            # 等待服务启动完成
            print("等待AI服务就绪...")
            for i in range(600):  # 最多等待
                if self.ai_process.poll() is not None:
                    print(f"❌ AI进程意外退出，退出码: {self.ai_process.returncode}")
                    return

                if self.is_ready:
                    # 额外等待1秒确保服务完全就绪
                    time.sleep(1)
                    return

                if i % 30 == 0:
                    print(f"⏳ 等待AI服务启动... ({i}/120秒)")
                time.sleep(1)

            print("❌ AI服务启动超时")

        except Exception as e:
            print(f"❌ 启动AI服务失败: {e}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")

    def judge_message(self, user_id, message):
        """使用AI判断消息是否违规"""
        if not self.is_ready:
            print("⚠️ AI服务未就绪，跳过检测")
            return False

        print(f"🤖 开始AI检测 - 用户:{user_id}")
        print(f"📝 原始消息: {message}")

        try:
            formatted_message = f"QQ号{user_id}发送了：{message}"
            encoded_message = urllib.parse.quote(formatted_message, safe='')
            api_url = f"{self.ai_api_url}{encoded_message}"

            print(f"🌐 API地址: {api_url}")
            print("⏳ 发送AI检测请求...")

            start_time = time.time()
            response = requests.get(api_url, timeout=300)
            response_time = time.time() - start_time

            print(f"⏱️ AI响应时间: {response_time:.3f}秒")
            print(f"📊 HTTP状态码: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"📋 AI返回结果: {result}")
                print(f"📋 结果类型: {type(result)}")

                is_violation = result is True
                print(f"✅ 最终判断: {'违规' if is_violation else '正常'}")
                return is_violation
            else:
                print(f"❌ AI API HTTP错误: {response.status_code}")
                print(f"📄 响应内容: {response.text}")
                return False

        except requests.exceptions.Timeout:
            print("⏰ AI API请求超时 (300秒)")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"🔌 AI API连接失败: {e}")
            return False
        except Exception as e:
            print(f"💥 AI API请求异常: {e}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            return False

    def stop_service(self):
        """停止AI服务"""
        if self.ai_process:
            print("🛑 停止AI服务...")
            self.ai_process.terminate()

            # 等待进程结束
            try:
                self.ai_process.wait(timeout=10)
                print("✅ AI进程正常终止")
            except subprocess.TimeoutExpired:
                print("⚠️ AI进程终止超时，强制杀死")
                self.ai_process.kill()

            self.ai_process = None
            self.is_ready = False
            print("✅ AI服务已停止")
        else:
            print("ℹ️ AI服务未运行")