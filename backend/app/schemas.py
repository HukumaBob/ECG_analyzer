"""
Pydantic-схемы входных/выходных данных API.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Вспомогательные типы
# ---------------------------------------------------------------------------


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    NORMAL = "normal"
    TECHNICAL = "technical"


class DiagnosisItem(BaseModel):
    label: str = Field(..., description="Машинный идентификатор класса")
    label_ru: str = Field(..., description="Название на русском")
    probability: float = Field(..., ge=0.0, le=1.0, description="Вероятность [0..1]")
    triggered: bool = Field(..., description="Превышен ли порог срабатывания")
    priority: Priority


# ---------------------------------------------------------------------------
# Клинические метаданные
# ---------------------------------------------------------------------------


class PatientMetadataRequest(BaseModel):
    """
    Клинические метаданные пациента для байесовской поправки.
    Все поля опциональны — без них анализ выполняется только по ЭКГ.
    """

    age: Optional[int] = Field(None, ge=0, le=120, description="Возраст, лет")
    sex: Optional[str] = Field(None, description="Пол: M (мужской) или F (женский)")
    heart_rate: Optional[int] = Field(None, ge=10, le=300, description="ЧСС из анамнеза, уд/мин")
    medications: list[str] = Field(default_factory=list, description="Список препаратов")
    icd10_codes: list[str] = Field(default_factory=list, description="Активные МКБ-10 диагнозы")
    potassium: Optional[float] = Field(None, ge=1.0, le=10.0, description="K+, ммоль/л")
    magnesium: Optional[float] = Field(None, ge=0.1, le=5.0, description="Mg²+, ммоль/л")
    has_pacemaker: Optional[bool] = Field(None, description="Установленный кардиостимулятор")

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.upper() not in ("M", "F"):
            raise ValueError("sex должен быть 'M' или 'F'")
        return v.upper() if v else v


# ---------------------------------------------------------------------------
# Входные данные
# ---------------------------------------------------------------------------


class AnalyzeRequest(BaseModel):
    """
    Мета-параметры, которые можно передать вместе с файлом ЭКГ.
    Сам файл передаётся как multipart/form-data.
    """

    patient_id: Optional[str] = Field(None, description="ID пациента (опционально, только для логирования)")
    notes: Optional[str] = Field(None, max_length=500, description="Примечания врача")
    metadata: Optional[PatientMetadataRequest] = Field(None, description="Клинические метаданные для байесовской поправки")


# ---------------------------------------------------------------------------
# Выходные данные
# ---------------------------------------------------------------------------


class EcgPreview(BaseModel):
    """Данные ЭКГ для отображения графика."""

    leads: list[list[float]] = Field(..., description="12 отведений, каждое — список отсчётов")
    sample_rate: int = Field(..., description="Частота дискретизации превью (после downsample)")
    duration_sec: float = Field(..., description="Длительность показанного фрагмента, сек")
    lead_names: list[str] = Field(
        default=["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"],
        description="Названия отведений",
    )


class AnalyzeResponse(BaseModel):
    """Результат анализа ЭКГ."""

    request_id: str = Field(..., description="UUID запроса для трассировки")
    has_critical: bool = Field(..., description="True если сработал хотя бы один критический класс")
    diagnoses: list[DiagnosisItem] = Field(..., description="Список всех 17 классов с вероятностями")
    conclusion: str = Field(..., description="Текстовое заключение на русском языке")
    segments_analyzed: int = Field(..., description="Количество 5-секундных сегментов ЭКГ")
    device_used: str = Field(..., description="cuda или cpu")
    warning: Optional[str] = Field(None, description="Предупреждение (напр. низкое качество сигнала)")
    ecg_preview: Optional[EcgPreview] = Field(None, description="Данные ЭКГ для графика (первые 10 сек, downsampled)")


class HealthResponse(BaseModel):
    """Статус сервиса."""

    status: str = Field(..., description="ok | degraded")
    model_loaded: bool
    device: Optional[str] = Field(None, description="cuda или cpu")
    version: str = "0.1.0"
