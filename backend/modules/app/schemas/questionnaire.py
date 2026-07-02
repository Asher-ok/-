from pydantic import BaseModel, field_serializer, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


def _format_datetime_minute(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.replace(tzinfo=None).strftime("%Y-%m-%d %H:%M")


def _clean_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_i18n_text(value: Any) -> Optional[Dict[str, Optional[str]]]:
    if value is None:
        return None
    if isinstance(value, str):
        text = _clean_text(value)
        return {"zh": text, "en": None} if text else None
    if not isinstance(value, dict):
        return None
    zh = _clean_text(value.get("zh") or value.get("zh-CN") or value.get("cn"))
    en = _clean_text(value.get("en") or value.get("en-US"))
    if not zh and not en:
        return None
    return {"zh": zh, "en": en}


def _pick_primary_text(i18n_value: Any, fallback: Any = None) -> str:
    normalized = _normalize_i18n_text(i18n_value)
    if normalized:
        return normalized.get("zh") or normalized.get("en") or (_clean_text(fallback) or "")
    return _clean_text(fallback) or ""


def _normalize_options(value: Any) -> Any:
    if value is None or not isinstance(value, list):
        return value
    normalized = []
    for index, item in enumerate(value):
        if item is None:
            continue
        if isinstance(item, (str, int, float)):
            text = _clean_text(item)
            if not text:
                continue
            normalized.append({
                "label": text,
                "value": text,
                "text": text,
                "order_index": index + 1
            })
            continue
        if not isinstance(item, dict):
            continue

        text_i18n = _normalize_i18n_text(
            item.get("text_i18n")
            or {
                "zh": item.get("text_zh") or item.get("label_zh"),
                "en": item.get("text_en") or item.get("label_en")
            }
        )
        text = _pick_primary_text(
            text_i18n,
            item.get("text") or item.get("label") or item.get("name") or item.get("title") or item.get("value")
        )
        if not text:
            continue

        option = {
            "label": _clean_text(item.get("label")) or text,
            "value": _clean_text(item.get("value")) or _clean_text(item.get("label")) or text,
            "text": _clean_text(item.get("text")) or text
        }
        if item.get("id") is not None:
            option["id"] = item.get("id")
        if item.get("order_index") is not None and str(item.get("order_index")).strip() != "":
            option["order_index"] = item.get("order_index")
        if text_i18n:
            option["text_i18n"] = text_i18n
        normalized.append(option)
    return normalized


class QuestionCreate(BaseModel):
    title: str
    title_i18n: Optional[Dict[str, Optional[str]]] = None
    type: str  # single_choice, multiple_choice, text, number, date
    required: bool = False
    options: Optional[List[Dict[str, Any]]] = None
    placeholder: Optional[str] = None
    hint: Optional[str] = None
    order_index: int = 0

    @field_validator("options", mode="before")
    @classmethod
    def normalize_options(cls, v):
        return _normalize_options(v)

    @field_validator("title_i18n", mode="before")
    @classmethod
    def normalize_title_i18n(cls, v):
        return _normalize_i18n_text(v)

    @model_validator(mode="after")
    def fill_title_from_i18n(self):
        self.title = _pick_primary_text(self.title_i18n, self.title)
        return self


class QuestionUpdate(BaseModel):
    title: Optional[str] = None
    title_i18n: Optional[Dict[str, Optional[str]]] = None
    type: Optional[str] = None
    required: Optional[bool] = None
    options: Optional[List[Dict[str, Any]]] = None
    placeholder: Optional[str] = None
    hint: Optional[str] = None
    order_index: Optional[int] = None

    @field_validator("options", mode="before")
    @classmethod
    def normalize_options(cls, v):
        return _normalize_options(v)

    @field_validator("title_i18n", mode="before")
    @classmethod
    def normalize_title_i18n(cls, v):
        return _normalize_i18n_text(v)


class QuestionResponse(BaseModel):
    id: str
    title: str
    title_i18n: Optional[Dict[str, Optional[str]]] = None
    type: str
    required: bool
    conditional_required: Optional[bool] = False
    depends_on: Optional[str] = None
    options: Optional[List[Dict[str, Any]]]
    placeholder: Optional[str]
    hint: Optional[str]
    order_index: int

    @field_serializer("title_i18n")
    def serialize_title_i18n(self, value):
        return _normalize_i18n_text(value)

    @field_serializer("options")
    def serialize_options(self, value):
        return _normalize_options(value)
    
    class Config:
        from_attributes = True


class QuestionnaireCreate(BaseModel):
    title: str
    title_i18n: Optional[Dict[str, Optional[str]]] = None
    description: Optional[str] = None
    description_i18n: Optional[Dict[str, Optional[str]]] = None
    is_active: bool = True
    questions: Optional[List[QuestionCreate]] = []

    @field_validator("title_i18n", mode="before")
    @classmethod
    def normalize_title_i18n(cls, v):
        return _normalize_i18n_text(v)

    @field_validator("description_i18n", mode="before")
    @classmethod
    def normalize_description_i18n(cls, v):
        return _normalize_i18n_text(v)

    @model_validator(mode="after")
    def fill_title_description_from_i18n(self):
        self.title = _pick_primary_text(self.title_i18n, self.title)
        self.description = _pick_primary_text(self.description_i18n, self.description)
        return self


class QuestionnaireUpdate(BaseModel):
    title: Optional[str] = None
    title_i18n: Optional[Dict[str, Optional[str]]] = None
    description: Optional[str] = None
    description_i18n: Optional[Dict[str, Optional[str]]] = None
    is_active: Optional[bool] = None

    @field_validator("title_i18n", mode="before")
    @classmethod
    def normalize_title_i18n(cls, v):
        return _normalize_i18n_text(v)

    @field_validator("description_i18n", mode="before")
    @classmethod
    def normalize_description_i18n(cls, v):
        return _normalize_i18n_text(v)

    @model_validator(mode="after")
    def fill_title_description_from_i18n(self):
        if self.title is None or not str(self.title).strip():
            self.title = _pick_primary_text(self.title_i18n, self.title)
        if self.description is None or not str(self.description).strip():
            self.description = _pick_primary_text(self.description_i18n, self.description)
        return self


class QuestionnaireResponse(BaseModel):
    id: str
    title: str
    title_i18n: Optional[Dict[str, Optional[str]]] = None
    description: Optional[str]
    description_i18n: Optional[Dict[str, Optional[str]]] = None
    is_active: bool
    questions: List[QuestionResponse] = []

    @field_serializer("title_i18n")
    def serialize_title_i18n(self, value):
        return _normalize_i18n_text(value)

    @field_serializer("description_i18n")
    def serialize_description_i18n(self, value):
        return _normalize_i18n_text(value)
    
    class Config:
        from_attributes = True


class QuestionnaireSubmissionCreate(BaseModel):
    task_id: str
    customer_id: str
    answers: Dict[str, Any]


class QuestionnaireSubmissionResponse(BaseModel):
    id: str
    questionnaire_id: str
    task_id: str
    customer_id: str
    employee_id: str
    answers: Dict[str, Any]
    submitted_at: datetime
    
    @field_serializer("submitted_at")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)

    class Config:
        from_attributes = True
