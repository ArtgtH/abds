from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UserPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fio: str | None = Field(default=None, min_length=1)
    phone: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def require_change(self) -> "UserPatch":
        if self.fio is None and self.phone is None:
            raise ValueError("at least one field is required")
        return self


class ReadingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int = Field(ge=1, strict=True)
    tariff_id: int = Field(ge=1, strict=True)
    gauge_id: int = Field(ge=1, strict=True)
    reading_date: date
    day_kw: int = Field(ge=0, le=2**32 - 1, strict=True)
    night_kw: int = Field(ge=0, le=2**32 - 1, strict=True)


class GaugeInstall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gauge_id: int = Field(ge=1, strict=True)
