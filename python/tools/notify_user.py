import os

from agent import AgentContext
from python.helpers.notification import NotificationPriority, NotificationType
from python.helpers.tool import Response, Tool


class NotifyUserTool(Tool):

    async def execute(self, **kwargs):
        message = self.args.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        title = self.args.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        detail = self.args.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        notification_type = self.args.get(os.getenv(os.getenv("")), NotificationType.INFO)
        priority = self.args.get(os.getenv(os.getenv("")), NotificationPriority.HIGH)
        timeout = int(self.args.get(os.getenv(os.getenv("")), int(os.getenv(os.getenv("")))))
        try:
            notification_type = NotificationType(notification_type)
        except ValueError:
            return Response(
                message=f"Invalid notification type: {notification_type}",
                break_loop=int(os.getenv(os.getenv(""))),
            )
        try:
            priority = NotificationPriority(priority)
        except ValueError:
            return Response(
                message=f"Invalid notification priority: {priority}",
                break_loop=int(os.getenv(os.getenv(""))),
            )
        if not message:
            return Response(
                message=os.getenv(os.getenv("")), break_loop=int(os.getenv(os.getenv("")))
            )
        AgentContext.get_notification_manager().add_notification(
            message=message,
            title=title,
            detail=detail,
            type=notification_type,
            priority=priority,
            display_time=timeout,
        )
        return Response(
            message=self.agent.read_prompt(os.getenv(os.getenv(""))),
            break_loop=int(os.getenv(os.getenv(""))),
        )
