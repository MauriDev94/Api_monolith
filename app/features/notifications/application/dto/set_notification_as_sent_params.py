from dataclasses import dataclass


@dataclass(slots=True)
class SetNotificationAsSentParams:
    """Input DTO for marking a notification as sent."""

    notification_id: str
