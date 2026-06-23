import json
from dataclasses import dataclass

from services.action_confirmation_service import ActionConfirmationService
from services.backend_api_service import BackendAPIService
from services.domain_tool_handlers import BookingToolHandler, NotificationToolHandler, PaymentToolHandler
from services.tool_access_policy import ToolAccessPolicy


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    properties: dict
    handler: object
    required: tuple[str, ...] = ()
    mode: str = "read"
    allowed_roles: tuple[str, ...] | None = None


class ToolService:
    LOGIN_REQUIRED_ROLES = ("USER", "MERCHANT", "ADMIN")
    STAFF_ROLES = ("MERCHANT", "ADMIN")
    ADMIN_ROLES = ("ADMIN",)

    def __init__(
        self,
        config,
        search_tool=None,
        weather_tool=None,
        time_tool=None,
        geocode_tool=None,
        action_confirmation_service=None,
    ):
        self.backend_api_service = BackendAPIService(config)
        self.access_policy = ToolAccessPolicy(self.backend_api_service)
        self.booking_handler = BookingToolHandler(self.backend_api_service, self.access_policy)
        self.payment_handler = PaymentToolHandler(self.backend_api_service, self.access_policy)
        self.notification_handler = NotificationToolHandler(self.backend_api_service, self.access_policy)
        self.action_confirmation_service = action_confirmation_service or ActionConfirmationService(
            ttl_seconds=config.action_confirmation_ttl_seconds()
        )
        self.search_tool = search_tool
        self.weather_tool = weather_tool
        self.time_tool = time_tool
        self.geocode_tool = geocode_tool
        self._tool_registry = {}
        self._register_tools()

    def get_tool_definitions(self, allowed_tool_names=None, user_context=None):
        allowed_names = set(allowed_tool_names) if allowed_tool_names else None
        definitions = []
        for spec in self._tool_registry.values():
            if allowed_names is not None and spec.name not in allowed_names:
                continue
            if not self._is_role_allowed(spec, user_context):
                continue
            definitions.append(self._build_definition(spec))
        return definitions

    def get_allowed_tool_names(self, user_context=None, mode=None):
        names = []
        for spec in self._tool_registry.values():
            if mode and spec.mode != mode:
                continue
            if self._is_role_allowed(spec, user_context):
                names.append(spec.name)
        return tuple(names)

    def handle_tool_call(self, tool_call, user_context=None):
        function_call = tool_call.get("function", {})
        name = function_call.get("name")
        arguments = function_call.get("arguments") or "{}"

        try:
            parsed_arguments = self._parse_arguments(arguments)
            result = self._dispatch(name, parsed_arguments, user_context=user_context)
            return {
                "ok": True,
                "tool": name,
                "result": result,
            }
        except Exception as exc:
            return {
                "ok": False,
                "tool": name,
                "error": str(exc),
            }

    def execute(self, name, tool_input, user_context=None):
        try:
            result = self._dispatch(name, tool_input or {}, user_context=user_context)
            return {
                "ok": True,
                "tool": name,
                "result": result,
            }
        except Exception as exc:
            return {
                "ok": False,
                "tool": name,
                "error": str(exc),
            }

    def _register_tools(self):
        self._register_general_tools()
        self._register_property_tools()
        self._register_room_type_tools()
        self._register_booking_tools()
        self._register_payment_tools()
        self._register_review_tools()
        self._register_notification_tools()
        self._register_merchant_tools()
        self._register_user_tools()
        self._register_coupon_tools()

    def _register_general_tools(self):
        if self.search_tool is not None:
            self._register_tool(
                self.search_tool.name,
                self.search_tool.description,
                self.search_tool.input_schema.get("properties", {}),
                lambda user_context=None, **kwargs: self.search_tool.execute(kwargs),
                required=self.search_tool.input_schema.get("required", ()),
            )
        if self.weather_tool is not None:
            self._register_tool(
                self.weather_tool.name,
                self.weather_tool.description,
                self.weather_tool.input_schema.get("properties", {}),
                lambda user_context=None, **kwargs: self.weather_tool.execute(kwargs),
                required=self.weather_tool.input_schema.get("required", ()),
            )
        if self.time_tool is not None:
            self._register_tool(
                self.time_tool.name,
                self.time_tool.description,
                self.time_tool.input_schema.get("properties", {}),
                lambda user_context=None, **kwargs: self.time_tool.execute(kwargs),
                required=self.time_tool.input_schema.get("required", ()),
            )
        if self.geocode_tool is not None:
            self._register_tool(
                self.geocode_tool.name,
                self.geocode_tool.description,
                self.geocode_tool.input_schema.get("properties", {}),
                lambda user_context=None, **kwargs: self.geocode_tool.execute(kwargs),
                required=self.geocode_tool.input_schema.get("required", ()),
            )

    def _register_tool(
        self,
        name,
        description,
        properties,
        handler,
        required=None,
        mode="read",
        allowed_roles=None,
    ):
        self._tool_registry[name] = ToolSpec(
            name=name,
            description=description,
            properties=properties,
            handler=handler,
            required=tuple(required or ()),
            mode=mode,
            allowed_roles=tuple(allowed_roles) if allowed_roles else None,
        )

    def _build_definition(self, spec):
        properties = dict(spec.properties)
        if spec.mode == "action":
            properties["confirmation_token"] = {
                "type": "string",
                "description": "执行写操作前由系统返回的确认令牌。首次请求动作时不要填写。",
            }

        return {
            "name": spec.name,
            "description": self._build_description(spec),
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": [] if spec.mode == "action" else list(spec.required),
            },
        }

    def _build_description(self, spec):
        if spec.mode != "action":
            return spec.description
        return (
            f"{spec.description} 这是写操作：首次调用只会创建待确认动作，不会执行；"
            "只有用户明确确认并提供 confirmation_token 后才会执行。"
        )

    def _public(self, handler):
        return lambda user_context=None, **kwargs: handler(**kwargs)

    def _dispatch(self, name, arguments, user_context=None):
        spec = self._tool_registry.get(name)
        if not spec:
            raise ValueError(f"未知工具：{name}")
        if not self._is_role_allowed(spec, user_context):
            raise ValueError(f"当前角色无权调用工具：{name}")
        clean_arguments = dict(arguments or {})
        confirmation_token = clean_arguments.pop("confirmation_token", None)

        if spec.mode == "action":
            if not confirmation_token:
                self._validate_required_arguments(spec, clean_arguments)
                pending_summary = self._build_pending_action_summary(
                    name,
                    clean_arguments,
                    user_context=user_context,
                )
                pending_action = self.action_confirmation_service.create(
                    name,
                    clean_arguments,
                    user_context=user_context,
                    summary=pending_summary,
                )
                return {
                    "status": "pending_confirmation",
                    "message": pending_summary.get("message") or "该操作会修改后端状态，请确认后再执行。",
                    "pending_action": pending_action.to_response(),
                }

            pending_action = self.action_confirmation_service.consume(
                confirmation_token,
                name,
                clean_arguments,
                user_context=user_context,
            )
            clean_arguments = dict(pending_action.arguments)

        return spec.handler(user_context=user_context, **clean_arguments)

    def _validate_required_arguments(self, spec, arguments):
        missing = [
            name
            for name in spec.required
            if arguments.get(name) is None or arguments.get(name) == ""
        ]
        if missing:
            raise ValueError(f"缺少必填参数：{', '.join(missing)}")

    def _parse_arguments(self, arguments):
        if isinstance(arguments, dict):
            return arguments
        if not isinstance(arguments, str):
            return {}
        try:
            return json.loads(arguments)
        except json.JSONDecodeError:
            return {}

    def _build_pending_action_summary(self, tool_name, arguments, user_context=None):
        builder = getattr(self, f"_pending_summary_{tool_name}", None)
        if callable(builder):
            return builder(arguments, user_context=user_context)
        return {
            "action": tool_name,
            "message": "该操作会修改后端状态，请确认后再执行。",
            "confirmation_text": f"确认执行动作 {tool_name}",
        }

    def _resolve_role(self, user_context):
        return self.access_policy.resolve_role(user_context)

    def _is_role_allowed(self, spec, user_context):
        return self.access_policy.is_role_allowed(spec, user_context)

    def _current_user_id(self, user_context):
        return self.access_policy.current_user_id(user_context)

    def _current_merchant_id(self, user_context):
        return self.access_policy.current_merchant_id(user_context)

    def _to_int(self, value):
        return self.access_policy.to_int(value)

    @staticmethod
    def _stringify(value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()

    def _get_path(self, payload, *path):
        return self.access_policy.get_path(payload, *path)

    def _unwrap_item(self, result):
        return self.access_policy.unwrap_item(result)

    def _unwrap_items(self, result):
        return self.access_policy.unwrap_items(result)

    def _set_items(self, result, items):
        return self.access_policy.set_items(result, items)

    def _filter_items(self, result, predicate):
        return self.access_policy.filter_items(result, predicate)

    def _booking_user_id(self, item):
        return self.access_policy.booking_user_id(item)

    def _booking_merchant_id(self, item):
        return self.access_policy.booking_merchant_id(item)

    def _payment_user_id(self, item):
        return self.access_policy.payment_user_id(item)

    def _payment_merchant_id(self, item):
        return self.access_policy.payment_merchant_id(item)

    def _review_user_id(self, item):
        return self.access_policy.review_user_id(item)

    def _review_merchant_id(self, item):
        return self.access_policy.review_merchant_id(item)

    def _notification_user_id(self, item):
        return self.access_policy.notification_user_id(item)

    def _merchant_owner_user_id(self, item):
        return self.access_policy.merchant_owner_user_id(item)

    def _coupon_merchant_id(self, item):
        return self.access_policy.coupon_merchant_id(item)

    def _can_access_booking(self, item, user_context):
        return self.access_policy.can_access_booking(item, user_context)

    def _can_access_payment(self, item, user_context):
        return self.access_policy.can_access_payment(item, user_context)

    def _can_access_review_action(self, item, user_context):
        return self.access_policy.can_access_review_action(item, user_context)

    def _can_access_review_by_booking(self, item, user_context):
        return self.access_policy.can_access_review_by_booking(item, user_context)

    def _can_access_notification(self, item, user_context):
        return self.access_policy.can_access_notification(item, user_context)

    def _assert_access(self, allowed, message):
        self.access_policy.assert_access(allowed, message)

    def _ensure_property_owned_by_current_merchant(self, property_id, user_context):
        self.access_policy.ensure_property_owned_by_current_merchant(property_id, user_context)

    def _load_booking_detail(self, booking_id):
        return self.backend_api_service.get_booking_detail(booking_id)

    def _load_booking_by_number(self, booking_number):
        return self.backend_api_service.get_booking_by_number(booking_number)

    def _load_payment_detail(self, payment_id):
        return self.backend_api_service.get_payment_detail(payment_id)

    def _load_payment_by_number(self, payment_number):
        return self.backend_api_service.get_payment_by_number(payment_number)

    def _load_review_detail(self, review_id):
        return self.backend_api_service.get_review_detail(review_id)

    def _ensure_notification_owned(self, notification_id, user_context):
        self.access_policy.ensure_notification_owned(notification_id, user_context)

    def _list_current_merchant_property_ids(self, user_context):
        return self.access_policy.list_current_merchant_property_ids(user_context)

    def _register_property_tools(self):
        self._register_tool(
            "list_properties",
            "按商家ID、城市（精确匹配）、状态、精选标记筛选房源列表。"
            "注意：城市参数为精确匹配（'上海'≠'上海市'，可能查不到）。"
            "用户按城市/区域搜索时，请改用 search_properties 的 keyword 参数（模糊匹配）。",
            {
                "merchant_id": {"type": "integer", "description": "商家 ID，可选。"},
                "city": {"type": "string", "description": "城市名精确匹配（'上海'和'上海市'不同），可选。用户位置查询请改用 search_properties 工具。"},
                "status": {"type": "string", "description": "房源状态，可选。"},
                "featured": {"type": "boolean", "description": "是否只查精选房源，可选。"},
            },
            self._public(self.backend_api_service.list_properties),
        )
        self._register_tool(
            "search_properties",
            "智能搜索房源（推荐首选）。keyword 参数支持模糊匹配，适合处理城市、区域、地标、店名、设施等自然语言查询。"
            "城市和区域名称应通过 keyword 传入（如 keyword='上海浦东'），而非 city/district 精确参数。",
            {
                "keyword": {"type": "string", "description": "搜索关键词，支持模糊匹配。城市名、区县名、地标、店名、设施、特色（如'海景''亲子''地铁口'）都应通过此参数传入。例如：用户说'上海浦东的房源'→ keyword='上海浦东'。"},
                "city": {"type": "string", "description": "城市名精确筛选（'上海'和'上海市'不同，可能查不到），可选。用户位置查询应优先使用 keyword 参数。"},
                "district": {"type": "string", "description": "区县名精确筛选（'浦东'和'浦东新区'不同，可能查不到），可选。用户位置查询应优先使用 keyword 参数。"},
                "min_price": {"type": "number", "description": "最低价格，可选。"},
                "max_price": {"type": "number", "description": "最高价格，可选。"},
                "min_rating": {"type": "number", "description": "最低评分，可选。"},
                "featured": {"type": "boolean", "description": "是否只看精选房源，可选。"},
                "facilities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "设施列表，可选。",
                },
                "latitude": {"type": "number", "description": "纬度，可选。"},
                "longitude": {"type": "number", "description": "经度，可选。"},
                "distance_km": {"type": "number", "description": "距离半径（公里），可选。"},
                "page": {"type": "integer", "description": "页码，默认 1。"},
                "size": {"type": "integer", "description": "每页条数，默认 10。"},
            },
            self._public(self.backend_api_service.search_properties),
        )
        self._register_tool(
            "get_property_detail",
            "查询房源详情和房型信息。",
            {
                "property_id": {"type": "integer", "description": "房源 ID。"},
            },
            self._public(self.backend_api_service.get_property_detail),
            required=["property_id"],
        )
        self._register_tool(
            "get_top_properties",
            "查询热门房源排行榜。",
            {
                "limit": {"type": "integer", "description": "返回条数，默认 5。"},
            },
            self._public(self.backend_api_service.get_top_properties),
        )

    def _register_room_type_tools(self):
        self._register_tool(
            "list_room_types",
            "查询房型列表，可按房源 ID 过滤。",
            {
                "property_id": {"type": "integer", "description": "房源 ID，可选。"},
            },
            self._public(self.backend_api_service.list_room_types),
        )
        self._register_tool(
            "get_room_type_detail",
            "查询单个房型详情。",
            {
                "room_type_id": {"type": "integer", "description": "房型 ID。"},
            },
            self._public(self.backend_api_service.get_room_type_detail),
            required=["room_type_id"],
        )
        self._register_tool(
            "get_active_room_types",
            "查询某个房源当前可用的房型。",
            {
                "property_id": {"type": "integer", "description": "房源 ID。"},
            },
            self._public(self.backend_api_service.get_active_room_types),
            required=["property_id"],
        )

    def _register_booking_tools(self):
        self._register_tool(
            "list_bookings",
            "查询订单列表，支持按用户、房源、商家和状态筛选。",
            {
                "user_id": {"type": "integer", "description": "用户 ID，可选。"},
                "property_id": {"type": "integer", "description": "房源 ID，可选。"},
                "merchant_id": {"type": "integer", "description": "商家 ID，可选。"},
                "status": {"type": "string", "description": "订单状态，可选。"},
            },
            self._handle_list_bookings,
            allowed_roles=self.LOGIN_REQUIRED_ROLES,
        )
        self._register_tool(
            "get_booking_detail",
            "按订单 ID 查询订单详情。",
            {
                "booking_id": {"type": "integer", "description": "订单 ID。"},
            },
            self._handle_get_booking_detail,
            required=["booking_id"],
            allowed_roles=self.LOGIN_REQUIRED_ROLES,
        )
        self._register_tool(
            "get_booking_by_number",
            "按订单号查询订单详情。",
            {
                "booking_number": {"type": "string", "description": "订单号。"},
            },
            self._handle_get_booking_by_number,
            required=["booking_number"],
            allowed_roles=self.LOGIN_REQUIRED_ROLES,
        )
        self._register_tool(
            "cancel_booking",
            "取消订单。会修改后端状态，仅在用户明确要求取消时调用。",
            {
                "booking_id": {"type": "integer", "description": "订单 ID。"},
                "reason": {"type": "string", "description": "取消原因。"},
            },
            self._handle_cancel_booking,
            required=["booking_id", "reason"],
            mode="action",
            allowed_roles=self.LOGIN_REQUIRED_ROLES,
        )
        self._register_tool(
            "check_in_booking",
            "办理入住。会修改后端状态，仅在用户明确要求办理入住时调用。",
            {
                "booking_id": {"type": "integer", "description": "订单 ID。"},
            },
            self._handle_check_in_booking,
            required=["booking_id"],
            mode="action",
            allowed_roles=self.LOGIN_REQUIRED_ROLES,
        )
        self._register_tool(
            "check_out_booking",
            "办理离店。会修改后端状态，仅在用户明确要求办理离店时调用。",
            {
                "booking_id": {"type": "integer", "description": "订单 ID。"},
            },
            self._handle_check_out_booking,
            required=["booking_id"],
            mode="action",
            allowed_roles=self.LOGIN_REQUIRED_ROLES,
        )
        self._register_tool(
            "create_booking",
            "创建订单。会写入新的预订记录，仅在用户明确要求下单或订房时调用。",
            {
                "room_type_id": {"type": "integer", "description": "房型 ID。"},
                "check_in_date": {"type": "string", "description": "入住日期，格式 YYYY-MM-DD。"},
                "check_out_date": {"type": "string", "description": "离店日期，格式 YYYY-MM-DD。"},
                "number_of_guests": {"type": "integer", "description": "入住人数。"},
                "contact_name": {"type": "string", "description": "联系人姓名。"},
                "contact_phone": {"type": "string", "description": "联系人手机号。"},
                "adult_count": {"type": "integer", "description": "成人数，可选。"},
                "child_count": {"type": "integer", "description": "儿童数，可选。"},
                "room_id": {"type": "integer", "description": "房间 ID，可选。"},
                "coupon_id": {"type": "integer", "description": "优惠券 ID，可选。"},
                "special_requests": {"type": "string", "description": "特殊需求，可选。"},
                "contact_email": {"type": "string", "description": "联系人邮箱，可选。"},
            },
            self._handle_create_booking,
            required=[
                "room_type_id",
                "check_in_date",
                "check_out_date",
                "number_of_guests",
                "contact_name",
                "contact_phone",
            ],
            mode="action",
            allowed_roles=("USER", "ADMIN"),
        )

    def _register_payment_tools(self):
        self._register_tool(
            "list_payments",
            "查询支付记录，支持按订单、用户、商家和状态筛选。",
            {
                "booking_id": {"type": "integer", "description": "订单 ID，可选。"},
                "user_id": {"type": "integer", "description": "用户 ID，可选。"},
                "merchant_id": {"type": "integer", "description": "商家 ID，可选。"},
                "status": {"type": "string", "description": "支付状态，可选。"},
            },
            self._handle_list_payments,
            allowed_roles=self.LOGIN_REQUIRED_ROLES,
        )
        self._register_tool(
            "get_payment_detail",
            "按支付 ID 查询支付详情。",
            {
                "payment_id": {"type": "integer", "description": "支付 ID。"},
            },
            self._handle_get_payment_detail,
            required=["payment_id"],
            allowed_roles=self.LOGIN_REQUIRED_ROLES,
        )
        self._register_tool(
            "get_payment_by_number",
            "按支付单号查询支付详情。",
            {
                "payment_number": {"type": "string", "description": "支付单号。"},
            },
            self._handle_get_payment_by_number,
            required=["payment_number"],
            allowed_roles=self.LOGIN_REQUIRED_ROLES,
        )
        self._register_tool(
            "create_payment",
            "创建支付记录。会写入新的支付单，仅在用户明确要求发起支付时调用。",
            {
                "booking_id": {"type": "integer", "description": "订单 ID。"},
                "payment_method": {
                    "type": "string",
                    "description": "支付方式：ALIPAY、WECHAT、BANK_CARD、CASH、OTHER。",
                },
                "payment_type": {
                    "type": "string",
                    "description": "支付类型：DEPOSIT、FULL、REFUND。",
                },
                "amount": {"type": "number", "description": "支付金额。"},
                "remark": {"type": "string", "description": "支付备注，可选。"},
                "status": {"type": "string", "description": "支付状态，可选。"},
            },
            self._handle_create_payment,
            required=["booking_id", "payment_method", "payment_type", "amount"],
            mode="action",
            allowed_roles=self.LOGIN_REQUIRED_ROLES,
        )
        self._register_tool(
            "process_payment",
            "处理支付并确认到账。会修改支付和订单状态，仅在用户明确要求确认支付时调用。",
            {
                "payment_id": {"type": "integer", "description": "支付 ID。"},
                "transaction_id": {"type": "string", "description": "外部交易流水号。"},
            },
            self._handle_process_payment,
            required=["payment_id", "transaction_id"],
            mode="action",
            allowed_roles=self.LOGIN_REQUIRED_ROLES,
        )

    def _register_review_tools(self):
        self._register_tool(
            "list_reviews",
            "查询评价列表，支持按房源、用户和状态筛选。",
            {
                "property_id": {"type": "integer", "description": "房源 ID，可选。"},
                "user_id": {"type": "integer", "description": "用户 ID，可选。"},
                "status": {"type": "string", "description": "评价状态，可选。"},
            },
            self._handle_list_reviews,
        )
        self._register_tool(
            "get_review_detail",
            "按评价 ID 查询评价详情。",
            {
                "review_id": {"type": "integer", "description": "评价 ID。"},
            },
            self._handle_get_review_detail,
            required=["review_id"],
        )
        self._register_tool(
            "get_review_by_booking",
            "按订单 ID 查询该订单对应的评价。",
            {
                "booking_id": {"type": "integer", "description": "订单 ID。"},
            },
            self._handle_get_review_by_booking,
            required=["booking_id"],
            allowed_roles=self.LOGIN_REQUIRED_ROLES,
        )
        self._register_tool(
            "reply_review",
            "回复评价。会修改后端状态，仅在用户明确要求回复评价时调用。",
            {
                "review_id": {"type": "integer", "description": "评价 ID。"},
                "reply_content": {"type": "string", "description": "回复内容。"},
            },
            self._handle_reply_review,
            required=["review_id", "reply_content"],
            mode="action",
            allowed_roles=self.STAFF_ROLES,
        )

    def _register_notification_tools(self):
        self._register_tool(
            "list_notifications",
            "查询通知列表，支持按用户和未读状态筛选。",
            {
                "user_id": {"type": "integer", "description": "用户 ID，可选。"},
                "unread_only": {"type": "boolean", "description": "是否只看未读通知，默认 false。"},
            },
            self._handle_list_notifications,
            allowed_roles=self.LOGIN_REQUIRED_ROLES,
        )
        self._register_tool(
            "get_unread_notification_count",
            "查询用户未读通知数量。",
            {
                "user_id": {"type": "integer", "description": "用户 ID。"},
            },
            self._handle_get_unread_notification_count,
            required=["user_id"],
            allowed_roles=self.LOGIN_REQUIRED_ROLES,
        )
        self._register_tool(
            "mark_notification_read",
            "将单条通知设为已读。会修改后端状态，仅在用户明确要求时调用。",
            {
                "notification_id": {"type": "integer", "description": "通知 ID。"},
            },
            self._handle_mark_notification_read,
            required=["notification_id"],
            mode="action",
            allowed_roles=self.LOGIN_REQUIRED_ROLES,
        )
        self._register_tool(
            "mark_all_notifications_read",
            "将某个用户的通知全部设为已读。会修改后端状态，仅在用户明确要求时调用。",
            {
                "user_id": {"type": "integer", "description": "用户 ID。"},
            },
            self._handle_mark_all_notifications_read,
            required=["user_id"],
            mode="action",
            allowed_roles=self.LOGIN_REQUIRED_ROLES,
        )

    def _register_merchant_tools(self):
        self._register_tool(
            "list_merchants",
            "查询商家列表，支持按状态和城市筛选。",
            {
                "status": {"type": "string", "description": "商家状态，可选。"},
                "city": {"type": "string", "description": "城市名，可选。"},
            },
            self._public(self.backend_api_service.list_merchants),
            allowed_roles=self.ADMIN_ROLES,
        )
        self._register_tool(
            "get_merchant_detail",
            "按商家 ID 查询商家详情。",
            {
                "merchant_id": {"type": "integer", "description": "商家 ID。"},
            },
            self._handle_get_merchant_detail,
            required=["merchant_id"],
            allowed_roles=self.STAFF_ROLES,
        )
        self._register_tool(
            "get_merchant_by_user",
            "按用户 ID 查询其关联的商家信息。",
            {
                "user_id": {"type": "integer", "description": "用户 ID。"},
            },
            self._handle_get_merchant_by_user,
            required=["user_id"],
            allowed_roles=self.STAFF_ROLES,
        )

    def _register_user_tools(self):
        self._register_tool(
            "list_users",
            "查询用户列表。",
            {},
            self._public(self.backend_api_service.list_users),
            allowed_roles=self.ADMIN_ROLES,
        )
        self._register_tool(
            "get_user_detail",
            "按用户 ID 查询用户详情。",
            {
                "user_id": {"type": "integer", "description": "用户 ID。"},
            },
            self._handle_get_user_detail,
            required=["user_id"],
            allowed_roles=self.LOGIN_REQUIRED_ROLES,
        )

    def _register_coupon_tools(self):
        self._register_tool(
            "list_coupons",
            "查询优惠券列表，支持按商家和状态筛选。",
            {
                "merchant_id": {"type": "integer", "description": "商家 ID，可选。"},
                "status": {"type": "string", "description": "优惠券状态，可选。"},
            },
            self._handle_list_coupons,
        )
        self._register_tool(
            "get_coupon_detail",
            "按优惠券 ID 查询详情。",
            {
                "coupon_id": {"type": "integer", "description": "优惠券 ID。"},
            },
            self._handle_get_coupon_detail,
            required=["coupon_id"],
        )

    def _handle_list_bookings(self, user_context=None, **kwargs):
        return self.booking_handler.list_bookings(user_context=user_context, **kwargs)

    def _handle_get_booking_detail(self, booking_id, user_context=None):
        return self.booking_handler.get_booking_detail(booking_id, user_context=user_context)

    def _handle_get_booking_by_number(self, booking_number, user_context=None):
        return self.booking_handler.get_booking_by_number(booking_number, user_context=user_context)

    def _handle_cancel_booking(self, booking_id, reason, user_context=None):
        return self.booking_handler.cancel_booking(booking_id, reason, user_context=user_context)

    def _handle_check_in_booking(self, booking_id, user_context=None):
        return self.booking_handler.check_in_booking(booking_id, user_context=user_context)

    def _handle_check_out_booking(self, booking_id, user_context=None):
        return self.booking_handler.check_out_booking(booking_id, user_context=user_context)

    def _handle_create_booking(
        self,
        room_type_id,
        check_in_date,
        check_out_date,
        number_of_guests,
        contact_name,
        contact_phone,
        adult_count=1,
        child_count=0,
        room_id=None,
        coupon_id=None,
        special_requests=None,
        contact_email=None,
        user_context=None,
    ):
        return self.booking_handler.create_booking(
            room_type_id=room_type_id,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            number_of_guests=number_of_guests,
            contact_name=contact_name,
            contact_phone=contact_phone,
            adult_count=adult_count,
            child_count=child_count,
            room_id=room_id,
            coupon_id=coupon_id,
            special_requests=special_requests,
            contact_email=contact_email,
            user_context=user_context,
        )

    def _handle_list_payments(self, user_context=None, **kwargs):
        return self.payment_handler.list_payments(user_context=user_context, **kwargs)

    def _handle_get_payment_detail(self, payment_id, user_context=None):
        return self.payment_handler.get_payment_detail(payment_id, user_context=user_context)

    def _handle_get_payment_by_number(self, payment_number, user_context=None):
        return self.payment_handler.get_payment_by_number(payment_number, user_context=user_context)

    def _handle_create_payment(
        self,
        booking_id,
        payment_method,
        payment_type,
        amount,
        remark=None,
        status=None,
        user_context=None,
    ):
        return self.payment_handler.create_payment(
            booking_id=booking_id,
            payment_method=payment_method,
            payment_type=payment_type,
            amount=amount,
            remark=remark,
            status=status,
            user_context=user_context,
        )

    def _handle_process_payment(self, payment_id, transaction_id, user_context=None):
        return self.payment_handler.process_payment(
            payment_id=payment_id,
            transaction_id=transaction_id,
            user_context=user_context,
        )

    def _handle_list_reviews(self, user_context=None, **kwargs):
        role = self._resolve_role(user_context)
        scoped = dict(kwargs)

        if role == "USER" and scoped.get("user_id") is not None:
            scoped["user_id"] = self._current_user_id(user_context)

        if role == "MERCHANT":
            property_id = scoped.get("property_id")
            if property_id is not None:
                self._ensure_property_owned_by_current_merchant(property_id, user_context)
                result = self.backend_api_service.list_reviews(**scoped)
                return self._filter_items(result, lambda item: self._can_access_review_action(item, user_context))

            property_ids = self._list_current_merchant_property_ids(user_context)
            items = []
            for current_property_id in property_ids:
                chunk = self.backend_api_service.list_reviews(
                    property_id=current_property_id,
                    status=scoped.get("status"),
                )
                items.extend(self._unwrap_items(chunk))
            return {
                "query": {
                    "merchant_id": self._current_merchant_id(user_context),
                    "status": scoped.get("status"),
                },
                "count": len(items),
                "items": items,
                "source": "booking-service:/reviews",
            }

        return self.backend_api_service.list_reviews(**scoped)

    def _handle_get_review_detail(self, review_id, user_context=None):
        result = self._load_review_detail(review_id)
        role = self._resolve_role(user_context)
        if role == "MERCHANT":
            self._assert_access(
                self._can_access_review_action(self._unwrap_item(result), user_context),
                "当前商家无权访问该评价。",
            )
        return result

    def _handle_get_review_by_booking(self, booking_id, user_context=None):
        result = self.backend_api_service.get_review_by_booking(booking_id)
        self._assert_access(
            self._can_access_review_by_booking(self._unwrap_item(result), user_context),
            "当前用户无权访问该订单的评价。",
        )
        return result

    def _handle_reply_review(self, review_id, reply_content, user_context=None):
        result = self._load_review_detail(review_id)
        self._assert_access(
            self._can_access_review_action(self._unwrap_item(result), user_context),
            "当前商家无权回复该评价。",
        )
        return self.backend_api_service.reply_review(review_id, reply_content)

    def _handle_list_notifications(self, user_context=None, **kwargs):
        return self.notification_handler.list_notifications(user_context=user_context, **kwargs)

    def _handle_get_unread_notification_count(self, user_id, user_context=None):
        return self.notification_handler.get_unread_notification_count(
            user_id, user_context=user_context
        )

    def _handle_mark_notification_read(self, notification_id, user_context=None):
        return self.notification_handler.mark_notification_read(
            notification_id, user_context=user_context
        )

    def _handle_mark_all_notifications_read(self, user_id, user_context=None):
        return self.notification_handler.mark_all_notifications_read(
            user_id, user_context=user_context
        )

    def _handle_get_merchant_detail(self, merchant_id, user_context=None):
        role = self._resolve_role(user_context)
        scoped_merchant_id = merchant_id
        if role == "MERCHANT":
            scoped_merchant_id = self._current_merchant_id(user_context)
        return self.backend_api_service.get_merchant_detail(scoped_merchant_id)

    def _handle_get_merchant_by_user(self, user_id, user_context=None):
        role = self._resolve_role(user_context)
        scoped_user_id = user_id
        if role == "MERCHANT":
            scoped_user_id = self._current_user_id(user_context)

        result = self.backend_api_service.get_merchant_by_user(scoped_user_id)
        item = self._unwrap_item(result)
        if role == "MERCHANT":
            self._assert_access(
                self._merchant_owner_user_id(item) == self._current_user_id(user_context),
                "当前商家无权访问该商家信息。",
            )
        return result

    def _handle_get_user_detail(self, user_id, user_context=None):
        role = self._resolve_role(user_context)
        scoped_user_id = user_id
        if role in {"USER", "MERCHANT"}:
            scoped_user_id = self._current_user_id(user_context)
        return self.backend_api_service.get_user_detail(scoped_user_id)

    def _handle_list_coupons(self, user_context=None, **kwargs):
        role = self._resolve_role(user_context)
        scoped = dict(kwargs)
        if role == "MERCHANT":
            scoped["merchant_id"] = self._current_merchant_id(user_context)
        result = self.backend_api_service.list_coupons(**scoped)
        if role == "MERCHANT":
            return self._filter_items(
                result,
                lambda item: self._coupon_merchant_id(item) == self._current_merchant_id(user_context),
            )
        return result

    def _handle_get_coupon_detail(self, coupon_id, user_context=None):
        result = self.backend_api_service.get_coupon_detail(coupon_id)
        if self._resolve_role(user_context) == "MERCHANT":
            self._assert_access(
                self._coupon_merchant_id(self._unwrap_item(result)) == self._current_merchant_id(user_context),
                "当前商家无权访问该优惠券。",
            )
        return result

    def _pending_summary_cancel_booking(self, arguments, user_context=None):
        booking_id = arguments.get("booking_id")
        reason = str(arguments.get("reason") or "").strip()
        booking = self.booking_handler.get_booking_detail(booking_id, user_context=user_context)
        item = self._unwrap_item(booking)
        booking_number = self._get_path(item, "bookingNumber") or booking_id
        status = self._get_path(item, "status") or "UNKNOWN"
        return {
            "action": "cancel_booking",
            "target_type": "booking",
            "target_id": booking_id,
            "target_label": f"订单 {booking_number}",
            "current_status": status,
            "impact": "订单状态将变为已取消，可能触发平台取消规则。",
            "reason": reason,
            "message": f"已为订单 {booking_number} 创建取消确认，当前状态为 {status}，确认后才会执行取消。",
            "confirmation_text": f"确认取消订单 {booking_number}",
        }

    def _pending_summary_check_in_booking(self, arguments, user_context=None):
        booking_id = arguments.get("booking_id")
        booking = self.booking_handler.get_booking_detail(booking_id, user_context=user_context)
        item = self._unwrap_item(booking)
        booking_number = self._get_path(item, "bookingNumber") or booking_id
        status = self._get_path(item, "status") or "UNKNOWN"
        return {
            "action": "check_in_booking",
            "target_type": "booking",
            "target_id": booking_id,
            "target_label": f"订单 {booking_number}",
            "current_status": status,
            "impact": "订单状态将更新为已入住。",
            "message": f"已为订单 {booking_number} 创建入住确认，当前状态为 {status}，确认后才会执行入住。",
            "confirmation_text": f"确认订单 {booking_number} 入住",
        }

    def _pending_summary_check_out_booking(self, arguments, user_context=None):
        booking_id = arguments.get("booking_id")
        booking = self.booking_handler.get_booking_detail(booking_id, user_context=user_context)
        item = self._unwrap_item(booking)
        booking_number = self._get_path(item, "bookingNumber") or booking_id
        status = self._get_path(item, "status") or "UNKNOWN"
        return {
            "action": "check_out_booking",
            "target_type": "booking",
            "target_id": booking_id,
            "target_label": f"订单 {booking_number}",
            "current_status": status,
            "impact": "订单状态将更新为已离店。",
            "message": f"已为订单 {booking_number} 创建离店确认，当前状态为 {status}，确认后才会执行离店。",
            "confirmation_text": f"确认订单 {booking_number} 离店",
        }

    def _pending_summary_create_booking(self, arguments, user_context=None):
        room_type_id = arguments.get("room_type_id")
        check_in_date = self._stringify(arguments.get("check_in_date"))
        check_out_date = self._stringify(arguments.get("check_out_date"))
        number_of_guests = arguments.get("number_of_guests")
        contact_name = self._stringify(arguments.get("contact_name"))
        return {
            "action": "create_booking",
            "target_type": "booking_create",
            "target_id": room_type_id,
            "target_label": f"房型 {room_type_id} 新订单",
            "impact": "确认后会创建新的订单记录，并占用对应日期库存。",
            "message": f"已创建订房确认：房型 {room_type_id}，{check_in_date} 至 {check_out_date}，{number_of_guests} 人入住，联系人 {contact_name}。",
            "confirmation_text": f"确认创建房型 {room_type_id} 的订单",
        }

    def _pending_summary_create_payment(self, arguments, user_context=None):
        booking_id = arguments.get("booking_id")
        booking = self.booking_handler.get_booking_detail(booking_id, user_context=user_context)
        item = self._unwrap_item(booking)
        booking_number = self._get_path(item, "bookingNumber") or booking_id
        amount = arguments.get("amount")
        payment_method = self._stringify(arguments.get("payment_method"))
        return {
            "action": "create_payment",
            "target_type": "payment_create",
            "target_id": booking_id,
            "target_label": f"订单 {booking_number} 支付单",
            "impact": "确认后会创建新的支付记录，但不会自动把订单改成已支付。",
            "message": f"已创建支付确认：订单 {booking_number}，金额 {amount}，支付方式 {payment_method}。",
            "confirmation_text": f"确认创建订单 {booking_number} 的支付单",
        }

    def _pending_summary_process_payment(self, arguments, user_context=None):
        payment_id = arguments.get("payment_id")
        payment = self.payment_handler.get_payment_detail(payment_id, user_context=user_context)
        item = self._unwrap_item(payment)
        payment_number = self._get_path(item, "paymentNumber") or payment_id
        booking_number = self._get_path(item, "booking", "bookingNumber") or ""
        status = self._get_path(item, "status") or "UNKNOWN"
        return {
            "action": "process_payment",
            "target_type": "payment_process",
            "target_id": payment_id,
            "target_label": f"支付单 {payment_number}",
            "current_status": status,
            "booking_number": booking_number,
            "impact": "确认后会把支付单更新为成功，并可能同步把订单状态更新为已确认/已支付。",
            "message": f"已创建支付处理确认：支付单 {payment_number} 当前状态为 {status}，确认后会执行到账处理。",
            "confirmation_text": f"确认处理支付单 {payment_number}",
        }

    def _pending_summary_reply_review(self, arguments, user_context=None):
        review_id = arguments.get("review_id")
        review = self._load_review_detail(review_id)
        item = self._unwrap_item(review)
        booking_number = self._get_path(item, "booking", "bookingNumber")
        property_name = self._get_path(item, "property", "propertyName") or self._get_path(item, "property", "name")
        return {
            "action": "reply_review",
            "target_type": "review",
            "target_id": review_id,
            "target_label": f"评价 {review_id}",
            "property_name": property_name or "",
            "booking_number": booking_number or "",
            "impact": "确认后会提交商家回复内容，并写入评价记录。",
            "message": f"已为评价 {review_id} 创建回复确认，确认后才会正式提交回复。",
            "confirmation_text": f"确认回复评价 {review_id}",
        }

    def _pending_summary_mark_notification_read(self, arguments, user_context=None):
        notification_id = arguments.get("notification_id")
        self._ensure_notification_owned(notification_id, user_context)
        return {
            "action": "mark_notification_read",
            "target_type": "notification",
            "target_id": notification_id,
            "target_label": f"通知 {notification_id}",
            "impact": "确认后该通知会被标记为已读。",
            "message": f"已为通知 {notification_id} 创建已读确认，确认后才会执行。",
            "confirmation_text": f"确认通知 {notification_id} 已读",
        }

    def _pending_summary_mark_all_notifications_read(self, arguments, user_context=None):
        role = self._resolve_role(user_context)
        target_user_id = arguments.get("user_id")
        if role in {"USER", "MERCHANT"}:
            target_user_id = self._current_user_id(user_context)
        return {
            "action": "mark_all_notifications_read",
            "target_type": "notification_batch",
            "target_id": target_user_id,
            "target_label": f"用户 {target_user_id} 的全部通知",
            "impact": "确认后该用户的通知会被全部标记为已读。",
            "message": f"已为用户 {target_user_id} 创建全部已读确认，确认后才会执行。",
            "confirmation_text": f"确认用户 {target_user_id} 全部通知已读",
        }
