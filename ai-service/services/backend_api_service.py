import logging

import requests

from services.location_utils import normalize_city_name, normalize_district_name
from services.request_context import get_auth_header, get_request_id


logger = logging.getLogger(__name__)


class BackendAPIService:
    def __init__(self, config):
        self.config = config

    # === SECTION: requests ===
    def _request(self, method, path, params=None, json_body=None, text_body=None):
        headers = {
            "Accept": "application/json",
            "User-Agent": self.config.http_user_agent(),
        }
        request_id = get_request_id()
        if request_id:
            headers[self.config.request_id_header()] = request_id
        auth_header = get_auth_header()
        if auth_header:
            headers["Authorization"] = auth_header
        request_kwargs = {
            "method": method,
            "url": f"{self._base_url()}{path}",
            "params": self._clean_params(params),
            "headers": headers,
            "timeout": self.config.http_timeout(),
        }

        if json_body is not None:
            request_kwargs["json"] = json_body
        if text_body is not None:
            headers["Content-Type"] = "text/plain; charset=utf-8"
            request_kwargs["data"] = str(text_body)

        try:
            response = requests.request(**request_kwargs)
        except requests.RequestException as exc:
            logger.exception(
                "backend_api_request_failed method=%s path=%s request_id=%s",
                method,
                path,
                request_id or "-",
            )
            raise ValueError(self._build_request_exception_error(method, path, exc)) from exc

        if not response.ok:
            logger.warning(
                "backend_api_http_error method=%s path=%s status=%s request_id=%s",
                method,
                path,
                response.status_code,
                request_id or "-",
            )
            raise ValueError(self._build_http_error(method, path, response))

        if not response.content:
            return {}

        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return response.json()

        text = response.text.strip()
        return {"text": text} if text else {}

    def _base_url(self):
        return str(self.config.booking_service_base_url()).rstrip("/")

    def _clean_params(self, payload):
        if not payload:
            return {}

        cleaned = {}
        for key, value in payload.items():
            if value is None or value == "" or value == []:
                continue
            cleaned[key] = value
        return cleaned

    def _build_http_error(self, method, path, response):
        status_code = response.status_code
        details = (response.text or "").strip()
        if details:
            try:
                payload = response.json()
                message = payload.get("message") or payload.get("error")
                if message and isinstance(message, str):
                    return f"{method} {path} 调用失败，HTTP {status_code}：{message}"
            except Exception:
                pass
            if len(details) > 500:
                details = f"{details[:500]}..."
            return f"{method} {path} 调用失败，HTTP {status_code}：{details}"
        return f"{method} {path} 调用失败，HTTP {status_code}"

    def _build_request_exception_error(self, method, path, exc):
        return f"{method} {path} 调用失败：{exc.__class__.__name__}"

    def _wrap_list(self, source, query, payload):
        items = payload if isinstance(payload, list) else []
        return {
            "query": query or {},
            "count": len(items),
            "items": items,
            "source": source,
        }

    def _wrap_item(self, source, payload, **extra):
        result = {"item": payload, "source": source}
        result.update(extra)
        return result

    def _wrap_action(self, source, action, payload):
        return {
            "action": action,
            "result": payload,
            "source": source,
        }

    # === SECTION: property_tools ===
    def list_properties(self, merchant_id=None, city=None, status=None, featured=None):
        params = self._clean_params(
            {
                "merchantId": merchant_id,
                "city": normalize_city_name(city),
                "status": status,
                "featured": featured,
            }
        )
        payload = self._request("GET", "/properties", params=params)
        return self._wrap_list("booking-service:/properties", params, payload)

    def search_properties(
        self,
        keyword=None,
        city=None,
        district=None,
        min_price=None,
        max_price=None,
        min_rating=None,
        featured=None,
        facilities=None,
        latitude=None,
        longitude=None,
        distance_km=None,
        page=1,
        size=10,
    ):
        params = self._clean_params(
            {
                "keyword": keyword,
                "city": normalize_city_name(city),
                "district": normalize_district_name(district),
                "minPrice": min_price,
                "maxPrice": max_price,
                "minRating": min_rating,
                "featured": featured,
                "facilities": facilities,
                "latitude": latitude,
                "longitude": longitude,
                "distanceKm": distance_km,
                "page": max(1, int(page or 1)),
                "size": min(max(1, int(size or 10)), 20),
            }
        )
        payload = self._request("GET", "/properties/search", params=params)
        return {
            "query": params,
            "items": payload.get("items") or [],
            "total": payload.get("total", 0),
            "page": payload.get("page", params.get("page", 1)),
            "size": payload.get("size", params.get("size", 10)),
            "used_elasticsearch": payload.get("usedElasticsearch"),
            "source": "booking-service:/properties/search",
        }

    def get_property_detail(self, property_id):
        normalized_property_id = int(property_id)
        payload = self._request("GET", f"/properties/{normalized_property_id}/detail")
        return self._wrap_item(
            f"booking-service:/properties/{normalized_property_id}/detail",
            payload,
        )

    def get_top_properties(self, limit=5):
        params = {"limit": min(max(1, int(limit or 5)), 20)}
        payload = self._request("GET", "/properties/top", params=params)
        return self._wrap_list("booking-service:/properties/top", params, payload)

    # === SECTION: room_type_tools ===
    def list_room_types(self, property_id=None):
        params = self._clean_params({"propertyId": property_id})
        payload = self._request("GET", "/room-types", params=params)
        return self._wrap_list("booking-service:/room-types", params, payload)

    def get_room_type_detail(self, room_type_id):
        normalized_room_type_id = int(room_type_id)
        payload = self._request("GET", f"/room-types/{normalized_room_type_id}")
        return self._wrap_item(
            f"booking-service:/room-types/{normalized_room_type_id}",
            payload,
        )

    def get_active_room_types(self, property_id):
        normalized_property_id = int(property_id)
        payload = self._request("GET", f"/room-types/property/{normalized_property_id}/active")
        return self._wrap_list(
            f"booking-service:/room-types/property/{normalized_property_id}/active",
            {"propertyId": normalized_property_id},
            payload,
        )

    # === SECTION: booking_tools ===
    def list_bookings(self, user_id=None, property_id=None, merchant_id=None, status=None):
        params = self._clean_params(
            {
                "userId": user_id,
                "propertyId": property_id,
                "merchantId": merchant_id,
                "status": status,
            }
        )
        payload = self._request("GET", "/bookings", params=params)
        return self._wrap_list("booking-service:/bookings", params, payload)

    def get_booking_detail(self, booking_id):
        normalized_booking_id = int(booking_id)
        payload = self._request("GET", f"/bookings/{normalized_booking_id}")
        return self._wrap_item(
            f"booking-service:/bookings/{normalized_booking_id}",
            payload,
        )

    def get_booking_by_number(self, booking_number):
        payload = self._request("GET", f"/bookings/number/{booking_number}")
        return self._wrap_item(
            f"booking-service:/bookings/number/{booking_number}",
            payload,
        )

    # === SECTION: identity_tools ===
    def get_user_detail(self, user_id):
        normalized_user_id = int(user_id)
        payload = self._request("GET", f"/users/{normalized_user_id}")
        return self._wrap_item(
            f"booking-service:/users/{normalized_user_id}",
            payload,
        )

    def get_merchant_by_user_id(self, user_id):
        normalized_user_id = int(user_id)
        payload = self._request("GET", f"/merchants/user/{normalized_user_id}")
        return self._wrap_item(
            f"booking-service:/merchants/user/{normalized_user_id}",
            payload,
        )

    def cancel_booking(self, booking_id, reason):
        normalized_booking_id = int(booking_id)
        payload = self._request(
            "POST",
            f"/bookings/{normalized_booking_id}/cancel",
            text_body=reason,
        )
        return self._wrap_action(
            f"booking-service:/bookings/{normalized_booking_id}/cancel",
            "cancel_booking",
            payload,
        )

    def create_booking(
        self,
        user_id,
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
    ):
        payload = self._request(
            "POST",
            "/bookings",
            json_body={
                "user": {"id": int(user_id)},
                "roomType": {"id": int(room_type_id)},
                "room": {"id": int(room_id)} if room_id is not None else None,
                "coupon": {"id": int(coupon_id)} if coupon_id is not None else None,
                "checkInDate": str(check_in_date),
                "checkOutDate": str(check_out_date),
                "numberOfGuests": int(number_of_guests),
                "adultCount": int(adult_count or 0),
                "childCount": int(child_count or 0),
                "specialRequests": special_requests,
                "contactName": str(contact_name),
                "contactPhone": str(contact_phone),
                "contactEmail": contact_email,
            },
        )
        return self._wrap_action(
            "booking-service:/bookings",
            "create_booking",
            payload,
        )

    def check_in_booking(self, booking_id):
        normalized_booking_id = int(booking_id)
        payload = self._request("POST", f"/bookings/{normalized_booking_id}/check-in")
        return self._wrap_action(
            f"booking-service:/bookings/{normalized_booking_id}/check-in",
            "check_in_booking",
            payload,
        )

    def check_out_booking(self, booking_id):
        normalized_booking_id = int(booking_id)
        payload = self._request("POST", f"/bookings/{normalized_booking_id}/check-out")
        return self._wrap_action(
            f"booking-service:/bookings/{normalized_booking_id}/check-out",
            "check_out_booking",
            payload,
        )

    # === SECTION: payment_tools ===
    def list_payments(self, booking_id=None, user_id=None, merchant_id=None, status=None):
        params = self._clean_params(
            {
                "bookingId": booking_id,
                "userId": user_id,
                "merchantId": merchant_id,
                "status": status,
            }
        )
        payload = self._request("GET", "/payments", params=params)
        return self._wrap_list("booking-service:/payments", params, payload)

    def get_payment_detail(self, payment_id):
        normalized_payment_id = int(payment_id)
        payload = self._request("GET", f"/payments/{normalized_payment_id}")
        return self._wrap_item(
            f"booking-service:/payments/{normalized_payment_id}",
            payload,
        )

    def get_payment_by_number(self, payment_number):
        payload = self._request("GET", f"/payments/number/{payment_number}")
        return self._wrap_item(
            f"booking-service:/payments/number/{payment_number}",
            payload,
        )

    def create_payment(
        self,
        booking_id,
        payment_method,
        payment_type,
        amount,
        remark=None,
        status=None,
    ):
        payload = self._request(
            "POST",
            "/payments",
            json_body={
                "booking": {"id": int(booking_id)},
                "paymentMethod": str(payment_method),
                "paymentType": str(payment_type),
                "amount": amount,
                "remark": remark,
                "status": status,
            },
        )
        return self._wrap_action(
            "booking-service:/payments",
            "create_payment",
            payload,
        )

    def process_payment(self, payment_id, transaction_id):
        normalized_payment_id = int(payment_id)
        payload = self._request(
            "POST",
            f"/payments/{normalized_payment_id}/process",
            params={"transactionId": transaction_id},
        )
        return self._wrap_action(
            f"booking-service:/payments/{normalized_payment_id}/process",
            "process_payment",
            payload,
        )

    # === SECTION: review_tools ===
    def list_reviews(self, property_id=None, user_id=None, status=None):
        params = self._clean_params(
            {
                "propertyId": property_id,
                "userId": user_id,
                "status": status,
            }
        )
        payload = self._request("GET", "/reviews", params=params)
        return self._wrap_list("booking-service:/reviews", params, payload)

    def get_review_detail(self, review_id):
        normalized_review_id = int(review_id)
        payload = self._request("GET", f"/reviews/{normalized_review_id}")
        return self._wrap_item(
            f"booking-service:/reviews/{normalized_review_id}",
            payload,
        )

    def get_review_by_booking(self, booking_id):
        normalized_booking_id = int(booking_id)
        payload = self._request("GET", f"/reviews/booking/{normalized_booking_id}")
        return self._wrap_item(
            f"booking-service:/reviews/booking/{normalized_booking_id}",
            payload,
        )

    def reply_review(self, review_id, reply_content):
        normalized_review_id = int(review_id)
        payload = self._request(
            "POST",
            f"/reviews/{normalized_review_id}/reply",
            text_body=reply_content,
        )
        return self._wrap_action(
            f"booking-service:/reviews/{normalized_review_id}/reply",
            "reply_review",
            payload,
        )

    # === SECTION: notification_tools ===
    def list_notifications(self, user_id=None, unread_only=False):
        params = self._clean_params(
            {
                "userId": user_id,
                "unreadOnly": bool(unread_only),
            }
        )
        payload = self._request("GET", "/notifications", params=params)
        return self._wrap_list("booking-service:/notifications", params, payload)

    def get_unread_notification_count(self, user_id):
        params = {"userId": int(user_id)}
        payload = self._request("GET", "/notifications/unread-count", params=params)
        return {
            "query": params,
            "count": payload.get("count", 0),
            "source": "booking-service:/notifications/unread-count",
        }

    def mark_notification_read(self, notification_id):
        normalized_notification_id = int(notification_id)
        payload = self._request("POST", f"/notifications/{normalized_notification_id}/read")
        return self._wrap_action(
            f"booking-service:/notifications/{normalized_notification_id}/read",
            "mark_notification_read",
            payload,
        )

    def mark_all_notifications_read(self, user_id):
        params = {"userId": int(user_id)}
        payload = self._request("POST", "/notifications/read-all", params=params)
        return self._wrap_action(
            "booking-service:/notifications/read-all",
            "mark_all_notifications_read",
            {
                "query": params,
                "updated": payload.get("updated", 0),
            },
        )

    # === SECTION: merchant_tools ===
    def list_merchants(self, status=None, city=None):
        params = self._clean_params(
            {
                "status": status,
                "city": city,
            }
        )
        payload = self._request("GET", "/merchants", params=params)
        return self._wrap_list("booking-service:/merchants", params, payload)

    def get_merchant_detail(self, merchant_id):
        normalized_merchant_id = int(merchant_id)
        payload = self._request("GET", f"/merchants/{normalized_merchant_id}")
        return self._wrap_item(
            f"booking-service:/merchants/{normalized_merchant_id}",
            payload,
        )

    def get_merchant_by_user(self, user_id):
        normalized_user_id = int(user_id)
        payload = self._request("GET", f"/merchants/user/{normalized_user_id}")
        return self._wrap_item(
            f"booking-service:/merchants/user/{normalized_user_id}",
            payload,
        )

    # === SECTION: user_tools ===
    def list_users(self):
        payload = self._request("GET", "/users")
        return self._wrap_list("booking-service:/users", {}, payload)

    def get_user_detail(self, user_id):
        normalized_user_id = int(user_id)
        payload = self._request("GET", f"/users/{normalized_user_id}")
        return self._wrap_item(
            f"booking-service:/users/{normalized_user_id}",
            payload,
        )

    # === SECTION: coupon_tools ===
    def list_coupons(self, merchant_id=None, status=None):
        params = self._clean_params(
            {
                "merchantId": merchant_id,
                "status": status,
            }
        )
        payload = self._request("GET", "/coupons", params=params)
        return self._wrap_list("booking-service:/coupons", params, payload)

    def get_coupon_detail(self, coupon_id):
        normalized_coupon_id = int(coupon_id)
        payload = self._request("GET", f"/coupons/{normalized_coupon_id}")
        return self._wrap_item(
            f"booking-service:/coupons/{normalized_coupon_id}",
            payload,
        )
