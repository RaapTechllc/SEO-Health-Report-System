"""Root-level shim — canonical code lives in packages/auth/."""

from packages.auth import *  # noqa: F401,F403
from packages.auth import (  # noqa: F401 — explicit re-exports for type checkers
    authenticate_user,
    create_access_token,
    create_user,
    decode_token,
    get_current_user,
    get_user_by_id,
    get_user_by_id_and_tenant,
    get_users_by_tenant,
    hash_password,
    needs_rehash,
    require_admin,
    require_auth,
    verify_password,
)
