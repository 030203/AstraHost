class BookingToolHandler:
    def __init__(self, backend_api_service, access_policy):
        self.backend_api_service = backend_api_service
        self.access_policy = access_policy

    def list_bookings(self, user_context=None, **kwargs):
        role = self.access_policy.resolve_role(user_context)
        scoped = dict(kwargs)
        if role == "USER":
            scoped["user_id"] = self.access_policy.current_user_id(user_context)
            scoped.pop("merchant_id", None)
        elif role == "MERCHANT":
            if scoped.get("property_id") is not None:
                self.access_policy.ensure_property_owned_by_current_merchant(
                    scoped["property_id"], user_context
                )
                scoped.pop("merchant_id", None)
            else:
                scoped["merchant_id"] = self.access_policy.current_merchant_id(user_context)
            scoped.pop("user_id", None)

        result = self.backend_api_service.list_bookings(**scoped)
        return self.access_policy.filter_items(
            result,
            lambda item: self.access_policy.can_access_booking(item, user_context),
        )

    def get_booking_detail(self, booking_id, user_context=None):
        result = self.backend_api_service.get_booking_detail(booking_id)
        self.access_policy.assert_access(
            self.access_policy.can_access_booking(
                self.access_policy.unwrap_item(result), user_context
            ),
            "当前用户无权访问该订单。",
        )
        return result

    def get_booking_by_number(self, booking_number, user_context=None):
        result = self.backend_api_service.get_booking_by_number(booking_number)
        self.access_policy.assert_access(
            self.access_policy.can_access_booking(
                self.access_policy.unwrap_item(result), user_context
            ),
            "当前用户无权访问该订单。",
        )
        return result

    def cancel_booking(self, booking_id, reason, user_context=None):
        booking = self.backend_api_service.get_booking_detail(booking_id)
        self.access_policy.assert_access(
            self.access_policy.can_access_booking(
                self.access_policy.unwrap_item(booking), user_context
            ),
            "当前用户无权取消该订单。",
        )
        return self.backend_api_service.cancel_booking(booking_id, reason)

    def create_booking(
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
        return self.backend_api_service.create_booking(
            user_id=self.access_policy.current_user_id(user_context),
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
        )

    def check_in_booking(self, booking_id, user_context=None):
        booking = self.backend_api_service.get_booking_detail(booking_id)
        self.access_policy.assert_access(
            self.access_policy.can_access_booking(
                self.access_policy.unwrap_item(booking), user_context
            ),
            "当前用户无权操作该订单入住。",
        )
        return self.backend_api_service.check_in_booking(booking_id)

    def check_out_booking(self, booking_id, user_context=None):
        booking = self.backend_api_service.get_booking_detail(booking_id)
        self.access_policy.assert_access(
            self.access_policy.can_access_booking(
                self.access_policy.unwrap_item(booking), user_context
            ),
            "当前用户无权操作该订单离店。",
        )
        return self.backend_api_service.check_out_booking(booking_id)


class PaymentToolHandler:
    def __init__(self, backend_api_service, access_policy):
        self.backend_api_service = backend_api_service
        self.access_policy = access_policy

    def list_payments(self, user_context=None, **kwargs):
        role = self.access_policy.resolve_role(user_context)
        scoped = dict(kwargs)
        if role == "USER":
            scoped["user_id"] = self.access_policy.current_user_id(user_context)
            scoped.pop("merchant_id", None)
        elif role == "MERCHANT":
            scoped["merchant_id"] = self.access_policy.current_merchant_id(user_context)
            scoped.pop("user_id", None)

        result = self.backend_api_service.list_payments(**scoped)
        return self.access_policy.filter_items(
            result,
            lambda item: self.access_policy.can_access_payment(item, user_context),
        )

    def get_payment_detail(self, payment_id, user_context=None):
        result = self.backend_api_service.get_payment_detail(payment_id)
        self.access_policy.assert_access(
            self.access_policy.can_access_payment(
                self.access_policy.unwrap_item(result), user_context
            ),
            "当前用户无权访问该支付记录。",
        )
        return result

    def get_payment_by_number(self, payment_number, user_context=None):
        result = self.backend_api_service.get_payment_by_number(payment_number)
        self.access_policy.assert_access(
            self.access_policy.can_access_payment(
                self.access_policy.unwrap_item(result), user_context
            ),
            "当前用户无权访问该支付记录。",
        )
        return result

    def create_payment(
        self,
        booking_id,
        payment_method,
        payment_type,
        amount,
        remark=None,
        status=None,
        user_context=None,
    ):
        booking = self.backend_api_service.get_booking_detail(booking_id)
        self.access_policy.assert_access(
            self.access_policy.can_access_booking(
                self.access_policy.unwrap_item(booking), user_context
            ),
            "当前用户无权为该订单创建支付记录。",
        )
        return self.backend_api_service.create_payment(
            booking_id=booking_id,
            payment_method=payment_method,
            payment_type=payment_type,
            amount=amount,
            remark=remark,
            status=status,
        )

    def process_payment(self, payment_id, transaction_id, user_context=None):
        payment = self.backend_api_service.get_payment_detail(payment_id)
        self.access_policy.assert_access(
            self.access_policy.can_access_payment(
                self.access_policy.unwrap_item(payment), user_context
            ),
            "当前用户无权处理该支付记录。",
        )
        return self.backend_api_service.process_payment(payment_id, transaction_id)


class NotificationToolHandler:
    def __init__(self, backend_api_service, access_policy):
        self.backend_api_service = backend_api_service
        self.access_policy = access_policy

    def list_notifications(self, user_context=None, **kwargs):
        role = self.access_policy.resolve_role(user_context)
        scoped = dict(kwargs)
        if role in {"USER", "MERCHANT"}:
            scoped["user_id"] = self.access_policy.current_user_id(user_context)
        result = self.backend_api_service.list_notifications(**scoped)
        return self.access_policy.filter_items(
            result,
            lambda item: self.access_policy.can_access_notification(item, user_context),
        )

    def get_unread_notification_count(self, user_id, user_context=None):
        role = self.access_policy.resolve_role(user_context)
        scoped_user_id = user_id
        if role in {"USER", "MERCHANT"}:
            scoped_user_id = self.access_policy.current_user_id(user_context)
        return self.backend_api_service.get_unread_notification_count(scoped_user_id)

    def mark_notification_read(self, notification_id, user_context=None):
        self.access_policy.ensure_notification_owned(notification_id, user_context)
        return self.backend_api_service.mark_notification_read(notification_id)

    def mark_all_notifications_read(self, user_id, user_context=None):
        role = self.access_policy.resolve_role(user_context)
        scoped_user_id = user_id
        if role in {"USER", "MERCHANT"}:
            scoped_user_id = self.access_policy.current_user_id(user_context)
        return self.backend_api_service.mark_all_notifications_read(scoped_user_id)
