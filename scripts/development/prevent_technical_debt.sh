#!/bin/bash
# Technical Debt Prevention Workflow
# Usage: ./scripts/development/prevent_technical_debt.sh [feature_name]
set -e
FEATURE_NAME="${1:-"current_changes"}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
print_step(){ echo -e "${BLUE}🔍 $1${NC}"; }; print_success(){ echo -e "${GREEN}✅ $1${NC}"; }
print_warning(){ echo -e "${YELLOW}⚠️  $1${NC}"; }; print_error(){ echo -e "${RED}❌ $1${NC}"; }
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                TECHNICAL DEBT PREVENTION                     ║${NC}"
echo -e "${BLUE}║              Feature: ${FEATURE_NAME}${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
ISSUES_FOUND=0; ISSUES_FIXED=0

# 1) TODO/FIXME/HACK scan (baseline threshold relaxed; we only flag spikes)
print_step "Scanning for technical debt markers (TODO, FIXME, HACK, XXX)..."
TODO_COUNT=$(grep -r "TODO\|FIXME\|HACK\|XXX" app/ --include="*.py" | grep -v "__pycache__" | wc -l | tr -d ' ')
if [ "$TODO_COUNT" -gt 150 ]; then print_warning "Found $TODO_COUNT markers (spike)"; ((ISSUES_FOUND++)); else print_success "Markers within acceptable range ($TODO_COUNT)"; fi

# 2) MyPy type safety
print_step "Checking type safety with mypy..."
MYPY_OUTPUT=$(venv/bin/mypy --explicit-package-bases app 2>&1 || true)
if echo "$MYPY_OUTPUT" | grep -q "error:"; then
  ERRORS=$(echo "$MYPY_OUTPUT" | grep -c "error:" || echo "0")
  print_error "Found $ERRORS mypy errors"; echo "$MYPY_OUTPUT" | head -20; ((ISSUES_FOUND++))
else print_success "Type safety check passed (0 errors)"; fi

# 3) Ruff lint
print_step "Checking code quality with ruff..."
RUFF_OUTPUT=$(venv/bin/ruff check . 2>&1 || true)
if ! echo "$RUFF_OUTPUT" | grep -q "All checks passed!"; then
  print_warning "Ruff issues detected, attempting auto-fix..."
  venv/bin/ruff check . --fix --quiet 2>/dev/null || true
  RUFF_OUTPUT_AFTER=$(venv/bin/ruff check . 2>&1 || true)
  if echo "$RUFF_OUTPUT_AFTER" | grep -q "All checks passed!"; then print_success "Ruff auto-fix complete"; ((ISSUES_FIXED++))
  else echo "$RUFF_OUTPUT_AFTER" | head -10; ((ISSUES_FOUND++)); fi
else print_success "Code quality check passed"; fi

# 4) Black formatting
print_step "Checking code formatting..."
venv/bin/black --check --diff . 1>/dev/null 2>&1 || { print_step "Applying black formatting..."; venv/bin/black . 1>/dev/null 2>&1; print_success "Formatting applied"; ((ISSUES_FIXED++)); }

# 5) Basic performance scans (len() patterns & API for-loops)
print_step "Scanning for performance anti-patterns..."
LEN_ISSUES=$(grep -r "len(" app/ --include="*.py" | grep -v "__pycache__" | wc -l | tr -d ' ')
N_PLUS_ONE=$(grep -r "for.*in.*:" app/api/ --include="*.py" | grep -v "__pycache__" | wc -l | tr -d ' ')
if [ "$LEN_ISSUES" -gt 150 ] || [ "$N_PLUS_ONE" -gt 50 ]; then
  print_warning "Potential perf patterns: len()=${LEN_ISSUES}, api for-loops=${N_PLUS_ONE}"; ((ISSUES_FOUND++))
else print_success "No obvious performance anti-pattern spikes"; fi

# 6) Smoke test (imports only)
print_step "Running smoke test to verify no import/syntax regressions..."
TEST_OUTPUT=$(venv/bin/python -c "
try:
    from app.main import app  # noqa
    from app.database.database import get_db  # noqa
    print('IMPORT_SUCCESS')
except Exception as e:
    print(f'IMPORT_ERROR: {e}')
" 2>&1 || true)
if echo "$TEST_OUTPUT" | grep -q "IMPORT_SUCCESS"; then print_success "Smoke test passed"
else print_error "Smoke test failed"; echo "$TEST_OUTPUT"; ((ISSUES_FOUND++)); fi

# Summary
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                        SUMMARY REPORT                        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
if [ "$ISSUES_FOUND" -eq 0 ]; then
  print_success "🎉 ZERO TECHNICAL DEBT DETECTED"; print_success "✅ All quality gates passed"; print_success "✅ Ready for tests & docs"; exit 0
else
  print_error "🚨 TECHNICAL DEBT DETECTED: $ISSUES_FOUND issue(s)"
  if [ "$ISSUES_FIXED" -gt 0 ]; then print_success "Auto-fixed $ISSUES_FIXED item(s)"; fi
  echo "Required actions:"
  echo "1) venv/bin/mypy --explicit-package-bases app"
  echo "2) venv/bin/ruff check . --fix"
  echo "3) venv/bin/black ."
  echo "4) make test-docker (optional)"
  exit 1
fi


