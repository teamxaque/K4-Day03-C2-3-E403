"""
TOOL REGISTRY & SCHEMAS
Đề tài: Trợ lý tra cứu đơn hàng & xử lý đổi trả
Role 2: Tool & Spec Engineer
"""

import json
from datetime import date, timedelta
from functools import wraps
from typing import Any


# =========================================================
# MOCK DATABASE
# Khi triển khai thực tế, thay bằng truy vấn DB hoặc API.
# =========================================================

ORDER_DATABASE = {
    "DH001": {
        "customer_name": "Nguyễn Văn An",
        "customer_phone": "0901234567",
        "pickup_address": "123 Nguyễn Trãi, Thanh Xuân, Hà Nội",
        "status": "delivered",
        "created_at": str(date.today() - timedelta(days=5)),
        "delivered_at": str(date.today() - timedelta(days=3)),
        "items": [
            {
                "item_id": "SP001",
                "product_name": "Tai nghe Bluetooth",
                "category": "dien_tu",
                "quantity": 1,
                "unit_price": 550000,
            },
            {
                "item_id": "SP002",
                "product_name": "Áo sơ mi nam",
                "category": "thoi_trang",
                "quantity": 2,
                "unit_price": 350000,
            },
        ],
    },
    "DH002": {
        "customer_name": "Trần Thị Bình",
        "customer_phone": "0912345678",
        "pickup_address": "45 Lê Lợi, Quận 1, TP.HCM",
        "status": "shipping",
        "created_at": str(date.today() - timedelta(days=2)),
        "delivered_at": None,
        "items": [
            {
                "item_id": "SP003",
                "product_name": "Nồi chiên không dầu",
                "category": "gia_dung",
                "quantity": 1,
                "unit_price": 1800000,
            }
        ],
    },
}

RETURN_POLICY_DATABASE = {
    "dien_tu": {
        "return_window_days": 7,
        "allow_refund": True,
        "require_original_packaging": True,
        "description": (
            "Sản phẩm điện tử được đổi trả trong 7 ngày. "
            "Phải còn đầy đủ hộp và phụ kiện."
        ),
    },
    "thoi_trang": {
        "return_window_days": 14,
        "allow_refund": True,
        "require_original_packaging": False,
        "description": (
            "Sản phẩm thời trang được đổi trả trong 14 ngày. "
            "Sản phẩm chưa qua giặt và còn nguyên tem."
        ),
    },
    "gia_dung": {
        "return_window_days": 7,
        "allow_refund": True,
        "require_original_packaging": True,
        "description": (
            "Sản phẩm gia dụng được đổi trả trong 7 ngày. "
            "Phải còn đầy đủ phụ kiện đi kèm."
        ),
    },
}

RETURN_REQUEST_DATABASE: dict[str, dict[str, Any]] = {}
SHIPPING_LABEL_DATABASE: dict[str, dict[str, Any]] = {}

ALLOWED_REASONS = {
    "defective": "Sản phẩm bị lỗi",
    "damaged": "Sản phẩm hư hỏng khi giao",
    "wrong_item": "Giao sai sản phẩm",
    "missing_accessories": "Thiếu phụ kiện",
    "changed_mind": "Khách hàng thay đổi nhu cầu",
}

ALLOWED_ITEM_CONDITIONS = {
    "unopened": "Chưa mở hộp",
    "opened": "Đã mở hộp nhưng chưa sử dụng",
    "used": "Đã sử dụng",
}

ALLOWED_REQUEST_TYPES = {
    "refund": "Hoàn tiền",
    "exchange": "Đổi sản phẩm",
}


# =========================================================
# HELPER FUNCTIONS
# =========================================================

