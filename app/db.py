from psycopg.conninfo import conninfo_to_dict
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from .config import settings
from .models import Base


def _normalize_database_url(raw_value: str):
    """Return a SQLAlchemy-compatible database URL without exposing credentials."""
    raw = raw_value.strip()

    if not raw:
        raise RuntimeError("Database connection string is empty")

    # Local development SQLite URL.
    if raw.startswith("sqlite"):
        return raw

    # Already a PostgreSQL URL. Force the installed psycopg v3 driver.
    if raw.startswith("postgresql+psycopg://"):
        return raw
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+psycopg://", 1)
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql+psycopg://", 1)

    # Azure may provide an ADO-style semicolon-delimited connection string.
    if ";" in raw:
        values = {}
        for part in raw.split(";"):
            part = part.strip()
            if not part or "=" not in part:
                continue
            key, value = part.split("=", 1)
            values[key.strip().lower().replace(" ", "")] = value.strip()

        host = values.get("host") or values.get("server")
        database = values.get("database") or values.get("dbname") or values.get("initialcatalog")
        username = (
            values.get("username")
            or values.get("userid")
            or values.get("user")
            or values.get("uid")
        )
        password = values.get("password") or values.get("pwd")
        port = values.get("port")
        sslmode = values.get("sslmode")

        if host and host.lower().startswith("tcp:"):
            host = host[4:]

        if not all([host, database, username, password]):
            raise RuntimeError(
                "Azure PostgreSQL connection string is missing host, database, username, or password"
            )

        query = {"sslmode": sslmode.lower()} if sslmode else {}
        return URL.create(
            "postgresql+psycopg",
            username=username,
            password=password,
            host=host,
            port=int(port) if port else 5432,
            database=database,
            query=query,
        )

    # Azure PostgreSQL commonly provides libpq format:
    # host=... port=5432 dbname=... user=... password=... sslmode=require
    try:
        values = conninfo_to_dict(raw)
    except Exception as exc:
        raise RuntimeError(
            "AZURE_POSTGRESQL_CONNECTIONSTRING is not in a supported PostgreSQL format"
        ) from exc

    host = values.get("host")
    database = values.get("dbname")
    username = values.get("user")
    password = values.get("password")
    port = values.get("port")
    sslmode = values.get("sslmode")

    if not all([host, database, username, password]):
        raise RuntimeError(
            "Azure PostgreSQL connection string is missing host, database, username, or password"
        )

    query = {"sslmode": sslmode} if sslmode else {}
    return URL.create(
        "postgresql+psycopg",
        username=username,
        password=password,
        host=host,
        port=int(port) if port else 5432,
        database=database,
        query=query,
    )


database_url = _normalize_database_url(settings.database_url)
is_sqlite = str(database_url).startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    if engine.dialect.name == "postgresql":
        # Serialize startup DDL across multiple Gunicorn workers.
        with engine.begin() as connection:
            connection.execute(text("SELECT pg_advisory_xact_lock(724173745)"))
            Base.metadata.create_all(bind=connection)
        return

    Base.metadata.create_all(bind=engine)
