### **Adding New Features**
Follow the **7-step Technical Debt Prevention workflow** in the `features/` folder structure:

#### **Steps 1-5: Core Implementation**
1. **Create Model** - `app/models/features/[feature_name]/`
2. **Create Schemas** - `app/schemas/features/[feature_name]/`
3. **Create CRUD** - `app/crud/features/[feature_name]/`
4. **Create API Routes** - `app/api/features/[feature_name]/`
5. **Create Migration** - `alembic/versions/`

#### **Step 6: ⚡ MANDATORY Technical Debt Check & Resolution**
BEFORE writing tests or documentation, run:
```bash
make debt-check
# or
./scripts/development/prevent_technical_debt.sh [feature_name]
```
This will:
- Scan for type errors (mypy), lint issues (ruff), and formatting (black)
- Auto-fix what’s safe (ruff --fix, black)
- Flag potential performance anti-pattern spikes
- Smoke-test imports to catch obvious breakages

#### **Step 7: Testing & Documentation**
6. Create Tests — `tests/[type]/features/[feature_name]/` (mirrors app structure)
7. Create Documentation — `docs/features/[feature_name]/` (5-file structure)


