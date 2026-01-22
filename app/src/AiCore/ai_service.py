from src.AiCore.ai_factory import create_ai_client


class AiService:
    def __init__(self):
        self.is_ready = False
        self.client = None

    def start_service(self):
        """初始化AI服务"""
        print("初始化AI服务...")
        try:
            self.client = create_ai_client()
            print("加载知识库和提示词...")
            self.client.load_knowledge_base()
            self.client.load_history()

            print("预热模型...")
            response = self.client.chat("ready")
            if response:
                self.is_ready = True
                print("✅ AI服务初始化成功")
            else:
                print("❌ AI服务初始化失败")
        except Exception as e:
            print(f"❌ 初始化AI服务失败: {e}")
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
            print(f"🔍 格式化消息: {formatted_message}")
            print("⏳ 开始AI检测...")

            import time
            start_time = time.time()
            result = self.client.judge(formatted_message) if self.client else False
            response_time = time.time() - start_time

            print(f"⏱️ AI响应时间: {response_time:.3f}秒")
            print(f"📋 AI返回结果: {result}")
            print(f"📋 结果类型: {type(result)}")

            is_violation = result is True
            print(f"✅ 最终判断: {'违规' if is_violation else '正常'}")
            return is_violation

        except Exception as e:
            print(f"💥 AI检测异常: {e}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            return False

    def stop_service(self):
        """停止AI服务"""
        if self.is_ready:
            print("🛑 停止AI服务...")
            self.is_ready = False
            self.client = None
            print("✅ AI服务已停止")
        else:
            print("ℹ️ AI服务未运行")


if __name__ == "__main__":
    print("初始化AI系统...")
    service = AiService()
    service.start_service()
