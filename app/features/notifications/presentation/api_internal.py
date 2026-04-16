from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.features.notifications.application.usecases.process_reminders_use_case import (
    process_reminders,
)


class ProcessRemindersResponse(BaseModel):
    """Response for process reminders endpoint."""

    processed: int
    created: int
    failed: int


# Internal router - no auth required (protected by internal network in production)
internal_router = APIRouter(prefix="/internal", tags=["Internal"])


@internal_router.post(
    "/reminders/process",
    response_model=ProcessRemindersResponse,
    status_code=status.HTTP_200_OK,
)
def trigger_reminder_processing(days_ahead: int = 1):
    """Trigger the reminder job manually (for testing/development).

    In production, this should be protected by network policies.
    """
    try:
        result = process_reminders(days_ahead=days_ahead)
        return ProcessRemindersResponse(**result)
    except Exception as e:
        msg = f"Failed to process reminders: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=msg,
        ) from e
