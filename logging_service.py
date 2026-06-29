"""Structured logging utilities for audit trails and debugging."""
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from flask import current_app, request, g, has_request_context, has_app_context
from flask_login import current_user

# Fallback logger for when there's no Flask app context at all (e.g. the
# background backup scheduler thread, or a bare CLI script) — current_app
# itself requires an app context, so logging through it would crash exactly
# when something has already gone wrong and most needs to be logged.
_fallback_logger = logging.getLogger('travel_worthy.background')


class StructuredLogger:
    """Helper class for structured logging with audit trail support."""

    @staticmethod
    def _get_logger() -> logging.Logger:
        """Return the Flask app logger when available, else a plain fallback."""
        if has_app_context():
            return current_app.logger
        return _fallback_logger

    @staticmethod
    def _get_request_context() -> Dict[str, Any]:
        """Extract relevant request context for logging.

        Returns:
            Dictionary with request details. Falls back to request-less
            context when called from outside an HTTP request (CLI commands,
            the background backup scheduler, etc.) instead of raising
            RuntimeError: Working outside of request context.
        """
        context: Dict[str, Any] = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

        if has_request_context():
            context.update({
                'remote_addr': request.remote_addr,
                'method': request.method,
                'endpoint': request.endpoint,
                'user_agent': request.headers.get('User-Agent', ''),
            })

        if has_app_context() and current_user and current_user.is_authenticated:
            context['user_id'] = current_user.id
            context['user_email'] = current_user.email

        return context

    @staticmethod
    def log_auth_event(event_type: str, email: str, success: bool, reason: Optional[str] = None) -> None:
        """Log authentication event with audit trail.
        
        Args:
            event_type: Type of auth event (login, register, logout, password_change)
            email: User email
            success: Whether event succeeded
            reason: Optional reason for failure
        """
        context = StructuredLogger._get_request_context()
        context.update({
            'event_type': 'auth',
            'auth_type': event_type,
            'email': email,
            'success': success,
            'reason': reason,
        })
        
        level = logging.INFO if success else logging.WARNING
        StructuredLogger._get_logger().log(level, json.dumps(context))

    @staticmethod
    def log_admin_action(action_type: str, resource_type: str, resource_id: int, 
                        changes: Optional[Dict[str, Any]] = None) -> None:
        """Log admin actions for compliance and audit.
        
        Args:
            action_type: Type of action (create, update, delete)
            resource_type: Type of resource (package, user, booking, etc.)
            resource_id: ID of resource affected
            changes: Dictionary of what changed
        """
        context = StructuredLogger._get_request_context()
        context.update({
            'event_type': 'admin_action',
            'action': action_type,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'changes': changes or {},
        })
        
        StructuredLogger._get_logger().info(json.dumps(context))

    @staticmethod
    def log_error(error_type: str, message: str, details: Optional[Dict[str, Any]] = None,
                 severity: str = 'ERROR') -> None:
        """Log application errors with full context.
        
        Args:
            error_type: Category of error (database, validation, file_upload, etc.)
            message: Human-readable error message
            details: Additional error details
            severity: ERROR, WARNING, CRITICAL
        """
        context = StructuredLogger._get_request_context()
        context.update({
            'event_type': 'error',
            'error_type': error_type,
            'message': message,
            'severity': severity,
            'details': details or {},
        })
        
        level_map = {
            'ERROR': logging.ERROR,
            'WARNING': logging.WARNING,
            'CRITICAL': logging.CRITICAL,
        }
        level = level_map.get(severity, logging.ERROR)
        StructuredLogger._get_logger().log(level, json.dumps(context))

    @staticmethod
    def log_database_query(query_type: str, table: str, duration_ms: float, 
                          rows_affected: int, success: bool) -> None:
        """Log database operations for performance monitoring.
        
        Args:
            query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
            table: Table name
            duration_ms: Query execution time in milliseconds
            rows_affected: Number of rows affected
            success: Whether query succeeded
        """
        context = StructuredLogger._get_request_context()
        context.update({
            'event_type': 'database',
            'query_type': query_type,
            'table': table,
            'duration_ms': duration_ms,
            'rows_affected': rows_affected,
            'success': success,
        })
        
        StructuredLogger._get_logger().debug(json.dumps(context))


def log_function_call(func_name: str, **kwargs) -> None:
    """Decorator helper to log function calls.
    
    Args:
        func_name: Name of function being called
        **kwargs: Additional context to log
    """
    context = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event_type': 'function_call',
        'function': func_name,
        **kwargs
    }
    
    if has_app_context() and current_user and current_user.is_authenticated:
        context['user_id'] = current_user.id

    StructuredLogger._get_logger().debug(json.dumps(context))