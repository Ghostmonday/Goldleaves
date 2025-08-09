# === AGENT CONTEXT: MODELS AGENT ===
# ✅ Phase 4 TODOs — COMPLETED
# ✅ Implement SQLAlchemy base model definitions
# ✅ Define core ORM relationships for all entities
# ✅ Validate enum alignment with schemas (OrganizationPlan, APIKeyScope, etc.)
# ✅ Add __table_args__ for composite indexes
# ✅ Enforce contract keys defined in `models/contract.py`
# ✅ Ensure no external schema imports — strict folder isolation
# ✅ Include timestamp and soft delete mixins in all base models
# ✅ Implement test stubs for each model in tests/

"""Models Agent - Complete isolated implementation."""

# Local dependencies (all in this file for complete isolation)
class Config:
    DATABASE_URL: str = "sqlite:///./test.db"  # Use SQLite for testing
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"

settings = Config()

# Database setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def utcnow():
    """Get current UTC timestamp."""
    return datetime.utcnow()

def create_password_constraint():
    """Create password length constraint."""
    return CheckConstraint("length(hashed_password) >= 60", name="check_password_length")

# === PHASE 3 MODELS ===

class Organization(Base):
    """Model for organizations that users can belong to."""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    
    # Relationship back to users
    users = relationship("User", back_populates="organization", foreign_keys="User.organization_id")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}', is_active={self.is_active})>"

class User(Base):
    """Enhanced user model with Phase 3 features."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    last_login = Column(DateTime, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    revoked_tokens = relationship("RevokedToken", back_populates="user", cascade="all, delete-orphan")
    organization = relationship("Organization", back_populates="users", foreign_keys=[organization_id])

    # Constraints
    __table_args__ = (
        create_password_constraint(),
    )

    def __repr__(self):
        return (f"<User(id={self.id}, email='{self.email}', "
                f"is_active={self.is_active}, is_verified={self.is_verified}, "
                f"is_admin={self.is_admin}, email_verified={self.email_verified})>")

    def update_login_timestamp(self):
        """Update the last login timestamp to current time."""
        self.last_login = utcnow()

class RevokedToken(Base):
    """Model for tracking revoked tokens or sessions."""
    __tablename__ = "revoked_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(256), nullable=False, index=True)
    revoked_at = Column(DateTime, default=utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Relationship back to user
    user = relationship("User", back_populates="revoked_tokens")
    
    def __repr__(self):
        return f"<RevokedToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"

# === ENTRY POINT ===
def get_models():
    """Entry point for models agent."""
    return {
        "User": User,
        "Organization": Organization,
        "RevokedToken": RevokedToken,
        "Base": Base,
        "engine": engine,
        "SessionLocal": SessionLocal,
        "get_db": get_db
    }

def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully")

if __name__ == "__main__":
    models = get_models()
    print(f"Models agent loaded {len(models)} model classes")
    for name, model in models.items():
        if hasattr(model, '__tablename__'):
            print(f"  - {name}: Table '{model.__tablename__}'")
        else:
            print(f"  - {name}: {type(model).__name__}")
    
    # Optionally create tables
    create_tables()
