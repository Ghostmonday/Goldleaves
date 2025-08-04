# PHASE12_CONTEXT_README.md

# Phase 12 Context Files - Form Crowdsourcing Implementation

## Overview
This folder contains the 20 most important files for implementing Phase 12 - Form Crowdsourcing feature for the Goldleaves legal platform. These files provide the essential context, architecture, and foundation needed to build the crowdsourcing system.

## Phase 12 Requirements Summary
✅ **Dual Submission Strategy**: Paralegal + Crowdsourcing contributors
✅ **10 Unique Pages = 1 Week Free Logic**: Reward system for contributors  
✅ **Form Locking Upon Acceptance**: Forms locked once approved
✅ **Field-Level AI Validation Hooks**: Stubbed for Phase 14 integration
✅ **Metadata Handling**: County, language, jurisdiction support
✅ **Versioning System**: Form version tracking
✅ **Reward Ledger**: Contributor tracking and rewards
✅ **Ingestion Stats + Deduplication**: Analytics and duplicate detection
✅ **Reviewer Flow**: Admin review, approve/reject process
✅ **File Storage Layer**: PDF, DOCX support
✅ **User Feedback System**: Structured feedback collection

## File Descriptions

### Core Infrastructure (Files 1-5)
1. **01_core_config.py** - Application configuration and settings
2. **02_core_dependencies.py** - Authentication and dependency injection
3. **03_models_user.py** - User and organization models
4. **04_schemas_base.py** - Base response and pagination schemas
5. **05_frontend_sync_router.py** - Frontend API integration (Phase 11)

### Services Layer (Files 6-10)
6. **06_frontend_sync_service.py** - Frontend service implementation
7. **07_realtime_init.py** - Real-time services from Phase 11
8. **08_websocket_router.py** - WebSocket communication router
9. **09_core_security.py** - JWT and security utilities
10. **10_auth_service.py** - Authentication service logic

### Storage & Data (Files 11-15)
11. **11_storage_schemas.py** - Document storage and export schemas
12. **12_auth_router.py** - Authentication endpoints
13. **13_db_session.py** - Database session management
14. **14_main_app.py** - FastAPI application setup
15. **15_form_schemas.py** - Form-specific schemas for Phase 12

### Form Crowdsourcing Core (Files 16-20)
16. **16_form_registry_service.py** - Main form management service
17. **17_feedback_service.py** - User feedback collection service
18. **18_form_models.py** - Database models for forms and rewards
19. **19_forms_router.py** - Form API endpoints
20. **20_context_readme.md** - This documentation file

## Key Features Implemented

### 🏗️ **Form Registry System**
- **Upload Pipeline**: Multi-format file upload (PDF, DOCX)
- **Metadata Extraction**: County, state, language, jurisdiction
- **Duplicate Detection**: Hash-based and content similarity
- **Contributor Tracking**: Paralegal vs crowdsource attribution

### 🎯 **Reward System**
- **10 Pages = 1 Week Free**: Automatic reward calculation
- **Unique Page Tracking**: Prevents reward gaming
- **Reward Ledger**: Complete audit trail of granted benefits
- **Streak Bonuses**: Encourages consistent contributions

### 🔍 **Review Workflow**
- **Admin Review Interface**: Approve/reject/revision requests
- **Quality Scoring**: 1-10 rating system for forms
- **Review Comments**: Detailed feedback for contributors
- **Form Locking**: Approved forms become immutable

### 📊 **Analytics & Monitoring**
- **Ingestion Stats**: Upload rates, approval ratios
- **Contributor Leaderboards**: Top performers tracking
- **Quality Metrics**: Average scores, user feedback
- **System Health**: Performance and error monitoring

### 💬 **Feedback System**
- **Structured Feedback**: Field errors, parsing issues, suggestions
- **Severity Levels**: 1-5 importance scale
- **Ticket System**: Trackable feedback resolution
- **Admin Dashboard**: Feedback management interface

## Database Schema Overview

### Core Tables
- **forms**: Main form registry with metadata
- **contributor_stats**: Reward tracking per user
- **reward_ledger**: Detailed reward grant history
- **form_feedback**: User feedback and issue tracking

### Key Relationships
- Forms → Users (contributor, reviewer)
- Forms → Organizations (ownership)
- Rewards → Contributors (earning history)
- Feedback → Forms (quality tracking)

## API Endpoints Structure

### Form Management
- `POST /api/v2/forms/upload` - Upload new form
- `GET /api/v2/forms/` - List forms with filters
- `GET /api/v2/forms/{id}` - Form details
- `POST /api/v2/forms/{id}/review` - Admin review

### Contributor Features  
- `GET /api/v2/forms/contributor/{id}/rewards` - Reward status
- `POST /api/v2/forms/feedback` - Submit feedback
- `GET /api/v2/forms/stats/overview` - Public statistics

### Admin Functions
- `GET /api/v2/forms/feedback/stats` - Feedback analytics
- `GET /api/v2/forms/{id}/feedback` - Form-specific feedback

## Integration Points

### Phase 11 Dependencies
- Real-time notifications for form status updates
- WebSocket integration for live review status
- Frontend sync API for contributor dashboards

### Phase 14 Preparation
- AI validation hooks stubbed in form processing
- Field-level parsing preparation
- ML model integration points identified

### File Storage Integration
- Multi-provider support (AWS S3, Azure, GCP)
- Automatic format detection and conversion
- Secure download URL generation

## Security Considerations

### Access Control
- JWT-based authentication for all endpoints
- Role-based access (contributor, admin, reviewer)
- Organization-level data isolation

### Data Protection
- File hash verification for integrity
- Secure file storage with encryption
- PII handling in form metadata

### Rate Limiting
- Upload frequency limits per contributor
- Review request throttling
- Feedback submission controls

## Development Guidelines

### Testing Strategy
- Unit tests for service layer logic
- Integration tests for API endpoints
- End-to-end tests for complete workflows
- Performance tests for file upload scenarios

### Monitoring & Observability
- Upload success/failure metrics
- Review processing times
- Contributor engagement analytics
- System performance dashboards

### Deployment Considerations
- Horizontal scaling for file processing
- Database indexing for large form catalogs
- CDN integration for file downloads
- Background job processing for heavy operations

## Next Steps for Implementation

1. **Database Setup**: Create tables from model definitions
2. **File Storage**: Configure cloud storage providers  
3. **Form Processing**: Implement file parsing and validation
4. **Admin Interface**: Build review and management UI
5. **Testing**: Comprehensive test suite development
6. **Monitoring**: Set up analytics and alerting
7. **Documentation**: API documentation and user guides

This context provides a solid foundation for implementing the complete Phase 12 form crowdsourcing system with all required features and proper architectural separation.
