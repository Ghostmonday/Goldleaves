# core/email_utils.py

import asyncio
import logging
import smtplib
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from agent import create_email_verification_token

# Configure logging
logger = logging.getLogger(__name__)

# Email configuration (would typically come from settings)
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USERNAME = "your-app@example.com"
EMAIL_PASSWORD = "your-app-password"
EMAIL_FROM_NAME = "Goldleaves App"

async def send_verification_email(user_id: str, email: str, expires_delta: timedelta = None) -> bool:
    """
    Send email verification to user.
    
    Args:
        user_id (str): ID of the user to send verification to
        email (str): Email address to send verification to
        expires_delta (timedelta, optional): Token expiration time. Defaults to 24 hours.
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Create email verification token
        token = await create_email_verification_token(
            user_id=user_id,
            email=email,
            expires_delta=expires_delta
        )
        
        # Create verification URL (would use actual domain in production)
        verification_url = f"https://your-app.com/verify-email?token={token}"
        
        # Create email content
        subject = "Verify Your Email Address - Goldleaves"
        
        # HTML email template
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Email Verification</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #4CAF50; 
                          color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Goldleaves!</h1>
                </div>
                <div class="content">
                    <h2>Please verify your email address</h2>
                    <p>Thank you for signing up for Goldleaves. To complete your registration and activate your account, please verify your email address by clicking the button below:</p>
                    
                    <div style="text-align: center;">
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </div>
                    
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #666;">{verification_url}</p>
                    
                    <p><strong>Important:</strong> This verification link will expire in 24 hours for security reasons.</p>
                    
                    <p>If you didn't create an account with us, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2025 Goldleaves. All rights reserved.</p>
                    <p>This email was sent to {email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_body = f"""
        Welcome to Goldleaves!
        
        Please verify your email address by visiting this link:
        {verification_url}
        
        This verification link will expire in 24 hours for security reasons.
        
        If you didn't create an account with us, please ignore this email.
        
        © 2025 Goldleaves. All rights reserved.
        """
        
        # Send email
        success = await _send_email(
            to_email=email,
            subject=subject,
            text_body=text_body,
            html_body=html_body
        )
        
        if success:
            logger.info(f"Verification email sent successfully to {email} for user {user_id}")
        else:
            logger.error(f"Failed to send verification email to {email} for user {user_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error sending verification email to {email} for user {user_id}: {str(e)}")
        return False

async def send_password_reset_email(email: str, reset_token: str) -> bool:
    """
    Send password reset email to user.
    
    Args:
        email (str): Email address to send reset email to
        reset_token (str): Password reset token
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Create reset URL
        reset_url = f"https://your-app.com/reset-password?token={reset_token}"
        
        subject = "Reset Your Password - Goldleaves"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Password Reset</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f44336; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #f44336; 
                          color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <h2>Reset your password</h2>
                    <p>We received a request to reset your password for your Goldleaves account. Click the button below to create a new password:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </div>
                    
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #666;">{reset_url}</p>
                    
                    <p><strong>Important:</strong> This reset link will expire in 1 hour for security reasons.</p>
                    
                    <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
                </div>
                <div class="footer">
                    <p>© 2025 Goldleaves. All rights reserved.</p>
                    <p>This email was sent to {email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Password Reset Request - Goldleaves
        
        We received a request to reset your password. Click this link to reset your password:
        {reset_url}
        
        This reset link will expire in 1 hour for security reasons.
        
        If you didn't request a password reset, please ignore this email.
        
        © 2025 Goldleaves. All rights reserved.
        """
        
        success = await _send_email(
            to_email=email,
            subject=subject,
            text_body=text_body,
            html_body=html_body
        )
        
        if success:
            logger.info(f"Password reset email sent successfully to {email}")
        else:
            logger.error(f"Failed to send password reset email to {email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error sending password reset email to {email}: {str(e)}")
        return False

async def _send_email(to_email: str, subject: str, text_body: str, html_body: str = None) -> bool:
    """
    Send email using SMTP.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        text_body (str): Plain text email body
        html_body (str, optional): HTML email body
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{EMAIL_FROM_NAME} <{EMAIL_USERNAME}>"
        msg['To'] = to_email
        
        # Add text and HTML parts
        text_part = MIMEText(text_body, 'plain')
        msg.attach(text_part)
        
        if html_body:
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
        
        # Send email in a thread to avoid blocking
        def send_smtp_email():
            try:
                server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
                server.starttls()
                server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
                server.send_message(msg)
                server.quit()
                return True
            except Exception as e:
                logger.error(f"SMTP error sending email to {to_email}: {str(e)}")
                return False
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(None, send_smtp_email)
        
        return success
        
    except Exception as e:
        logger.error(f"Error preparing email for {to_email}: {str(e)}")
        return False

async def send_welcome_email(email: str, username: str = None) -> bool:
    """
    Send welcome email to newly registered user.
    
    Args:
        email (str): User's email address
        username (str, optional): User's username
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        display_name = username or email.split('@')[0]
        subject = f"Welcome to Goldleaves, {display_name}!"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to Goldleaves</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Goldleaves!</h1>
                </div>
                <div class="content">
                    <h2>Hello {display_name},</h2>
                    <p>Welcome to Goldleaves! We're excited to have you join our community.</p>
                    
                    <p>Your account has been successfully created and your email has been verified. You can now enjoy all the features our platform has to offer.</p>
                    
                    <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
                    
                    <p>Thank you for choosing Goldleaves!</p>
                </div>
                <div class="footer">
                    <p>© 2025 Goldleaves. All rights reserved.</p>
                    <p>This email was sent to {email}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Welcome to Goldleaves!
        
        Hello {display_name},
        
        Welcome to Goldleaves! We're excited to have you join our community.
        
        Your account has been successfully created and your email has been verified. 
        You can now enjoy all the features our platform has to offer.
        
        If you have any questions or need assistance, please don't hesitate to contact our support team.
        
        Thank you for choosing Goldleaves!
        
        © 2025 Goldleaves. All rights reserved.
        """
        
        success = await _send_email(
            to_email=email,
            subject=subject,
            text_body=text_body,
            html_body=html_body
        )
        
        if success:
            logger.info(f"Welcome email sent successfully to {email}")
        else:
            logger.error(f"Failed to send welcome email to {email}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error sending welcome email to {email}: {str(e)}")
        return False
