class MessageSender:
    def __init__(self, qq_api):
        self.qq_api = qq_api

    def send_private_message(self, user_id, message):
        """发送私聊消息"""
        return self.qq_api.send_private_message(user_id, message)

    def send_group_message(self, group_id, message):
        """发送群消息"""
        return self.qq_api.send_group_message(group_id, message)

    def send_image_message(self, target_id, image_path, is_group=False):
        """发送图片消息"""
        message = f"[CQ:image,file=file:///{image_path}]"
        if is_group:
            return self.send_group_message(target_id, message)
        else:
            return self.send_private_message(target_id, message)