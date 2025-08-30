# How to Build Features: Debt-Free Development Workflow 🚀

> **For AI Agents**: This template uses a **7-step workflow** that prevents technical debt by catching problems early. Follow the steps exactly in order - Step 6 (debt-check) is MANDATORY before tests/docs.

## 🧠 The Big Picture (ELI5)

Think of building features like building with LEGO:
1. **Steps 1-5**: Build the main structure (models, APIs, etc.)
2. **Step 6**: Quality inspector checks everything and fixes problems automatically 
3. **Step 7**: Write the instruction manual (tests + docs)

**Why this order?** Fixing problems when they're small is 10x easier than fixing a giant mess later!

## 🚀 The 7-Step Feature Development Workflow

### **Steps 1-5: Core Implementation** 
*Build the feature foundation first - like constructing the house before decorating*

```bash
# Example: Building a "book_reviews" feature
```

1. **📊 Create Model** → `app/models/features/[feature_name]/`
   - Define what your data looks like in the database
   - Use SQLAlchemy 2.0 with proper typing (`Mapped[str]`, `mapped_column()`)

2. **📋 Create Schemas** → `app/schemas/features/[feature_name]/`  
   - Define how data travels in/out of your API
   - Use Pydantic models for validation

3. **🔧 Create CRUD** → `app/crud/features/[feature_name]/`
   - Write database operations (Create, Read, Update, Delete)
   - Keep business logic separate from API logic

4. **🌐 Create API Routes** → `app/api/features/[feature_name]/`
   - Build the actual endpoints users will call
   - Add proper `response_model` and error handling

5. **📦 Create Migration** → `alembic/versions/`
   ```bash
   alembic revision --autogenerate -m "Add [feature_name] feature"
   alembic upgrade head
   ```

### **Step 6: ⚡ MANDATORY Technical Debt Prevention** 
*This is your quality gate - like a building inspector before move-in*

**🚨 CRITICAL**: Run this BEFORE writing tests or documentation:

```bash
make debt-check
# or for AI agents:
./scripts/development/prevent_technical_debt.sh [feature_name]
```

**What happens automatically:**
- 🔍 **Type Safety Check**: Finds mypy errors (like checking if puzzle pieces fit)
- 🧹 **Code Quality**: Auto-fixes formatting and style issues  
- ⚡ **Performance Scan**: Flags potential slow patterns
- 🚨 **Smoke Test**: Ensures imports work (catches obvious breakages)

**Expected Output:**
```bash
🎉 ZERO TECHNICAL DEBT DETECTED
✅ All quality gates passed  
✅ Ready for tests & docs
```

**If issues found:**
- Most problems auto-fix themselves
- Manual fixes needed are clearly listed
- Don't proceed until this passes!

### **Step 7: Testing & Documentation**
*Now write the instruction manual - everything should work perfectly*

6. **🧪 Create Tests** → `tests/[type]/features/[feature_name]/`
   - Mirror the app structure in your test folders
   - Write unit tests, integration tests, and edge case tests

7. **📚 Create Documentation** → `docs/features/[feature_name]/`
   - Create 5-file documentation structure:
     - `FEATURE_README.md` (overview)  
     - `api_reference.md` (endpoints)
     - `technical_design.md` (architecture)
     - `testing_strategy.md` (test approach)
     - `implementation_roadmap.md` (development plan)

## 🛠️ Quick Commands (For Daily Development)

```bash
# Format and lint code manually
ruff check .
black .

# Type check the app
python -m mypy app

# SQLAlchemy-specific type checking  
./scripts/development/mypy_sa_check.sh

# Run all pre-commit hooks
pre-commit run --all-files

# The magic debt-prevention command
make debt-check
```

## 🤖 AI Agent Instructions

When building features for this template:

1. **Always follow the 7-step order** - don't skip steps!
2. **Step 6 is non-negotiable** - run `make debt-check` and fix all issues before proceeding
3. **Use the exact folder structure** shown above
4. **Check that the debt-check passes** with "ZERO TECHNICAL DEBT DETECTED" message
5. **Mirror app structure in tests** - if you have `app/api/features/books/`, create `tests/api/features/books/`

## 💡 Why This Works

**Traditional approach (chaos):**
```
Build feature → Write tests → Discover 50 type errors → Fix errors → Tests break → Fix tests → More errors → 😭
```

**Our approach (zen):**  
```
Build feature → Debt-check catches 2-3 small issues → Auto-fix → Tests work perfectly → 😎
```

It's like washing dishes while cooking instead of leaving a giant pile for later!

## Prompt templates

- Migrate models in a feature
  "Convert app/models/<feature>/* to SQLAlchemy 2.0 typing. Use Mapped[...] and mapped_column(...), typed relationship annotations, TYPE_CHECKING for forward refs, and the assigned hybrid_property + .expression pattern. Remove broad ignores. Ensure ./scripts/development/mypy_sa_check.sh and mypy app pass, then add strict mypy overrides for these modules."

- Fix service initializer/decorators
  "Refactor app/services/**/__init__.py optional imports to predeclared typed Optionals, alias imports, and safe no-op fallbacks. Type custom decorators using ParamSpec/TypeVar so wrapped functions preserve their signatures. Ensure mypy app passes."

- Normalize dynamic values
  "Search for headers/cookies access and ORM scalar returns across services and crud. Ensure returns are str or str | None; assign ORM scalars to typed locals before returning. Remove ‘returning Any’ and unused-ignore. Keep ruff+mypy clean."

## PR checklist

- [ ] SQLAlchemy typed ORM used (`Mapped[...]`, `mapped_column(...)`, typed `relationship(...)`)
- [ ] Forward refs via `TYPE_CHECKING` blocks
- [ ] Decorators preserve signatures via `ParamSpec`/`TypeVar`
- [ ] Optional imports predeclared as Optionals with safe fallbacks
- [ ] Endpoints have `response_model` and return matching schema types
- [ ] Headers/cookies return `str | None` consistently
- [ ] ORM scalars assigned to typed locals before return
- [ ] mypy (app only) is clean; plugin script is green
- [ ] Ruff + Black clean
