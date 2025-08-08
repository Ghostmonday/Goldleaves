from fastapi import BackgroundTasks
from starlette.requests import Request

def send_verification_email(background_tasks: BackgroundTasks, email: str, token: str, request: Request):
    verification_url = f"{request.base_url}auth/verify-email?token={token}"
    message = f"Click the link to verify your email: {verification_url}"
    background_tasks.add_task(print, f"Sending email to {email}: {message}")
