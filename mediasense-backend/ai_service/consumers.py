import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """通知WebSocket消费者"""

    async def connect(self):
        """建立连接"""
        if self.scope["user"].is_anonymous:
            await self.close()
            return

        self.user_id = self.scope["user"].id
        self.group_name = f"user_{self.user_id}_notifications"

        # 将用户加入通知组
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

        # 发送未读通知数量
        unread_count = await self.get_unread_count()
        await self.send(json.dumps({"type": "unread_count", "count": unread_count}))

    async def disconnect(self, close_code):
        """断开连接"""
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """接收消息"""
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "mark_as_read":
                notification_id = data.get("notification_id")
                if notification_id:
                    await self.mark_as_read(notification_id)

            elif action == "mark_all_as_read":
                await self.mark_all_as_read()

            # 发送最新的未读数量
            unread_count = await self.get_unread_count()
            await self.send(json.dumps({"type": "unread_count", "count": unread_count}))

        except json.JSONDecodeError:
            pass

    async def notification_message(self, event):
        """处理通知消息"""
        await self.send(json.dumps({"type": "notification", "data": event["message"]}))

    @database_sync_to_async
    def get_unread_count(self):
        """获取未读通知数量"""
        from .services import NotificationService

        return NotificationService.get_unread_count(self.scope["user"])

    @database_sync_to_async
    def mark_as_read(self, notification_id):
        """标记通知为已读"""
        from .services import NotificationService

        return NotificationService.mark_as_read(notification_id, self.scope["user"])

    @database_sync_to_async
    def mark_all_as_read(self):
        """标记所有通知为已读"""
        from .services import NotificationService

        NotificationService.mark_all_as_read(self.scope["user"])
