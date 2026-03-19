#!/bin/bash
# run_migrations.sh - Database migration script for CI/CD
# Usage:
#   ./run_migrations.sh status       - Show current migration state
#   ./run_migrations.sh upgrade      - Run all pending migrations
#   ./run_migrations.sh upgrade --backup - Backup before migrating
#   ./run_migrations.sh rollback <version> - Rollback to version
#   ./run_migrations.sh verify       - Verify migrations are current

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

print_header() {
    echo ""
    echo -e "${BLUE}=========================================="
    echo -e " $1"
    echo -e "==========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}! $1${NC}"
}

print_info() {
    echo -e "${BLUE}→ $1${NC}"
}

# Check database connectivity
check_database() {
    print_info "Checking database connectivity..."
    
    if python3 -c "
from sqlalchemy import create_engine, text
import os
engine = create_engine(os.environ.get('DATABASE_URL', 'sqlite:///./seo_health.db'))
with engine.connect() as conn:
    conn.execute(text('SELECT 1'))
print('connected')
" 2>/dev/null | grep -q "connected"; then
        print_success "Database connection successful"
        return 0
    else
        print_error "Failed to connect to database"
        return 1
    fi
}

# Show migration status
show_status() {
    print_header "Migration Status"
    
    cd "$PROJECT_ROOT"
    
    print_info "Current database revision:"
    python3 -m alembic current 2>/dev/null || echo "No migrations applied yet"
    
    echo ""
    print_info "Migration history:"
    python3 -m alembic history --verbose 2>/dev/null | head -20
    
    echo ""
    print_info "Pending migrations:"
    PENDING=$(python3 -m alembic heads 2>/dev/null)
    CURRENT=$(python3 -m alembic current 2>/dev/null | grep -oP '[a-f0-9]+' | head -1)
    
    if [ "$PENDING" = "$CURRENT" ] || [ -z "$PENDING" ]; then
        print_success "No pending migrations"
    else
        print_warning "Pending migrations exist"
        python3 -m alembic upgrade --sql head 2>/dev/null | head -50
    fi
}

# Create backup (PostgreSQL only)
create_backup() {
    print_header "Creating Database Backup"
    
    DATABASE_URL="${DATABASE_URL:-}"
    
    if [[ "$DATABASE_URL" == postgresql://* ]]; then
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
        print_info "Creating backup: $BACKUP_FILE"
        
        # Extract connection details from DATABASE_URL
        # Format: postgresql://user:password@host:port/database
        if pg_dump "$DATABASE_URL" > "$BACKUP_FILE" 2>/dev/null; then
            print_success "Backup created: $BACKUP_FILE"
            echo "$BACKUP_FILE"
        else
            print_warning "Backup failed (continuing anyway)"
        fi
    else
        print_warning "Backup skipped (SQLite or non-PostgreSQL database)"
    fi
}

# Run migrations
run_upgrade() {
    local BACKUP_FIRST=false
    
    # Check for --backup flag
    if [ "$1" = "--backup" ]; then
        BACKUP_FIRST=true
    fi
    
    print_header "Running Database Migrations"
    
    cd "$PROJECT_ROOT"
    
    # Check database connectivity
    if ! check_database; then
        print_error "Cannot proceed without database connection"
        exit 1
    fi
    
    # Create backup if requested
    if [ "$BACKUP_FIRST" = true ]; then
        create_backup
    fi
    
    # Show current state
    print_info "Current revision:"
    python3 -m alembic current 2>/dev/null || echo "None"
    
    # Run migrations
    print_info "Running migrations..."
    if python3 -m alembic upgrade head; then
        print_success "Migrations completed successfully"
        
        # Show new state
        echo ""
        print_info "New revision:"
        python3 -m alembic current
        
        return 0
    else
        print_error "Migration failed!"
        return 1
    fi
}

# Rollback to specific version
run_rollback() {
    local TARGET_VERSION="$1"
    
    if [ -z "$TARGET_VERSION" ]; then
        print_error "Rollback requires a target version"
        echo "Usage: $0 rollback <version>"
        echo "Example: $0 rollback v007"
        exit 1
    fi
    
    print_header "Rolling Back to Version: $TARGET_VERSION"
    
    cd "$PROJECT_ROOT"
    
    # Check database connectivity
    if ! check_database; then
        print_error "Cannot proceed without database connection"
        exit 1
    fi
    
    # Create backup before rollback
    print_warning "Creating backup before rollback..."
    create_backup
    
    # Show current state
    print_info "Current revision:"
    python3 -m alembic current
    
    # Confirm rollback
    echo ""
    print_warning "This will rollback the database to version: $TARGET_VERSION"
    print_warning "Data may be lost. Continue? (y/N)"
    
    # In CI, skip confirmation
    if [ "${CI:-false}" = "true" ]; then
        print_info "CI detected, proceeding with rollback..."
    else
        read -r CONFIRM
        if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
            print_info "Rollback cancelled"
            exit 0
        fi
    fi
    
    # Run rollback
    print_info "Rolling back..."
    if python3 -m alembic downgrade "$TARGET_VERSION"; then
        print_success "Rollback completed successfully"
        
        # Show new state
        echo ""
        print_info "New revision:"
        python3 -m alembic current
        
        return 0
    else
        print_error "Rollback failed!"
        return 1
    fi
}

# Verify migrations are current
verify_migrations() {
    print_header "Verifying Migrations"
    
    cd "$PROJECT_ROOT"
    
    # Check database connectivity
    if ! check_database; then
        print_error "Cannot proceed without database connection"
        exit 1
    fi
    
    # Get current and head revisions
    CURRENT=$(python3 -m alembic current 2>/dev/null | grep -oP '[a-f0-9]+' | head -1)
    HEAD=$(python3 -m alembic heads 2>/dev/null | grep -oP '[a-f0-9]+' | head -1)
    
    print_info "Current: ${CURRENT:-none}"
    print_info "Head: ${HEAD:-none}"
    
    if [ "$CURRENT" = "$HEAD" ]; then
        print_success "Database is up to date"
        return 0
    else
        print_error "Database is not up to date"
        print_info "Run './run_migrations.sh upgrade' to apply pending migrations"
        return 1
    fi
}

# Main
case "${1:-help}" in
    status)
        show_status
        ;;
    upgrade)
        run_upgrade "$2"
        ;;
    rollback)
        run_rollback "$2"
        ;;
    verify)
        verify_migrations
        ;;
    help|--help|-h)
        echo "Database Migration Script"
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  status              Show current migration state"
        echo "  upgrade             Run all pending migrations"
        echo "  upgrade --backup    Backup before migrating"
        echo "  rollback <version>  Rollback to specific version"
        echo "  verify              Verify migrations are current"
        echo ""
        echo "Examples:"
        echo "  $0 status"
        echo "  $0 upgrade"
        echo "  $0 upgrade --backup"
        echo "  $0 rollback v007"
        echo "  $0 verify"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Run '$0 help' for usage"
        exit 1
        ;;
esac
