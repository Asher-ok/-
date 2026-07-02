from pydantic import BaseModel, Field, field_serializer, AliasChoices
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from .customer import CustomerResponse
def _format_datetime_minute(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.replace(tzinfo=None).strftime("%Y-%m-%d %H:%M")


class InvoiceItemCreate(BaseModel):
    task_id: Optional[str] = None
    line_no: Optional[int] = None
    item_id: Optional[str] = None
    category_id: Optional[str] = None
    item_code: Optional[str] = None
    item_name: Optional[str] = None
    specification: Optional[str] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    remark: Optional[str] = None

    description: Optional[str] = None
    service_code: Optional[str] = None
    price: Optional[Decimal] = None
    quantity: Decimal = Field(default=Decimal("1"), gt=0, description="数量须大于 0")
    service_date: Optional[datetime] = None
    service_time_start: Optional[str] = None
    service_time_end: Optional[str] = None


class InvoiceItemUpdate(BaseModel):
    id: Optional[str] = None
    task_id: Optional[str] = None
    line_no: Optional[int] = None
    item_id: Optional[str] = None
    category_id: Optional[str] = None
    item_code: Optional[str] = None
    item_name: Optional[str] = None
    specification: Optional[str] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    remark: Optional[str] = None

    description: Optional[str] = None
    service_code: Optional[str] = None
    price: Optional[Decimal] = None
    quantity: Decimal = Field(default=Decimal("1"), gt=0, description="数量须大于 0")
    service_date: Optional[datetime] = None
    service_time_start: Optional[str] = None
    service_time_end: Optional[str] = None


class InvoiceItemResponse(BaseModel):
    id: str
    task_service_item_id: Optional[str] = None
    line_no: Optional[int] = None
    item_id: Optional[str] = None
    category_id: Optional[str] = None
    item_code: Optional[str] = None
    item_name: Optional[str] = None
    specification: Optional[str] = None
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = None
    amount_excl_tax: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    amount_incl_tax: Optional[Decimal] = None
    remark: Optional[str] = None

    description: Optional[str] = None
    service_code: Optional[str] = None
    price: Optional[Decimal] = None
    quantity: Decimal
    amount: Decimal
    service_date: Optional[datetime]
    service_time_start: Optional[str]
    service_time_end: Optional[str]
    
    @field_serializer("service_date")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)
    
    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    customer_id: str
    invoice_date: datetime
    items: List[InvoiceItemCreate]


class InvoiceUpdate(BaseModel):
    customer_id: Optional[str] = None
    invoice_date: Optional[datetime] = None
    items: Optional[List[InvoiceItemUpdate]] = None


class InvoiceTaskOverride(BaseModel):
    task_id: str
    price: Decimal = Field(gt=0, description="单价须大于 0")
    quantity: Decimal = Field(gt=0, description="数量须大于 0")


class InvoiceGenerateRequest(BaseModel):
    """发票生成请求：通过筛选条件选择审核通过的任务"""
    customer_id: str  # 必需：客户ID
    employee_id: Optional[str] = None  # 可选：员工ID
    date_start: Optional[datetime] = None  # 可选：日期范围开始
    date_end: Optional[datetime] = None  # 可选：日期范围结束
    task_ids: Optional[List[str]] = None  # 可选：任务ID列表（如果提供，则只使用这些任务）
    task_overrides: Optional[List[InvoiceTaskOverride]] = None  # 可选：任务价格/数量覆盖
    invoice_date: Optional[datetime] = None  # 如果不提供，使用当前日期
    is_paid: Optional[bool] = False  # 生成时是否标记为已付款


class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    customer_id: str
    invoice_date: datetime
    total_amount: Decimal
    total_excl_tax: Optional[Decimal] = None
    total_tax: Optional[Decimal] = None
    total_incl_tax: Optional[Decimal] = None
    status: str
    sent_at: Optional[datetime]
    paid_at: Optional[datetime] = None
    voided_at: Optional[datetime] = None
    void_reason: Optional[str] = None
    email: Optional[str]
    pdf_url: Optional[str]
    currency: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_phone: Optional[str] = None
    buyer_email: Optional[str] = None
    buyer_address: Optional[str] = None
    items: List[InvoiceItemResponse] = []
    customer: Optional[CustomerResponse] = None
    created_at: datetime
    
    @field_serializer("invoice_date", "sent_at", "paid_at", "voided_at", "created_at")
    def serialize_datetimes(self, value):
        return _format_datetime_minute(value)
    
    class Config:
        from_attributes = True


class InvoiceItemCategoryResponse(BaseModel):
    id: str
    parent_id: Optional[str] = None
    name: str
    code: Optional[str] = None
    level: int
    path: str
    sort_order: int
    is_active: bool

    class Config:
        from_attributes = True


