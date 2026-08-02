from pydantic import BaseModel, ConfigDict


class Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BaseFrozen(Base):
    model_config = ConfigDict(frozen=True)
