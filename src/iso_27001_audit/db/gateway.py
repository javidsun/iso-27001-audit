from contextlib import contextmanager
from typing import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from iso_27001_audit.models.model import Model


class SqlAlchemyDatabaseGateway:
    def __init__(self, database_url: str, echo: bool = False) -> None:
        self._database_url = database_url
        self._echo = echo
        self._engine: Engine = create_engine(
            self._database_url,
            echo=self._echo,
            future=True,
            pool_pre_ping=True,
        )
        self._session_factory = sessionmaker(
            bind=self._engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            class_=Session,
        )

    @property
    def engine(self) -> Engine:
        return self._engine

    def create_schema(self) -> None:
        Model.metadata.create_all(bind=self._engine)

    def drop_schema(self) -> None:
        Model.metadata.drop_all(bind=self._engine)

    def dispose(self) -> None:
        self._engine.dispose()

    def get_session(self) -> Session:
        return self._session_factory()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()