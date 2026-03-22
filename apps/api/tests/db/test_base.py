"""Tests for db/base.py — Base declarative and TimestampMixin."""
import datetime

import pytest
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import Session


def test_base_is_declarative_base():
    from strata_api.db.base import Base

    assert hasattr(Base, "metadata")
    assert hasattr(Base, "__tablename__") is False  # Base itself has no table


def test_timestamp_mixin_has_created_at_and_updated_at():
    from strata_api.db.base import Base, TimestampMixin

    class SampleModel(TimestampMixin, Base):
        __tablename__ = "sample_model_test"
        id = Column(Integer, primary_key=True)
        name = Column(String)

    assert hasattr(SampleModel, "created_at")
    assert hasattr(SampleModel, "updated_at")


def test_timestamp_mixin_columns_are_datetime():
    """Verify TimestampMixin column types via a concrete mapped model."""
    from sqlalchemy import DateTime, inspect

    from strata_api.db.base import Base, TimestampMixin
    from sqlalchemy import Column, Integer, create_engine

    class TypeCheckModel(TimestampMixin, Base):
        __tablename__ = "type_check_model_test"
        id = Column(Integer, primary_key=True)

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    mapper = inspect(TypeCheckModel)
    created_col = mapper.columns["created_at"]
    updated_col = mapper.columns["updated_at"]
    assert isinstance(created_col.type, DateTime)
    assert isinstance(updated_col.type, DateTime)
    Base.metadata.drop_all(engine)


def test_timestamp_mixin_created_at_defaults_on_insert():
    from strata_api.db.base import Base, TimestampMixin

    class AnotherModel(TimestampMixin, Base):
        __tablename__ = "another_model_test"
        id = Column(Integer, primary_key=True)

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        obj = AnotherModel(id=1)
        session.add(obj)
        session.commit()
        session.refresh(obj)
        assert obj.created_at is not None
        assert isinstance(obj.created_at, datetime.datetime)

    Base.metadata.drop_all(engine)


def test_timestamp_mixin_updated_at_defaults_on_insert():
    from strata_api.db.base import Base, TimestampMixin

    class YetAnotherModel(TimestampMixin, Base):
        __tablename__ = "yet_another_model_test"
        id = Column(Integer, primary_key=True)

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        obj = YetAnotherModel(id=1)
        session.add(obj)
        session.commit()
        session.refresh(obj)
        assert obj.updated_at is not None

    Base.metadata.drop_all(engine)