class InvoiceItemDictResponse(BaseModel):
    id: str
    category_id: str
    item_code: str
    item_name: str
    spec_default: Optional[str] = None
    unit_default: Optional[str] = None
    price_default: Optional[Decimal] = None
    tax_rate_default: Decimal
    is_active: bool

    class Config:
        from_attributes = True


class InvoiceItemDictCreate(BaseModel):
    category_id: str
    item_code: str
    item_name: str
    spec_default: Optional[str] = None
    unit_default: Optional[str] = None
    price_default: Optional[Decimal] = None
    tax_rate_default: Optional[Decimal] = None
    reference_code: Optional[str] = None


class InvoiceServiceLevel1Response(BaseModel):
    id: str
    name: str
    sort_order: int
    is_active: bool

    class Config:
        from_attributes = True


class InvoiceServiceLevel1Create(BaseModel):
    name: str
    sort_order: int = 0
    is_active: bool = True


class InvoiceServiceLevel1Update(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class InvoiceServiceLevel2Response(BaseModel):
    id: str
    level1_id: str
    name: str
    sort_order: int
    is_active: bool

    class Config:
        from_attributes = True


class InvoiceServiceLevel2Create(BaseModel):
    level1_id: str
    name: str
    sort_order: int = 0
    is_active: bool = True


class InvoiceServiceLevel2Update(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class InvoiceServiceLevel3Response(BaseModel):
    id: str
    level1_id: str
    level2_id: Optional[str] = None
    name: str
    sort_order: int
    is_active: bool

    class Config:
        from_attributes = True


class InvoiceServiceLevel3Create(BaseModel):
    level1_id: str
    level2_id: Optional[str] = None
    name: str
    sort_order: int = 0
    is_active: bool = True


class InvoiceServiceLevel3Update(BaseModel):
    level2_id: Optional[str] = None
    name: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class InvoiceServiceCodeResponse(BaseModel):
    id: str
    level3_id: str
    code: str
    price: Optional[Decimal] = None
    unit: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class InvoiceServiceCodeCreate(BaseModel):
    level3_id: str
    code: str
    price: Optional[Decimal] = Field(default=None, validation_alias=AliasChoices("price", "unit_price", "unitPrice"))
    unit: Optional[str] = None
    is_active: bool = True


class InvoiceServiceCodeUpdate(BaseModel):
    level3_id: Optional[str] = None
    code: Optional[str] = None
    price: Optional[Decimal] = Field(default=None, validation_alias=AliasChoices("price", "unit_price", "unitPrice"))
    unit: Optional[str] = None
    is_active: Optional[bool] = None


class BatchSendUnsentInvoicesRequest(BaseModel):
    customer_id: Optional[str] = None
    language: Optional[str] = None


class BatchSendInvoiceResult(BaseModel):
    invoice_id: str
    invoice_number: Optional[str] = None
    customer_id: Optional[str] = None
    email: Optional[str] = None
    status: str
    reason: Optional[str] = None


class BatchSendUnsentInvoicesResponse(BaseModel):
    total: int
    sent: int
    skipped: int
    failed: int
    results: List[BatchSendInvoiceResult]


class BatchGenerateUninvoicedInvoicesRequest(BaseModel):
    customer_id: Optional[str] = None
    employee_id: Optional[str] = None
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    invoice_date: Optional[datetime] = None


class BatchGenerateInvoiceResult(BaseModel):
    customer_id: Optional[str] = None
    invoice_id: Optional[str] = None
    invoice_number: Optional[str] = None
    task_count: int = 0
    total_amount: Optional[Decimal] = None
    status: str
    reason: Optional[str] = None


class BatchGenerateUninvoicedInvoicesResponse(BaseModel):
    customers: int
    created: int
    skipped: int
    failed: int
    results: List[BatchGenerateInvoiceResult]


class UninvoicedTaskLine(BaseModel):
    description: Optional[str] = None
    code: Optional[str] = None
    unit: Optional[str] = None
    unit_price: Optional[str] = None
    quantity: Optional[str] = None
    amount: Optional[str] = None
    service_date: Optional[str] = None
    service_time_start: Optional[str] = None
    service_time_end: Optional[str] = None


class UninvoicedTaskInfo(BaseModel):
    id: str
    title: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    service_start_time: Optional[str] = None
    service_end_time: Optional[str] = None
    service_lines: List[UninvoicedTaskLine] = []
    subtotal: Optional[Decimal] = None


class BatchListUninvoicedTasksResponse(BaseModel):
    count: int
    tasks: List[UninvoicedTaskInfo]


class BatchGenerateByTaskResult(BaseModel):
    task_id: str
    customer_id: Optional[str] = None
    invoice_id: Optional[str] = None
    invoice_number: Optional[str] = None
    total_amount: Optional[Decimal] = None
    status: str
    reason: Optional[str] = None


class BatchGenerateByTaskResponse(BaseModel):
    total_tasks: int
    created: int
    skipped: int
    failed: int
    results: List[BatchGenerateByTaskResult]
