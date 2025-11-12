# Implementation Plan

## Overview
Complete the organization platform implementation by finishing the remaining critical tasks: running the database migration safely, updating protected endpoints to use organization dependencies, updating service layers with organization scoping, and ensuring data migration for existing users.

The organization platform foundation is already solid with authentication dependencies, organization management endpoints, database models, and migration scripts in place. The core business rule "NO APP ACCESS WITHOUT ORG MEMBERSHIP" is implemented in the authentication layer. The remaining work focuses on systematic replacement of user-only dependencies with organization-aware dependencies throughout the application stack, ensuring all user-generated content is properly scoped to organizations while maintaining data integrity and avoiding breaking changes.

## Types
No new type definitions required - existing organization models are complete.

The existing type system in `backend/database/models.py` already includes all necessary organization-related types: `OrganizationRole`, `Organization`, `OrganizationMember` models with proper relationships. The database schema includes organization_id foreign keys on all user-generated content tables (documents, conversation_sessions, audio_files) with appropriate indexes for performance.

## Files
Detailed breakdown of file modifications required to complete the organization platform implementation.

**Migration Files:**
- `migrations/versions/2025_11_11_1416_6b9f23fe27b2_add_organization_scoping_to_documents_.py` - Already created, needs execution
- New migration file needed: `create_default_organizations_for_existing_users.py` - Create before running main migration

**API Endpoint Files:**
- `backend/api/admin_v2.py` - Replace 8 instances of `get_current_user` with `get_current_organization`
- `backend/api/organization.py` - Replace 7 instances of `get_current_user` with `get_current_organization` 
- `backend/api/chat.py` - Update session management endpoints to use organization dependency
- `backend/api/websocket.py` - Update WebSocket endpoints for organization scoping
- `backend/api/speech.py` - Update STT/TTS endpoints for organization context

**Service Layer Files:**
- `backend/services/document_service.py` - Add organization_id parameter to all methods, update queries
- `backend/services/session_service.py` - Add organization_id parameter to session operations
- `backend/graphs/chat_graph.py` - Pass organization context through workflow
- `backend/rag/vectorstore.py` - Add organization-scoped vector search methods

**Configuration Files:**
- No configuration changes required

## Functions
Detailed breakdown of function modifications required for organization scoping.

**New Functions to Create:**
- `create_default_organization_migration()` in new migration file - Create default organizations for existing users
- `get_organization_scoped_documents()` in document_service.py - Organization-aware document queries
- `get_organization_scoped_sessions()` in session_service.py - Organization-aware session queries
- `organization_scoped_search()` in vectorstore.py - Vector search within organization boundaries

**Modified Functions:**
- `upload_document()` in document_service.py - Add organization_id parameter and validation
- `process_document()` in document_service.py - Include organization context in processing
- `delete_document()` in document_service.py - Verify organization ownership before deletion
- `get_user_documents()` in document_service.py - Filter by organization_id
- `create_session()` in session_service.py - Add organization_id parameter
- `get_session()` in session_service.py - Validate organization membership
- `process_conversation_turn_async()` in chat_graph.py - Pass organization context
- `similarity_search()` in vectorstore.py - Add organization filtering

**Removed Functions:**
- No functions to be removed, only enhanced with organization context

## Classes
Detailed breakdown of class modifications for organization integration.

**Modified Classes:**
- `DocumentService` in document_service.py - Add organization validation to all methods
- `SessionService` in session_service.py - Add organization context to session management
- `VectorStore` in vectorstore.py - Add organization-scoped search capabilities

**New Classes:**
- No new classes required - existing classes will be enhanced

**Removed Classes:**
- No classes to be removed

## Dependencies
No new external dependencies required for organization platform completion.

All necessary dependencies are already installed:
- SQLAlchemy for database operations with organization relationships
- Alembic for database migrations
- FastAPI for API endpoints with dependency injection
- Existing authentication and authorization infrastructure

The implementation leverages existing dependency injection patterns in FastAPI, using the already-created `get_current_organization()` dependency to replace `get_current_user()` dependencies throughout the application.

## Testing
Comprehensive testing approach for organization platform validation.

**Migration Testing:**
- Test migration on development database with existing users
- Verify organization_id population for all existing records
- Test rollback functionality
- Validate foreign key constraints

**API Endpoint Testing:**
- Test all updated endpoints with organization context
- Verify 403 responses for users without organizations
- Test organization admin-only endpoints
- Validate cross-organization data isolation

**Service Layer Testing:**
- Test document operations with organization scoping
- Test session management with organization context
- Test vector search with organization filtering
- Verify data isolation between organizations

**Integration Testing:**
- End-to-end workflow testing with organization context
- Frontend integration with organization-aware APIs
- WebSocket functionality with organization scoping

## Implementation Order
Critical sequence of implementation steps to minimize conflicts and ensure successful integration.

**Phase 1: Pre-Migration Safety (CRITICAL FIRST)**
1. Create and run pre-migration script to create default organizations for existing users
2. Verify all existing users have active_organization_id set
3. Test migration on development database copy

**Phase 2: Database Migration**
4. Start database services (docker-compose up -d postgres)
5. Run organization scoping migration: `alembic upgrade head`
6. Verify migration success and data integrity

**Phase 3: API Endpoint Updates**
7. Update `backend/api/admin_v2.py` - Replace get_current_user with get_current_organization
8. Update `backend/api/organization.py` - Replace get_current_user with get_current_organization  
9. Update `backend/api/chat.py` - Add organization dependency to session endpoints
10. Update `backend/api/websocket.py` - Add organization context to WebSocket handlers
11. Update `backend/api/speech.py` - Add organization context to STT/TTS endpoints

**Phase 4: Service Layer Updates**
12. Update `backend/services/document_service.py` - Add organization_id to all methods
13. Update `backend/services/session_service.py` - Add organization_id to session operations
14. Update `backend/graphs/chat_graph.py` - Pass organization context through workflow
15. Update `backend/rag/vectorstore.py` - Add organization-scoped search methods

**Phase 5: Testing and Validation**
16. Test all API endpoints with organization context
17. Verify data isolation between organizations
18. Test frontend integration with updated APIs
19. Perform end-to-end workflow testing

**Phase 6: Frontend Integration (if needed)**
20. Update frontend authentication flow for organization requirements
21. Add organization selector UI components
22. Update route guards for organization membership validation
