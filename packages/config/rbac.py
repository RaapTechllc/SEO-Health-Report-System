"""
Role-Based Access Control (RBAC) for multi-tenant SEO Health Report System.

Provides role and permission management with FastAPI dependency injection.
"""

from enum import Enum
from typing import Callable

from fastapi import Depends, HTTPException, status


class Role(str, Enum):
    """User roles within a tenant."""
    ADMIN = "admin"
    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Granular permissions for actions."""
    CREATE_AUDIT = "create_audit"
    VIEW_AUDIT = "view_audit"
    DELETE_AUDIT = "delete_audit"
    MANAGE_USERS = "manage_users"
    MANAGE_BILLING = "manage_billing"
    VIEW_REPORTS = "view_reports"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.ADMIN: {
        Permission.CREATE_AUDIT,
        Permission.VIEW_AUDIT,
        Permission.DELETE_AUDIT,
        Permission.MANAGE_USERS,
        Permission.MANAGE_BILLING,
        Permission.VIEW_REPORTS,
    },
    Role.OWNER: {
        Permission.CREATE_AUDIT,
        Permission.VIEW_AUDIT,
        Permission.DELETE_AUDIT,
        Permission.MANAGE_USERS,
        Permission.MANAGE_BILLING,
        Permission.VIEW_REPORTS,
    },
    Role.MEMBER: {
        Permission.CREATE_AUDIT,
        Permission.VIEW_AUDIT,
        Permission.VIEW_REPORTS,
    },
    Role.VIEWER: {
        Permission.VIEW_AUDIT,
        Permission.VIEW_REPORTS,
    },
}


def has_permission(user_role: str | Role, permission: str | Permission) -> bool:
    """
    Check if a role has a specific permission.

    Args:
        user_role: The user's role (string or Role enum)
        permission: The permission to check (string or Permission enum)

    Returns:
        True if the role has the permission, False otherwise
    """
    try:
        role = Role(user_role) if isinstance(user_role, str) else user_role
        perm = Permission(permission) if isinstance(permission, str) else permission
    except ValueError:
        return False

    role_perms = ROLE_PERMISSIONS.get(role, set())
    return perm in role_perms


def require_permission(permission: Permission | str) -> Callable:
    """
    FastAPI dependency that requires a specific permission.

    Usage:
        @router.post("/audits")
        async def create_audit(
            user: User = Depends(require_permission(Permission.CREATE_AUDIT))
        ):
            ...

    Args:
        permission: The required permission

    Returns:
        FastAPI dependency function
    """
    from auth import require_auth

    async def permission_dependency(user=Depends(require_auth)):
        perm = Permission(permission) if isinstance(permission, str) else permission

        if not has_permission(user.role, perm):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {perm.value} required"
            )
        return user

    return permission_dependency


def get_user_permissions(user_role: str | Role) -> set[Permission]:
    """
    Get all permissions for a given role.

    Args:
        user_role: The user's role

    Returns:
        Set of permissions for the role
    """
    try:
        role = Role(user_role) if isinstance(user_role, str) else user_role
    except ValueError:
        return set()

    return ROLE_PERMISSIONS.get(role, set())


__all__ = [
    "Role",
    "Permission",
    "ROLE_PERMISSIONS",
    "has_permission",
    "require_permission",
    "get_user_permissions",
]
