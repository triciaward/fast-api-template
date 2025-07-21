from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.crud import user as crud_user
from app.models.models import User
from app.schemas.user import UserCreate
from app.utils.search_filter import (
    FieldFilter,
    FilterOperator,
    SearchFilterBuilder,
    SearchFilterConfig,
    SearchOperator,
    TextSearchFilter,
    UserSearchParams,
    create_user_search_filters,
)


class TestSearchFilterUtility:
    """Test the search and filter utility functionality."""

    def test_search_filter_builder_initialization(self, sync_db_session: Session):
        """Test SearchFilterBuilder initialization."""
        builder = SearchFilterBuilder(User)
        assert builder.model_class == User
        assert "id" in builder._allowed_fields
        assert "email" in builder._allowed_fields
        assert "username" in builder._allowed_fields

    def test_field_validation(self, sync_db_session: Session):
        """Test field validation in SearchFilterBuilder."""
        builder = SearchFilterBuilder(User)

        # Valid fields
        assert builder._validate_field("email") is True
        assert builder._validate_field("username") is True
        assert builder._validate_field("is_verified") is True

        # Invalid fields
        assert builder._validate_field("invalid_field") is False
        assert builder._validate_field("") is False

    def test_text_search_contains(self, sync_db_session: Session):
        """Test text search with CONTAINS operator."""
        # Create test users
        _user1 = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="trish@example.com",
                username="trish_ward",
                password="Password123!",
            ),
        )
        _user2 = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="john@example.com", username="john_doe", password="Password123!"
            ),
        )

        # Test search configuration
        text_search = TextSearchFilter(
            query="trish",
            fields=["username", "email"],
            operator=SearchOperator.CONTAINS,
            case_sensitive=False,
        )

        config = SearchFilterConfig(text_search=text_search, sort_by=None)
        builder = SearchFilterBuilder(User)
        query = builder.build_query(config)

        result = sync_db_session.execute(query)
        users = result.scalars().all()

        assert len(users) == 1
        assert users[0].username == "trish_ward"

    def test_text_search_starts_with(self, sync_db_session: Session):
        """Test text search with STARTS_WITH operator."""
        # Create test users
        _user1 = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="trish@example.com",
                username="trish_ward",
                password="Password123!",
            ),
        )
        _user2 = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="john@example.com", username="john_doe", password="Password123!"
            ),
        )

        # Test search configuration
        text_search = TextSearchFilter(
            query="trish",
            fields=["username"],
            operator=SearchOperator.STARTS_WITH,
            case_sensitive=False,
        )

        config = SearchFilterConfig(text_search=text_search, sort_by=None)
        builder = SearchFilterBuilder(User)
        query = builder.build_query(config)

        result = sync_db_session.execute(query)
        users = result.scalars().all()

        assert len(users) == 1
        assert users[0].username == "trish_ward"

    def test_boolean_filter(self, sync_db_session: Session):
        """Test boolean field filtering."""
        # Create test users
        _user1 = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="trish@example.com",
                username="trish_ward",
                password="Password123!",
            ),
        )
        _user2 = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="john@example.com", username="john_doe", password="Password123!"
            ),
        )

        # Verify user1
        crud_user.verify_user_sync(sync_db_session, str(_user1.id))

        # Test filter configuration
        field_filter = FieldFilter(
            field="is_verified", operator=FilterOperator.EQUALS, value=True, values=None
        )

        config = SearchFilterConfig(
            text_search=None, filters=[field_filter], sort_by=None
        )
        builder = SearchFilterBuilder(User)
        query = builder.build_query(config)

        result = sync_db_session.execute(query)
        users = result.scalars().all()

        assert len(users) == 1
        assert users[0].is_verified is True

    def test_date_range_filter(self, sync_db_session: Session):
        """Test date range filtering."""
        # Create test users with different creation dates
        _user1 = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="old@example.com", username="old_user", password="Password123!"
            ),
        )

        # Manually set creation date for user1 to be old
        old_date = datetime.utcnow() - timedelta(days=30)
        _user1.date_created = old_date  # type: ignore
        sync_db_session.commit()

        _user2 = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="new@example.com", username="new_user", password="Password123!"
            ),
        )

        # Test date range filter
        recent_date = datetime.utcnow() - timedelta(days=7)

        field_filter = FieldFilter(
            field="date_created",
            operator=FilterOperator.GREATER_THAN_EQUAL,
            value=recent_date,
            values=None,
        )

        config = SearchFilterConfig(
            text_search=None, filters=[field_filter], sort_by=None
        )
        builder = SearchFilterBuilder(User)
        query = builder.build_query(config)

        result = sync_db_session.execute(query)
        users = result.scalars().all()

        assert len(users) == 1
        assert users[0].username == "new_user"

    def test_combined_search_and_filter(self, sync_db_session: Session):
        """Test combining text search with field filters."""
        # Create test users
        _user1 = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="trish@example.com",
                username="trish_ward",
                password="Password123!",
            ),
        )
        _user2 = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="john@example.com", username="john_doe", password="Password123!"
            ),
        )

        # Verify user1
        crud_user.verify_user_sync(sync_db_session, str(_user1.id))

        # Test combined configuration
        text_search = TextSearchFilter(
            query="trish",
            fields=["username", "email"],
            operator=SearchOperator.CONTAINS,
            case_sensitive=False,
        )

        field_filter = FieldFilter(
            field="is_verified", operator=FilterOperator.EQUALS, value=True, values=None
        )

        config = SearchFilterConfig(
            text_search=text_search, filters=[field_filter], sort_by=None
        )

        builder = SearchFilterBuilder(User)
        query = builder.build_query(config)

        result = sync_db_session.execute(query)
        users = result.scalars().all()

        assert len(users) == 1
        assert users[0].username == "trish_ward"
        assert users[0].is_verified is True

    def test_sorting(self, sync_db_session: Session):
        """Test query sorting."""
        # Create test users
        _user1 = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="alice@example.com", username="alice", password="Password123!"
            ),
        )
        _user2 = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="bob@example.com", username="bob", password="Password123!"
            ),
        )

        # Test ascending sort
        config = SearchFilterConfig(
            text_search=None, sort_by="username", sort_order="asc"
        )
        builder = SearchFilterBuilder(User)
        query = builder.build_query(config)

        result = sync_db_session.execute(query)
        users = result.scalars().all()

        assert users[0].username == "alice"
        assert users[1].username == "bob"

        # Test descending sort
        config = SearchFilterConfig(
            text_search=None, sort_by="username", sort_order="desc"
        )
        query = builder.build_query(config)

        result = sync_db_session.execute(query)
        users = result.scalars().all()

        assert users[0].username == "bob"
        assert users[1].username == "alice"

    def test_create_user_search_filters(self):
        """Test the convenience function for creating user search filters."""
        config = create_user_search_filters(
            search_query="trish",
            is_verified=True,
            oauth_provider="google",
            sort_by="date_created",
            sort_order="desc",
        )

        assert config.text_search is not None
        assert config.text_search.query == "trish"
        assert config.text_search.fields == ["username", "email"]
        assert len(config.filters) == 2  # is_verified and oauth_provider
        assert config.sort_by == "date_created"
        assert config.sort_order == "desc"

    def test_user_search_params(self):
        """Test UserSearchParams model."""
        params = UserSearchParams(
            search="trish",
            is_verified=True,
            oauth_provider="google",
            sort_by="date_created",
            sort_order="desc",
        )

        config = params.to_search_config()

        assert config.text_search is not None
        assert config.text_search.query == "trish"
        assert len(config.filters) == 2
        assert config.sort_by == "date_created"
        assert config.sort_order == "desc"

    def test_oauth_provider_none_filter(self, sync_db_session: Session):
        """Test filtering for users without OAuth provider."""
        # Create regular user (no OAuth)
        _user1 = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="regular@example.com",
                username="regular_user",
                password="Password123!",
            ),
        )

        # Create OAuth user
        _user2 = crud_user.create_oauth_user_sync(
            db=sync_db_session,
            email="oauth@example.com",
            username="oauth_user",
            oauth_provider="google",
            oauth_id="123",
            oauth_email="oauth@example.com",
        )

        # Test filtering for non-OAuth users
        field_filter = FieldFilter(
            field="oauth_provider",
            operator=FilterOperator.IS_NULL,
            value=None,
            values=None,
        )

        config = SearchFilterConfig(
            text_search=None, filters=[field_filter], sort_by=None
        )
        builder = SearchFilterBuilder(User)
        query = builder.build_query(config)

        result = sync_db_session.execute(query)
        users = result.scalars().all()

        assert len(users) == 1
        assert users[0].username == "regular_user"

    def test_case_insensitive_search(self, sync_db_session: Session):
        """Test case insensitive text search."""
        # Create test user
        _user = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="Trish@Example.com",
                username="Trish_Ward",
                password="Password123!",
            ),
        )

        # Test case insensitive search
        text_search = TextSearchFilter(
            query="trish",
            fields=["username", "email"],
            operator=SearchOperator.CONTAINS,
            case_sensitive=False,
        )

        config = SearchFilterConfig(text_search=text_search, sort_by=None)
        builder = SearchFilterBuilder(User)
        query = builder.build_query(config)

        result = sync_db_session.execute(query)
        users = result.scalars().all()

        assert len(users) == 1
        assert users[0].username == "Trish_Ward"

    def test_case_sensitive_search(self, sync_db_session: Session):
        """Test case sensitive text search."""
        # Create test user
        _user = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="Trish@Example.com",
                username="Trish_Ward",
                password="Password123!",
            ),
        )

        # Test case sensitive search (should not find "trish" in "Trish")
        text_search = TextSearchFilter(
            query="trish",
            fields=["username"],  # Only search username, not email
            operator=SearchOperator.CONTAINS,
            case_sensitive=True,
        )

        config = SearchFilterConfig(text_search=text_search, sort_by=None)
        builder = SearchFilterBuilder(User)
        query = builder.build_query(config)

        result = sync_db_session.execute(query)
        users = result.scalars().all()

        # Should not find anything with case sensitive search
        assert len(users) == 0

    def test_invalid_field_handling(self, sync_db_session: Session):
        """Test handling of invalid field names."""
        # Create test user
        _user = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="test@example.com", username="test_user", password="Password123!"
            ),
        )

        # Test with invalid field name
        field_filter = FieldFilter(
            field="invalid_field",
            operator=FilterOperator.EQUALS,
            value="test",
            values=None,
        )

        config = SearchFilterConfig(
            text_search=None, filters=[field_filter], sort_by=None
        )
        builder = SearchFilterBuilder(User)
        query = builder.build_query(config)

        result = sync_db_session.execute(query)
        users = result.scalars().all()

        # Should return all users since invalid filter is ignored
        assert len(users) == 1

    def test_empty_search_query(self, sync_db_session: Session):
        """Test handling of empty search queries."""
        # Create test user
        _user = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="test@example.com", username="test_user", password="Password123!"
            ),
        )

        # Test with empty query
        text_search = TextSearchFilter(
            query="   ",  # Whitespace only
            fields=["username", "email"],
            operator=SearchOperator.CONTAINS,
        )

        config = SearchFilterConfig(text_search=text_search, sort_by=None)
        builder = SearchFilterBuilder(User)
        query = builder.build_query(config)

        result = sync_db_session.execute(query)
        users = result.scalars().all()

        # Should return all users (no search filter applied)
        assert len(users) >= 1

    def test_full_text_search_option(self, sync_db_session: Session):
        """Test full-text search option (should fall back to LIKE if not available)."""
        # Create test users
        _user1 = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="trish@example.com",
                username="trish_ward",
                password="Password123!",
            ),
        )
        _user2 = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="john@example.com", username="john_doe", password="Password123!"
            ),
        )

        # Test full-text search configuration
        text_search = TextSearchFilter(
            query="trish",
            fields=["username", "email"],
            operator=SearchOperator.CONTAINS,
            case_sensitive=False,
            use_full_text_search=True,
        )

        config = SearchFilterConfig(text_search=text_search, sort_by=None)
        builder = SearchFilterBuilder(User)
        query = builder.build_query(config)

        result = sync_db_session.execute(query)
        users = result.scalars().all()

        # Should still find the user (either via full-text or fallback)
        assert len(users) >= 1

    def test_enhanced_sorting_validation(self, sync_db_session: Session):
        """Test enhanced sorting validation with invalid sort fields."""
        # Create test user
        _user = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="test@example.com", username="test_user", password="Password123!"
            ),
        )

        # Test with invalid sort field
        config = SearchFilterConfig(
            text_search=None, sort_by="invalid_field", sort_order="asc"
        )
        builder = SearchFilterBuilder(User)
        query = builder.build_query(config)

        result = sync_db_session.execute(query)
        users = result.scalars().all()

        # Should return users without sorting (invalid field ignored)
        assert len(users) >= 1

    def test_sort_order_validation(self, sync_db_session: Session):
        """Test sort order validation with invalid values."""
        # Create test user
        _user = crud_user.create_user_sync(
            sync_db_session,
            UserCreate(
                email="test@example.com", username="test_user", password="Password123!"
            ),
        )

        # Test with invalid sort order
        config = SearchFilterConfig(
            text_search=None, sort_by="username", sort_order="invalid_order"
        )
        builder = SearchFilterBuilder(User)
        query = builder.build_query(config)

        result = sync_db_session.execute(query)
        users = result.scalars().all()

        # Should return users with default ascending sort
        assert len(users) >= 1

    def test_user_search_params_with_full_text(self):
        """Test UserSearchParams with full-text search option."""
        params = UserSearchParams(
            search="test",
            use_full_text_search=True,
            is_verified=True,
            sort_by="username",
            sort_order="desc",
        )

        config = params.to_search_config()
        assert config.text_search is not None
        assert config.text_search.use_full_text_search is True
        assert config.sort_by == "username"
        assert config.sort_order == "desc"