class ToolInputError(ValueError):
    """Lỗi đầu vào an toàn để trả về cho ReAct Agent."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field


def _response(
    success: bool,
    message: str,
    error_code: str | None = None,
    **data: Any,
) -> str:
    """Chuẩn hóa kết quả trả về dưới dạng JSON."""

    result = {
        "success": success,
        "message": message,
    }

    if error_code:
        result["error_code"] = error_code

    if data:
        result["data"] = data

    return json.dumps(result, ensure_ascii=False, indent=2)


def _safe_tool(func):
    """
    Bắt mọi lỗi tại biên của tool.

    ReAct Agent luôn nhận một chuỗi JSON làm Observation, kể cả khi:
    - Agent truyền thiếu hoặc thừa tham số.
    - Kiểu dữ liệu đầu vào không hợp lệ.
    - DB/API giả lập chứa dữ liệu lỗi.
    - Có exception ngoài dự kiến trong quá trình thực thi.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> str:
        try:
            return func(*args, **kwargs)
        except ToolInputError as exc:
            return _response(
                False,
                str(exc),
                error_code="INVALID_INPUT",
                tool=func.__name__,
                field=exc.field,
            )
        except TypeError:
            # Không trả chi tiết exception để tránh lộ thông tin nội bộ.
            return _response(
                False,
                "Tham số gọi tool bị thiếu, thừa hoặc sai kiểu dữ liệu.",
                error_code="INVALID_ARGUMENTS",
                tool=func.__name__,
            )
        except Exception:
            # Lưới an toàn cuối cùng: tool không được làm crash ReAct loop.
            return _response(
                False,
                "Tool gặp lỗi nội bộ khi xử lý dữ liệu. Vui lòng thử lại.",
                error_code="TOOL_EXECUTION_ERROR",
                tool=func.__name__,
            )

    return wrapper


def _required_text(
    value: Any,
    field: str,
    *,
    uppercase: bool = False,
    lowercase: bool = False,
) -> str:
    """Kiểm tra và chuẩn hóa một tham số chuỗi bắt buộc."""

    if not isinstance(value, str):
        raise ToolInputError(
            field,
            f"'{field}' phải là chuỗi.",
        )

    normalized = value.strip()

    if not normalized:
        raise ToolInputError(
            field,
            f"'{field}' không được để trống.",
        )

    if uppercase:
        return normalized.upper()

    if lowercase:
        return normalized.lower()

    return normalized


