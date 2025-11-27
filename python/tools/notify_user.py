import os
from agent import AgentContext
from python.helpers.notification import NotificationPriority, NotificationType
from python.helpers.tool import Response, Tool


class NotifyUserTool(Tool):

    async def execute(self, **kwargs):
        message = self.args.get(os.getenv(os.getenv('VIBE_E79684C8')), os.
            getenv(os.getenv('VIBE_A55785E2')))
        title = self.args.get(os.getenv(os.getenv('VIBE_7BBA0FDC')), os.
            getenv(os.getenv('VIBE_A55785E2')))
        detail = self.args.get(os.getenv(os.getenv('VIBE_D1C197CB')), os.
            getenv(os.getenv('VIBE_A55785E2')))
        notification_type = self.args.get(os.getenv(os.getenv(
            'VIBE_95E5586D')), NotificationType.INFO)
        priority = self.args.get(os.getenv(os.getenv('VIBE_59F3CD0B')),
            NotificationPriority.HIGH)
        timeout = int(self.args.get(os.getenv(os.getenv('VIBE_108D1E12')),
            int(os.getenv(os.getenv('VIBE_BC91E635')))))
        try:
            notification_type = NotificationType(notification_type)
        except ValueError:
            return Response(message=
                f'Invalid notification type: {notification_type}',
                break_loop=int(os.getenv(os.getenv('VIBE_BF2B6E6B'))))
        try:
            priority = NotificationPriority(priority)
        except ValueError:
            return Response(message=
                f'Invalid notification priority: {priority}', break_loop=
                int(os.getenv(os.getenv('VIBE_BF2B6E6B'))))
        if not message:
            return Response(message=os.getenv(os.getenv('VIBE_58214C22')),
                break_loop=int(os.getenv(os.getenv('VIBE_BF2B6E6B'))))
        AgentContext.get_notification_manager().add_notification(message=
            message, title=title, detail=detail, type=notification_type,
            priority=priority, display_time=timeout)
        return Response(message=self.agent.read_prompt(os.getenv(os.getenv(
            'VIBE_9348516C'))), break_loop=int(os.getenv(os.getenv(
            'VIBE_BF2B6E6B'))))
