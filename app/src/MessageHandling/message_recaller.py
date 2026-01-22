class MessageRecaller:
    def __init__(self, qq_api):
        self.qq_api = qq_api

    def delete_message(self, message_id):
        """撤回消息"""
        return self.qq_api.delete_message(message_id)