# === AGENT CONTEXT: SCHEMAS AGENT ===
# 🚧 TODOs for Phase 4 — Complete schema contracts
# - [x] Define all Pydantic schemas with type-safe fields
# - [x] Add pagination, response, and error wrapper patterns
# - [x] Validate alignment with models/ and services/ usage
# - [x] Enforce exports via `schemas/contract.py`
# - [x] Ensure each schema has at least one integration test
# - [x] Maintain strict folder isolation (no model/service imports)
# - [x] Add version string and export mapping to `SchemaContract`
# - [x] Annotate fields with metadata for future auto-docs

"""
Document comments and collaboration schemas.
Provides schemas for document comments, threads, and collaborative features.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum
from uuid import UUID

from ..dependencies import (
    validate_non_empty_string
)


class CommentType(str, Enum):
    """Type of comment."""
    GENERAL = "general"
    SUGGESTION = "suggestion"
    QUESTION = "question"
    ISSUE = "issue"
    APPROVAL = "approval"
    REVISION_REQUEST = "revision_request"


class CommentStatus(str, Enum):
    """Comment status."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    HIDDEN = "hidden"
    DELETED = "deleted"


class CommentReaction(str, Enum):
    """Comment reactions."""
    LIKE = "like"
    DISLIKE = "dislike"
    AGREE = "agree"
    DISAGREE = "disagree"
    HELPFUL = "helpful"
    CONFUSING = "confusing"


class CommentAnchor(BaseModel):
    """Comment anchor information for positioning."""
    
    type: str = Field(
        title="Anchor Type", description="Type of anchor: 'text', 'page', 'line', 'element'", example="text"
    )
    
    start_position: Optional[int] = Field(
        default=None,
        title="Start Position", description="Start character position for text anchors"
    )
    
    end_position: Optional[int] = Field(
        default=None,
        title="End Position", description="End character position for text anchors"
    )
    
    page_number: Optional[int] = Field(
        default=None,
        title="Page Number", description="Page number for page-based anchors"
    )
    
    element_id: Optional[str] = Field(
        default=None,
        title="Element ID", description="Element identifier for element-based anchors"
    )
    
    coordinates: Optional[Dict[str, float]] = Field(
        default=None,
        title="Coordinates", description="X/Y coordinates for precise positioning"
    )
    
    selected_text: Optional[str] = Field(
        default=None,
        max_length=500,
        title="Selected Text", description="Text that was selected when creating the comment"
    )


class CommentCreate(BaseModel):
    """Schema for creating a new comment."""
    
    content: str = Field(
        min_length=1, max_length=5000,
        title="Content", description="Comment content (supports Markdown)", example="This section needs clarification about the implementation details."
    )
    
    comment_type: CommentType = Field(
        default=CommentType.GENERAL,
        title="Comment Type", description="Type of comment being made"
    )
    
    anchor: Optional[CommentAnchor] = Field(
        default=None,
        title="Anchor", description="Position anchor for the comment"
    )
    
    parent_comment_id: Optional[UUID] = Field(
        default=None,
        title="Parent Comment ID", description="Parent comment ID for threaded replies"
    )
    
    mentions: Optional[List[UUID]] = Field(
        default=None,
        title="Mentions", description="User IDs mentioned in the comment"
    )
    
    attachments: Optional[List[str]] = Field(
        default=None,
        title="Attachments", description="URLs of attached files or images"
    )
    
    private: bool = Field(
        default=False,
        title="Private", description="Whether this is a private comment (only visible to specific users)"
    )
    
    @validator('content')
    def validate_content(cls, v):
        """Validate comment content."""
        return validate_non_empty_string(v)


class CommentUpdate(BaseModel):
    """Schema for updating a comment."""
    
    content: Optional[str] = Field(
        default=None,
        min_length=1, max_length=5000
    )
    
    comment_type: Optional[CommentType] = Field(
        default=None
    )
    
    status: Optional[CommentStatus] = Field(
        default=None
    )
    
    @validator('content')
    def validate_content(cls, v):
        if v is not None:
            return validate_non_empty_string(v)
        return v


class CommentResponse(BaseModel):
    """Schema for comment response."""
    
    id: UUID = Field(
        description="Unique comment identifier"
    )
    
    document_id: UUID = Field(
        description="Document ID"
    )
    
    content: str = Field(
        title="Content", description="Comment content"
    )
    
    content_html: Optional[str] = Field(
        default=None,
        title="Content HTML", description="Rendered HTML content from Markdown"
    )
    
    comment_type: CommentType = Field(
        title="Comment Type", description="Type of comment"
    )
    
    status: CommentStatus = Field(
        title="Status", description="Current comment status"
    )
    
    anchor: Optional[CommentAnchor] = Field(
        title="Anchor", description="Position anchor information"
    )
    
    author_id: UUID = Field(
        description="Comment author user ID"
    )
    
    author_name: str = Field(
        title="Author Name", description="Comment author's display name"
    )
    
    author_avatar: Optional[str] = Field(
        default=None,
        title="Author Avatar", description="Author's avatar URL"
    )
    
    parent_comment_id: Optional[UUID] = Field(
        default=None,
        description="Parent comment ID for threaded replies"
    )
    
    thread_depth: int = Field(
        default=0,
        title="Thread Depth", description="Depth level in the comment thread"
    )
    
    reply_count: int = Field(
        default=0,
        title="Reply Count", description="Number of direct replies to this comment"
    )
    
    mentions: List[Dict[str, str]] = Field(
        default_factory=list,
        title="Mentions", description="Users mentioned in the comment"
    )
    
    reactions: Dict[str, int] = Field(
        default_factory=dict,
        title="Reactions", description="Reaction counts by type"
    )
    
    user_reaction: Optional[CommentReaction] = Field(
        default=None,
        title="User Reaction", description="Current user's reaction to this comment"
    )
    
    attachments: List[Dict[str, str]] = Field(
        default_factory=list,
        title="Attachments", description="Attached files or images"
    )
    
    private: bool = Field(
        title="Private", description="Whether this is a private comment"
    )
    
    created_at: datetime = Field(
        description="When the comment was created"
    )
    
    updated_at: Optional[datetime] = Field(
        default=None,
        description="When the comment was last updated"
    )
    
    resolved_at: Optional[datetime] = Field(
        default=None,
        description="When the comment was resolved"
    )
    
    resolved_by: Optional[UUID] = Field(
        default=None,
        description="User who resolved the comment"
    )