def _verify_order(
    order_id: str,
    customer_phone: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Tìm đơn hàng và xác thực số điện thoại khách hàng."""

    order = ORDER_DATABASE.get(order_id.upper())

    if order is None:
        return None, "Không tìm thấy đơn hàng."

    if order["customer_phone"] != customer_phone:
        return None, "Số điện thoại không khớp với đơn hàng."

    return order, None


def _find_item(
    order: dict[str, Any],
    item_id: str,
) -> dict[str, Any] | None:
    """Tìm sản phẩm trong đơn hàng."""

    for item in order["items"]:
        if item["item_id"].upper() == item_id.upper():
            return item

    return None


def _find_active_request(
    order_id: str,
    item_id: str,
) -> dict[str, Any] | None:
    """Kiểm tra sản phẩm đã có yêu cầu đổi trả hay chưa."""

    active_statuses = {
        "approved",
        "pending",
        "processing",
        "waiting_for_pickup",
    }

    for request in RETURN_REQUEST_DATABASE.values():
        if (
            request["order_id"] == order_id.upper()
            and request["item_id"] == item_id.upper()
            and request["status"] in active_statuses
        ):
            return request

    return None


def _evaluate_refund_eligibility(
    order_id: str,
    customer_phone: str,
    item_id: str,
    reason: str,
    item_condition: str,
) -> tuple[bool, str, dict[str, Any]]:
    """Thực thi các quy tắc kiểm tra điều kiện đổi trả."""

    order, error = _verify_order(order_id, customer_phone)

    if error:
        return False, error, {}

    item = _find_item(order, item_id)

    if item is None:
        return False, "Sản phẩm không thuộc đơn hàng.", {}

    policy = RETURN_POLICY_DATABASE.get(item["category"])

    if policy is None:
        return False, "Không tìm thấy chính sách cho sản phẩm.", {}

    if order["status"] != "delivered":
        return False, "Đơn hàng chưa được giao.", {}

    if not policy["allow_refund"]:
        return False, "Danh mục sản phẩm không hỗ trợ hoàn tiền.", {}

    if reason not in ALLOWED_REASONS:
        return False, "Lý do đổi trả không hợp lệ.", {}

    if item_condition not in ALLOWED_ITEM_CONDITIONS:
        return False, "Tình trạng sản phẩm không hợp lệ.", {}

    delivered_at = date.fromisoformat(order["delivered_at"])
    days_since_delivery = (date.today() - delivered_at).days

    if days_since_delivery > policy["return_window_days"]:
        return (
            False,
            f"Đã quá thời hạn {policy['return_window_days']} ngày.",
            {},
        )

    if (
        reason == "changed_mind"
        and item_condition != "unopened"
    ):
        return (
            False,
            "Sản phẩm đổi do thay đổi nhu cầu phải còn nguyên hộp.",
            {},
        )

    if (
        policy["require_original_packaging"]
        and reason == "changed_mind"
        and item_condition != "unopened"
    ):
        return False, "Sản phẩm phải còn bao bì nguyên vẹn.", {}

    existing_request = _find_active_request(order_id, item_id)

    if existing_request:
        return (
            False,
            "Sản phẩm đã có một yêu cầu đổi trả đang xử lý.",
            {"return_id": existing_request["return_id"]},
        )

    refund_amount = item["unit_price"] * item["quantity"]

    details = {
        "order": order,
        "item": item,
        "policy": policy,
        "refund_amount": refund_amount,
        "days_since_delivery": days_since_delivery,
    }

    return True, "Sản phẩm đủ điều kiện đổi trả.", details


# =========================================================
# 1. LOOKUP ORDER
# =========================================================

@_safe_tool
def lookup_order(order_id: str, customer_phone: str) -> str:
    """
    Tra cứu đơn hàng từ cơ sở dữ liệu.

    Phải gọi tool này trước khi trả lời các câu hỏi liên quan
    đến trạng thái hoặc sản phẩm trong đơn hàng.

    Args:
        order_id (str): Mã đơn hàng, ví dụ DH001.
        customer_phone (str): Số điện thoại dùng khi đặt hàng.

    Returns:
        str: Thông tin đơn hàng ở định dạng JSON.
    """

    order_id = _required_text(order_id, "order_id", uppercase=True)
    customer_phone = _required_text(customer_phone, "customer_phone")

    order, error = _verify_order(order_id, customer_phone)

    if error:
        return _response(False, error)

    safe_order = {
        "order_id": order_id.upper(),
        "customer_name": order["customer_name"],
        "status": order["status"],
        "created_at": order["created_at"],
        "delivered_at": order["delivered_at"],
        "items": order["items"],
    }

    return _response(
        True,
        "Tra cứu đơn hàng thành công.",
        order=safe_order,
    )


# =========================================================
# 2. CHECK RETURN POLICY
# =========================================================

@_safe_tool
def check_return_policy(category: str) -> str:
    """
    Kiểm tra chính sách đổi trả theo danh mục sản phẩm.

    Args:
        category (str): Danh mục sản phẩm:
            - dien_tu
            - thoi_trang
            - gia_dung

    Returns:
        str: Chính sách đổi trả ở định dạng JSON.
    """

    category = _required_text(category, "category", lowercase=True)
    policy = RETURN_POLICY_DATABASE.get(category)

    if policy is None:
        return _response(
            False,
            f"Không tìm thấy chính sách cho danh mục '{category}'.",
        )

    return _response(
        True,
        "Tra cứu chính sách thành công.",
        category=category,
        policy=policy,
    )


# =========================================================
# 3. CHECK REFUND ELIGIBILITY
# =========================================================

@_safe_tool
def check_refund_eligibility(
    order_id: str,
    customer_phone: str,
    item_id: str,
    reason: str,
    item_condition: str,
) -> str:
    """
    Kiểm tra sản phẩm có đủ điều kiện hoàn tiền/đổi trả hay không.

    Args:
        order_id (str): Mã đơn hàng.
        customer_phone (str): Số điện thoại đặt hàng.
        item_id (str): Mã sản phẩm trong đơn hàng.
        reason (str): Một trong các giá trị:
            - defective
            - damaged
            - wrong_item
            - missing_accessories
            - changed_mind
        item_condition (str): Một trong các giá trị:
            - unopened
            - opened
            - used

    Returns:
        str: Kết quả kiểm tra điều kiện ở định dạng JSON.
    """

    order_id = _required_text(order_id, "order_id", uppercase=True)
    customer_phone = _required_text(customer_phone, "customer_phone")
    item_id = _required_text(item_id, "item_id", uppercase=True)
    reason = _required_text(reason, "reason", lowercase=True)
    item_condition = _required_text(
        item_condition,
        "item_condition",
        lowercase=True,
    )

    eligible, message, details = _evaluate_refund_eligibility(
        order_id=order_id,
        customer_phone=customer_phone,
        item_id=item_id,
        reason=reason,
        item_condition=item_condition,
    )

    response_data = {
        "eligible": eligible,
        "order_id": order_id.upper(),
        "item_id": item_id.upper(),
    }

    if eligible:
        response_data.update({
            "refund_amount": details["refund_amount"],
            "return_window_days": (
                details["policy"]["return_window_days"]
            ),
            "days_since_delivery": details["days_since_delivery"],
        })

    return _response(
        eligible,
        message,
        **response_data,
    )


# =========================================================
# 4. CREATE RETURN REQUEST
# =========================================================

@_safe_tool
def create_return_request(
    order_id: str,
    customer_phone: str,
    item_id: str,
    reason: str,
    item_condition: str,
    request_type: str,
    customer_confirmed: bool,
) -> str:
    """
    Tạo yêu cầu đổi sản phẩm hoặc hoàn tiền.

    Đây là tool ghi dữ liệu. Agent chỉ được gọi sau khi khách
    hàng xác nhận thông tin yêu cầu.

    Args:
        order_id (str): Mã đơn hàng.
        customer_phone (str): Số điện thoại đặt hàng.
        item_id (str): Mã sản phẩm cần đổi trả.
        reason (str): Lý do đổi trả.
        item_condition (str): Tình trạng sản phẩm.
        request_type (str):
            - refund: Hoàn tiền
            - exchange: Đổi sản phẩm
        customer_confirmed (bool):
            True nếu khách đã xác nhận tạo yêu cầu.

    Returns:
        str: Thông tin yêu cầu đổi trả vừa tạo.
    """

    order_id = _required_text(order_id, "order_id", uppercase=True)
    customer_phone = _required_text(customer_phone, "customer_phone")
    item_id = _required_text(item_id, "item_id", uppercase=True)
    reason = _required_text(reason, "reason", lowercase=True)
    item_condition = _required_text(
        item_condition,
        "item_condition",
        lowercase=True,
    )
    request_type = _required_text(
        request_type,
        "request_type",
        lowercase=True,
    )

    if not isinstance(customer_confirmed, bool):
        raise ToolInputError(
            "customer_confirmed",
            "'customer_confirmed' phải là true hoặc false.",
        )

    if not customer_confirmed:
        return _response(
            False,
            "Khách hàng chưa xác nhận tạo yêu cầu đổi trả.",
        )

    if request_type not in ALLOWED_REQUEST_TYPES:
        return _response(
            False,
            "Loại yêu cầu phải là 'refund' hoặc 'exchange'.",
        )

    eligible, message, details = _evaluate_refund_eligibility(
        order_id=order_id,
        customer_phone=customer_phone,
        item_id=item_id,
        reason=reason,
        item_condition=item_condition,
    )

    if not eligible:
        return _response(False, message)

    return_id = f"DT{len(RETURN_REQUEST_DATABASE) + 1:03d}"

    request = {
        "return_id": return_id,
        "order_id": order_id.upper(),
        "item_id": item_id.upper(),
        "request_type": request_type,
        "reason": reason,
        "item_condition": item_condition,
        "refund_amount": (
            details["refund_amount"]
            if request_type == "refund"
            else 0
        ),
        # Prototype tự duyệt nếu đã vượt qua eligibility check.
        "status": "approved",
        "created_at": str(date.today()),
    }

    RETURN_REQUEST_DATABASE[return_id] = request

    return _response(
        True,
        "Tạo yêu cầu đổi trả thành công.",
        return_request=request,
    )


# =========================================================
# 5. GENERATE SHIPPING LABEL
# =========================================================

@_safe_tool
def generate_shipping_label(
    return_id: str,
    customer_phone: str,
) -> str:
    """
    Tạo nhãn vận chuyển cho yêu cầu đổi trả đã được duyệt.

    Khi triển khai thật, tool này sẽ gọi API đơn vị vận chuyển
    để lấy mã vận đơn và file nhãn PDF.

    Args:
        return_id (str): Mã yêu cầu đổi trả, ví dụ DT001.
        customer_phone (str): Số điện thoại đặt hàng.

    Returns:
        str: Thông tin nhãn vận chuyển ở định dạng JSON.
    """

    return_id = _required_text(return_id, "return_id", uppercase=True)
    customer_phone = _required_text(customer_phone, "customer_phone")
    request = RETURN_REQUEST_DATABASE.get(return_id)

    if request is None:
        return _response(
            False,
            "Không tìm thấy yêu cầu đổi trả.",
        )

    order, error = _verify_order(
        request["order_id"],
        customer_phone,
    )

    if error:
        return _response(False, error)

    # Đảm bảo gọi lại tool không tạo nhãn trùng.
    existing_label = SHIPPING_LABEL_DATABASE.get(return_id)

    if existing_label:
        return _response(
            True,
            "Nhãn vận chuyển đã tồn tại.",
            shipping_label=existing_label,
        )

    if request["status"] != "approved":
        return _response(
            False,
            "Yêu cầu đổi trả chưa được phê duyệt.",
        )

    tracking_number = (
        f"RTN{date.today().strftime('%Y%m%d')}"
        f"{len(SHIPPING_LABEL_DATABASE) + 1:04d}"
    )

    label = {
        "label_id": f"LBL{len(SHIPPING_LABEL_DATABASE) + 1:03d}",
        "return_id": return_id,
        "tracking_number": tracking_number,
        "carrier": "Demo Express",
        "pickup_address": order["pickup_address"],
        "return_warehouse": (
            "Kho đổi trả, 01 Đường Logistics, Hà Nội"
        ),
        "estimated_pickup_date": str(
            date.today() + timedelta(days=1)
        ),
        "instructions": (
            "Đóng gói sản phẩm và ghi mã vận đơn "
            f"{tracking_number} bên ngoài kiện hàng."
        ),
    }

    SHIPPING_LABEL_DATABASE[return_id] = label
    request["status"] = "waiting_for_pickup"

    return _response(
        True,
        "Tạo nhãn vận chuyển thành công.",
        shipping_label=label,
    )


# =========================================================
# TOOL REGISTRY
# =========================================================

AVAILABLE_TOOLS = {
    "lookup_order": lookup_order,
    "check_return_policy": check_return_policy,
    "check_refund_eligibility": check_refund_eligibility,
    "create_return_request": create_return_request,
    "generate_shipping_label": generate_shipping_label,
}


TOOL_SPECS = {
    "lookup_order": {
        "purpose": "Lấy thông tin đơn hàng từ DB.",
        "read_only": True,
        "requires_confirmation": False,
    },
    "check_return_policy": {
        "purpose": "Lấy chính sách theo danh mục từ policy DB.",
        "read_only": True,
        "requires_confirmation": False,
    },
    "check_refund_eligibility": {
        "purpose": "Kiểm tra điều kiện đổi trả và số tiền hoàn.",
        "read_only": True,
        "requires_confirmation": False,
    },
    "create_return_request": {
        "purpose": "Ghi yêu cầu đổi trả vào DB.",
        "read_only": False,
        "requires_confirmation": True,
    },
    "generate_shipping_label": {
        "purpose": "Tạo mã vận đơn trả hàng.",
        "read_only": False,
        "requires_confirmation": False,
    },
}