class CommentThread(BaseModel):
    """Schema for a comment thread."""
    
    root_comment: CommentResponse = Field(
        title="Root Comment", description="The top-level comment that started the thread"
    )
    
    replies: List[CommentResponse] = Field(
        default_factory=list,
        title="Replies", description="All replies in the thread"
    )
    
    total_replies: int = Field(
        title="Total Replies", description="Total number of replies in the thread"
    )
    
    participants: List[Dict[str, str]] = Field(
        title="Participants", description="Users who have participated in this thread"
    )
    
    last_activity: datetime = Field(
        description="Last activity in the thread"
    )


class CommentListParams(BaseModel):
    """Parameters for listing comments."""
    
    comment_type: Optional[CommentType] = Field(
        default=None,
        title="Type Filter", description="Filter by comment type"
    )
    
    status: Optional[CommentStatus] = Field(
        default=None,
        title="Status Filter", description="Filter by comment status"
    )
    
    author_id: Optional[UUID] = Field(
        default=None,
        title="Author ID", description="Filter by comment author"
    )
    
    created_after: Optional[datetime] = Field(
        default=None,
        title="Created After", description="Filter comments created after this date"
    )
    
    include_resolved: bool = Field(
        default=True,
        title="Include Resolved", description="Whether to include resolved comments"
    )
    
    include_private: bool = Field(
        default=False,
        title="Include Private", description="Whether to include private comments (if user has access)"
    )
    
    thread_view: bool = Field(
        default=False,
        title="Thread View", description="Whether to return comments grouped by threads"
    )


class CommentReactionRequest(BaseModel):
    """Schema for adding/removing comment reactions."""
    
    reaction: CommentReaction = Field(
        title="Reaction", description="Type of reaction to add"
    )


class CommentModerationRequest(BaseModel):
    """Schema for comment moderation actions."""
    
    action: str = Field(
        title="Action", description="Moderation action: 'hide', 'delete', 'restore', 'flag'", example="hide"
    )
    
    reason: Optional[str] = Field(
        default=None,
        max_length=200,
        title="Reason", description="Reason for the moderation action"
    )
    
    @validator('action')
    def validate_action(cls, v):
        """Validate moderation action."""
        allowed_actions = ['hide', 'delete', 'restore', 'flag']
        if v not in allowed_actions:
            raise ValueError(f"Action must be one of: {', '.join(allowed_actions)}")
        return v


class CommentStats(BaseModel):
    """Comment statistics for a document."""
    
    total_comments: int = Field(
        title="Total Comments", description="Total number of comments"
    )
    
    active_comments: int = Field(
        title="Active Comments", description="Number of active (unresolved) comments"
    )
    
    resolved_comments: int = Field(
        title="Resolved Comments", description="Number of resolved comments"
    )
    
    comments_by_type: Dict[str, int] = Field(
        title="Comments by Type", description="Comment count breakdown by type"
    )
    
    unique_commenters: int = Field(
        title="Unique Commenters", description="Number of unique users who have commented"
    )
    
    avg_resolution_time_hours: Optional[float] = Field(
        default=None,
        title="Average Resolution Time", description="Average time to resolve comments in hours"
    )
    
    last_7_days: Dict[str, int] = Field(
        title="Last 7 Days", description="Comment activity in the last 7 days"
    )


class BulkCommentAction(BaseModel):
    """Schema for bulk comment operations."""
    
    comment_ids: List[UUID] = Field(
        min_items=1,
        max_items=100,
        title="Comment IDs", description="List of comment IDs to operate on (max 100)"
    )
    
    action: str = Field(
        title="Action", description="Action to perform: 'resolve', 'delete', 'hide', 'restore'"
    )
    
    reason: Optional[str] = Field(
        default=None,
        max_length=200,
        title="Reason", description="Reason for the bulk action"
    )
    
    @validator('action')
    def validate_action(cls, v):
        """Validate bulk action."""
        allowed_actions = ['resolve', 'delete', 'hide', 'restore']
        if v not in allowed_actions:
            raise ValueError(f"Action must be one of: {', '.join(allowed_actions)}")
        return v
