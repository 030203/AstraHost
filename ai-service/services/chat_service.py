import json
from urllib.parse import quote


class ChatService:
    ACTION_CONFIRMATION_PROMPT = (
        "When a tool result has result.status=pending_confirmation, the action has NOT been executed. "
        "Tell the user that the action is waiting for confirmation, show pending_action.confirmation_text "
        "and pending_action.expires_at, and ask the user to reply with the exact confirmation text. "
        "Never say the action succeeded until the action tool returns a successful non-pending result. "
        "If the user confirms with a confirmation token, call the same action tool with confirmation_token."
    )
    PROPERTY_COLLECTION_TOOLS = (
        "list_properties",
        "search_properties",
        "get_top_properties",
    )
    PROPERTY_DETAIL_TOOLS = ("get_property_detail",)
    PROPERTY_TOOLS = PROPERTY_COLLECTION_TOOLS + PROPERTY_DETAIL_TOOLS
    RECOMMENDATION_HINTS = (
        "推荐",
        "找房",
        "找个",
        "找一下酒店",
        "找一下民宿",
        "酒店推荐",
        "民宿推荐",
        "热门酒店",
        "热门民宿",
        "有哪些酒店",
        "有哪些民宿",
        "看看酒店",
        "看看民宿",
        "高分酒店",
        "高分民宿",
        "介绍",
        "详细介绍",
        "介绍一下",
        "了解",
        "查看",
        "告诉我",
        "给我看看",
        "展示",
        "酒店信息",
        "民宿信息",
        "房源信息",
        "recommend",
        "top hotel",
        "show me",
        "tell me about",
    )

    def __init__(
        self,
        model_client,
        tool_service,
        skill_service,
        default_system_prompt,
        config,
        conversation_store=None,
    ):
        self.model_client = model_client
        self.tool_service = tool_service
        self.skill_service = skill_service
        self.default_system_prompt = default_system_prompt
        self.config = config
        self.conversation_store = conversation_store

    def chat(self, user_message, user_context=None, conversation_id=None, pending_action=None):
        confirmation_result = self._maybe_execute_pending_action(
            user_message,
            pending_action,
            user_context=user_context,
        )
        if confirmation_result is not None:
            self._store_conversation_turn(conversation_id, user_message, confirmation_result["answer"])
            return confirmation_result

        skill_route = self.skill_service.resolve(user_message, user_context=user_context)
        system_prompt = self._build_system_prompt(user_context, skill_route)
        tools = self.tool_service.get_tool_definitions(
            skill_route.tool_names,
            user_context=user_context,
        )
        messages = self._build_conversation_messages(conversation_id, user_message)
        recommendation_state = self._new_recommendation_state()
        latest_pending_action = None

        for _ in range(self.config.tool_call_max_steps()):
            response = self.model_client.create_message(
                messages=messages,
                tools=tools,
                system_prompt=system_prompt,
            )
            if response.stop_reason != "tool_use":
                answer = self._extract_text(response) or "No displayable content was returned."
                self._store_conversation_turn(conversation_id, user_message, answer)
                return {
                    "answer": answer,
                    "source": "anthropic+tools" if tools else "anthropic",
                    "route": self._serialize_route(skill_route),
                    "recommendations": self._finalize_recommendation_state(
                        recommendation_state,
                        user_message=user_message,
                        skill_route=skill_route,
                    ),
                    "pending_action": latest_pending_action,
                }

            tool_turn, _tool_events, recommendation_updates, current_pending_action = self._build_tool_turn(
                response,
                user_context=user_context,
            )
            for update in recommendation_updates:
                self._merge_recommendation_state(recommendation_state, update)
            if current_pending_action:
                latest_pending_action = current_pending_action
            messages.extend(tool_turn)

        return {
            "answer": "Tool call limit reached. Please narrow the request and try again.",
            "source": "service-error",
            "route": self._serialize_route(skill_route),
            "recommendations": self._finalize_recommendation_state(
                recommendation_state,
                user_message=user_message,
                skill_route=skill_route,
            ),
            "pending_action": latest_pending_action,
        }

    def stream_chat(self, user_message, user_context=None, conversation_id=None, pending_action=None):
        confirmation_result = self._maybe_execute_pending_action(
            user_message,
            pending_action,
            user_context=user_context,
        )
        if confirmation_result is not None:
            self._store_conversation_turn(conversation_id, user_message, confirmation_result["answer"])

            def confirmed_generator():
                yield {
                    "type": "done",
                    "answer": confirmation_result["answer"],
                    "source": confirmation_result["source"],
                    "route": confirmation_result["route"],
                    "recommendations": confirmation_result.get("recommendations"),
                    "pending_action": confirmation_result.get("pending_action"),
                }

            return {
                "source": confirmation_result["source"],
                "route": confirmation_result["route"],
            }, confirmed_generator()

        skill_route = self.skill_service.resolve(user_message, user_context=user_context)
        system_prompt = self._build_system_prompt(user_context, skill_route)
        tools = self.tool_service.get_tool_definitions(
            skill_route.tool_names,
            user_context=user_context,
        )
        route_payload = self._serialize_route(skill_route)
        messages = self._build_conversation_messages(conversation_id, user_message)
        source = "anthropic+tools" if tools else "anthropic"
        recommendation_state = self._new_recommendation_state()
        latest_pending_action = None

        def generator():
            nonlocal latest_pending_action
            yield {
                "type": "status",
                "phase": "thinking",
                "label": "正在思考",
            }

            for _ in range(self.config.tool_call_max_steps()):
                final_response = None
                for event in self.model_client.stream_message(
                    messages=messages,
                    tools=tools,
                    system_prompt=system_prompt,
                ):
                    if event.get("type") == "text_delta":
                        text = event.get("text") or ""
                        if text:
                            yield {"type": "chunk", "content": text}
                    elif event.get("type") == "final_response":
                        final_response = event.get("response")

                if final_response is None:
                    raise ValueError("Model stream ended without final response.")

                if final_response.stop_reason != "tool_use":
                    answer = self._extract_text(final_response) or "No displayable content was returned."
                    self._store_conversation_turn(conversation_id, user_message, answer)
                    yield {
                        "type": "done",
                        "answer": answer,
                        "source": source,
                        "route": route_payload,
                        "recommendations": self._finalize_recommendation_state(
                            recommendation_state,
                            user_message=user_message,
                            skill_route=skill_route,
                        ),
                        "pending_action": latest_pending_action,
                    }
                    return

                tool_turn, tool_events, recommendation_updates, current_pending_action = self._build_tool_turn(
                    final_response,
                    user_context=user_context,
                )
                for update in recommendation_updates:
                    self._merge_recommendation_state(recommendation_state, update)
                if current_pending_action:
                    latest_pending_action = current_pending_action
                for tool_event in tool_events:
                    yield tool_event
                yield {
                    "type": "status",
                    "phase": "thinking",
                    "label": "正在整理结果",
                }
                messages.extend(tool_turn)

            yield {
                "type": "done",
                "answer": "Tool call limit reached. Please narrow the request and try again.",
                "source": "service-error",
                "route": route_payload,
                "recommendations": self._finalize_recommendation_state(
                    recommendation_state,
                    user_message=user_message,
                    skill_route=skill_route,
                ),
                "pending_action": latest_pending_action,
            }

        return {
            "source": source,
            "route": route_payload,
        }, generator()

    def route(self, user_message, user_context=None):
        return self._serialize_route(
            self.skill_service.resolve(user_message, user_context=user_context)
        )

    def list_skills(self):
        return self.skill_service.describe()

    @staticmethod
    def _extract_pending_action(result):
        if not isinstance(result, dict):
            return None
        payload = result.get("result")
        if not isinstance(payload, dict):
            return None
        if payload.get("status") != "pending_confirmation":
            return None
        pending_action = payload.get("pending_action")
        return pending_action if isinstance(pending_action, dict) else None

    def _build_conversation_messages(self, conversation_id, user_message):
        messages = []
        if self.conversation_store and conversation_id:
            messages.extend(self.conversation_store.get_messages(conversation_id))
        messages.append({"role": "user", "content": user_message})
        return messages

    def _store_conversation_turn(self, conversation_id, user_message, answer):
        if not self.conversation_store or not conversation_id:
            return
        self.conversation_store.append_messages(
            conversation_id,
            [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": answer},
            ],
        )

    def _maybe_execute_pending_action(self, user_message, pending_action, user_context=None):
        if not isinstance(pending_action, dict):
            return None

        confirmation_text = self._stringify(pending_action.get("confirmation_text"))
        token = self._stringify(pending_action.get("token"))
        tool_name = self._stringify(pending_action.get("tool"))
        arguments = pending_action.get("arguments") if isinstance(pending_action.get("arguments"), dict) else {}
        normalized_message = self._stringify(user_message)

        if not token or not tool_name or not confirmation_text:
            return None
        if normalized_message != confirmation_text:
            return None

        execution_input = dict(arguments)
        execution_input["confirmation_token"] = token
        result = self.tool_service.execute(tool_name, execution_input, user_context=user_context)

        if result.get("ok"):
            answer = f"已确认并执行：{confirmation_text}"
        else:
            answer = f"确认执行失败：{result.get('error') or '未知错误'}"

        return {
            "answer": answer,
            "source": "action-confirmation",
            "route": {"skills": [], "tools": [tool_name], "systemPrompt": None},
            "recommendations": None,
            "pending_action": None,
            "tool_result": result,
        }

    def _build_tool_turn(self, response, user_context=None):
        assistant_content = []
        tool_results = []
        tool_events = []
        recommendation_updates = []
        pending_action = None

        for block in response.content:
            if getattr(block, "type", "") == "text":
                assistant_content.append({"type": "text", "text": block.text})
                continue

            if getattr(block, "type", "") != "tool_use":
                continue

            assistant_content.append(
                {
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                }
            )
            tool_events.append(
                {
                    "type": "tool_start",
                    "tool": block.name,
                    "input": block.input,
                    "label": self._tool_label(block.name),
                }
            )
            result = self.tool_service.execute(block.name, block.input, user_context=user_context)
            pending_action = self._extract_pending_action(result) or pending_action
            recommendation_update = self._build_recommendation_update(block.name, result)
            if recommendation_update:
                recommendation_updates.append(recommendation_update)
            tool_events.append(
                {
                    "type": "tool_end",
                    "tool": block.name,
                    "label": self._tool_label(block.name),
                    "status": "error" if isinstance(result, dict) and result.get("error") else "ok",
                    "summary": self._summarize_tool_result(result),
                }
            )
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

        return (
            [
                {"role": "assistant", "content": assistant_content},
                {"role": "user", "content": tool_results},
            ],
            tool_events,
            recommendation_updates,
            pending_action,
        )

    def _build_system_prompt(self, user_context, skill_route):
        prompt = self.default_system_prompt.strip()
        if user_context:
            parts = [
                f"id={user_context.get('id')}",
                f"username={user_context.get('username')}",
                f"role={user_context.get('role')}",
            ]
            if user_context.get("merchantId") is not None:
                parts.append(f"merchantId={user_context.get('merchantId')}")
            prompt += f"\nCurrent user: {', '.join(part for part in parts if part)}."
        else:
            prompt += "\nCurrent user is anonymous; only public or non-identity-bound data should be used."

        prompt += "\nAlways answer in Chinese."
        prompt += "\nHandle property, room type, booking, payment, review, notification, coupon, merchant and user questions."
        prompt += "\nFor concrete platform data such as status, price, score, time, count or records, prefer backend tools."
        prompt += "\nUse write tools only when the user explicitly asks to execute an action."
        prompt += "\nDo not fabricate booking status, payment results, prices, review counts or notification counts."
        prompt += f"\n{self.ACTION_CONFIRMATION_PROMPT}"

        if skill_route.active_skill_names:
            prompt += f"\nMatched skills: {', '.join(skill_route.active_skill_names)}."
        if skill_route.system_prompt:
            prompt += f"\n{skill_route.system_prompt}"
        return prompt

    @staticmethod
    def _serialize_route(skill_route):
        return {
            "skills": list(skill_route.active_skill_names),
            "tools": list(skill_route.tool_names),
            "systemPrompt": skill_route.system_prompt,
        }

    @staticmethod
    def _new_recommendation_state():
        return {
            "title": "",
            "subtitle": "",
            "cards_by_key": {},
            "order": [],
        }

    def _merge_recommendation_state(self, state, update):
        if not update:
            return

        if update.get("reset"):
            state["cards_by_key"].clear()
            state["order"].clear()
            state["title"] = update.get("title") or state["title"]
            state["subtitle"] = update.get("subtitle") or ""
        else:
            if not state["title"] and update.get("title"):
                state["title"] = update.get("title")
            if not state["subtitle"] and update.get("subtitle"):
                state["subtitle"] = update.get("subtitle")

        for card in update.get("cards") or []:
            key = self._recommendation_card_key(card)
            if not key:
                continue
            if key in state["cards_by_key"]:
                state["cards_by_key"][key] = self._merge_recommendation_card(
                    state["cards_by_key"][key],
                    card,
                )
                continue
            state["cards_by_key"][key] = card
            state["order"].append(key)

    def _finalize_recommendation_state(self, state, user_message="", skill_route=None):
        cards = [
            state["cards_by_key"][key]
            for key in state["order"]
            if key in state["cards_by_key"]
        ]
        if not cards:
            return None
        if not self._should_present_recommendations(user_message, skill_route):
            return None
        return {
            "title": state.get("title") or "酒店推荐",
            "subtitle": state.get("subtitle") or "",
            "count": len(cards),
            "cards": cards[:6],
        }

    def _build_recommendation_update(self, tool_name, tool_result):
        if tool_name not in self.PROPERTY_TOOLS:
            return None
        if not isinstance(tool_result, dict) or not tool_result.get("ok"):
            return None

        payload = tool_result.get("result") or {}
        query = payload.get("query") or {}
        cards = []
        reset = tool_name in self.PROPERTY_COLLECTION_TOOLS

        if tool_name in self.PROPERTY_COLLECTION_TOOLS:
            for item in payload.get("items") or []:
                card = self._build_property_card(item)
                if card:
                    cards.append(card)
        else:
            card = self._build_property_card(payload.get("item"))
            if card:
                cards.append(card)

        if not cards:
            return None

        return {
            "reset": reset,
            "title": self._recommendation_title(tool_name, len(cards)),
            "subtitle": self._recommendation_subtitle(query),
            "cards": cards,
        }

    def _should_present_recommendations(self, user_message, skill_route=None):
        active_skill_names = tuple(getattr(skill_route, "active_skill_names", ()) or ())
        if "property_support" not in active_skill_names:
            return False

        normalized = self._stringify(user_message).lower()
        if not normalized:
            return False

        return any(hint in normalized for hint in self.RECOMMENDATION_HINTS)

    @staticmethod
    def _recommendation_title(tool_name, card_count):
        if tool_name == "get_top_properties":
            return f"热门酒店推荐 ({card_count})"
        if tool_name == "get_property_detail":
            return "酒店详情"
        return f"为你找到的酒店推荐 ({card_count})"

    def _recommendation_subtitle(self, query):
        if not isinstance(query, dict):
            return ""

        parts = []
        city = self._stringify(query.get("city"))
        district = self._stringify(query.get("district"))
        keyword = self._stringify(query.get("keyword"))
        min_price = self._safe_number(query.get("minPrice") or query.get("min_price"))
        max_price = self._safe_number(query.get("maxPrice") or query.get("max_price"))
        min_rating = self._safe_number(query.get("minRating") or query.get("min_rating"))
        facilities = self._normalize_text_list(query.get("facilities"))[:3]

        if city:
            parts.append(city)
        if district:
            parts.append(district)
        if min_price is not None or max_price is not None:
            if min_price is not None and max_price is not None:
                parts.append(f"{int(min_price)}-{int(max_price)} 元")
            elif min_price is not None:
                parts.append(f"{int(min_price)} 元以上")
            else:
                parts.append(f"{int(max_price)} 元以下")
        if min_rating is not None:
            parts.append(f"{min_rating:.1f} 分以上")
        if query.get("featured"):
            parts.append("精选优先")
        parts.extend(facilities)
        if keyword and keyword not in parts:
            parts.append(keyword)
        return " · ".join(parts)

    def _build_property_card(self, item):
        if not isinstance(item, dict):
            return None

        property_id = self._stringify(
            self._first_value(item, "id", "propertyId", "property.id")
        )
        name = self._stringify(
            self._first_value(
                item,
                "name",
                "title",
                "propertyName",
                "property.name",
                "property.title",
            )
        )
        if not name and not property_id:
            return None

        city = self._stringify(self._first_value(item, "city", "property.city"))
        district = self._stringify(
            self._first_value(
                item,
                "district",
                "area",
                "region",
                "property.district",
                "location.district",
            )
        )
        address = self._stringify(
            self._first_value(
                item,
                "address",
                "property.address",
                "location.address",
                "fullAddress",
            )
        )
        hotel_type = self._stringify(
            self._first_value(
                item,
                "type",
                "category",
                "propertyType",
                "property.type",
                "property.category",
            )
        )
        featured = bool(
            self._first_value(item, "featured", "isFeatured", "property.featured")
        )
        rating = self._safe_number(
            self._first_value(
                item,
                "rating",
                "score",
                "avgRating",
                "property.rating",
            )
        )
        review_count = self._safe_number(
            self._first_value(
                item,
                "reviewCount",
                "reviews",
                "commentCount",
                "property.reviewCount",
            )
        )
        price_value = self._extract_price_value(item)
        price_label = self._format_price_label(price_value)
        summary = self._stringify(
            self._first_value(
                item,
                "summary",
                "description",
                "intro",
                "highlight",
                "property.summary",
                "property.description",
            )
        )
        highlights = self._collect_highlights(item, hotel_type=hotel_type, featured=featured)
        image_url = self._extract_image_url(item)
        detail_url = self._stringify(
            self._first_value(
                item,
                "detailUrl",
                "detailURL",
                "detailLink",
                "url",
                "link",
                "property.detailUrl",
                "property.url",
            )
        )
        if not detail_url and property_id:
            detail_url = self._build_property_detail_url(property_id)
        booking_url = self._stringify(
            self._first_value(
                item,
                "bookingUrl",
                "reserveUrl",
                "reservationUrl",
                "property.bookingUrl",
            )
        )
        latitude = self._safe_number(
            self._first_value(item, "latitude", "property.latitude", "location.latitude")
        )
        longitude = self._safe_number(
            self._first_value(item, "longitude", "property.longitude", "location.longitude")
        )
        map_url = self._build_map_url(
            name=name or property_id or "酒店",
            city=city,
            address=address,
            latitude=latitude,
            longitude=longitude,
        )

        # Extract room types if present (for detail views)
        room_types = self._extract_room_types(item)

        return {
            "id": property_id or name,
            "name": name or f"房源 {property_id}",
            "location": " · ".join(part for part in (city, district) if part),
            "address": address or "",
            "type": hotel_type or "",
            "featured": featured,
            "rating": f"{rating:.1f}" if rating is not None else "",
            "reviewCount": int(review_count) if review_count is not None else None,
            "priceValue": price_value,
            "priceLabel": price_label,
            "summary": summary or "",
            "highlights": highlights[:6],
            "roomTypes": room_types[:3] if room_types else [],
            "imageUrl": image_url or "",
            "detailUrl": detail_url or "",
            "bookingUrl": booking_url or "",
            "mapUrl": map_url or "",
            "followUpPrompt": f"请详细介绍一下{name or '这家酒店'}的房型、入住规则和预订建议",
        }

    def _build_property_detail_url(self, property_id):
        base_url = self._stringify(self.config.frontend_base_url()) if self.config else ""
        normalized_base = (base_url or "").rstrip("/")
        if not normalized_base:
            return f"/property/{property_id}"
        return f"{normalized_base}/property/{property_id}"

    def _collect_highlights(self, item, hotel_type="", featured=False):
        values = []
        if featured:
            values.append("精选推荐")
        if hotel_type:
            values.append(hotel_type)

        for field_name in (
            "facilities",
            "facilityTags",
            "amenities",
            "highlights",
            "tags",
            "serviceTags",
            "property.facilities",
            "property.amenities",
        ):
            values.extend(self._normalize_text_list(self._first_value(item, field_name)))

        breakfast_included = self._first_value(
            item,
            "breakfastIncluded",
            "property.breakfastIncluded",
        )
        if breakfast_included is True:
            values.append("含早餐")

        bed_type = self._stringify(
            self._first_value(item, "bedType", "roomType", "property.bedType")
        )
        if bed_type:
            values.append(bed_type)

        return self._dedupe(values)

    def _extract_price_value(self, item):
        direct_value = self._first_value(
            item,
            "minPrice",
            "lowestPrice",
            "startingPrice",
            "price",
            "property.minPrice",
        )
        if isinstance(direct_value, dict):
            return self._safe_number(
                self._first_value(direct_value, "amount", "value", "price")
            )
        return self._safe_number(direct_value)

    def _extract_image_url(self, item):
        image_value = self._first_value(
            item,
            "coverImage",
            "cover",
            "image",
            "thumbnail",
            "imageUrl",
            "coverUrl",
            "property.coverImage",
            "property.imageUrl",
            "images.0",
            "photos.0",
        )
        if isinstance(image_value, dict):
            image_value = self._first_value(image_value, "url", "src", "imageUrl")
        return self._stringify(image_value)

    def _extract_room_types(self, item):
        """Extract room type information from detail response"""
        room_types_data = self._first_value(item, "roomTypes", "room_types", "rooms")
        if not isinstance(room_types_data, list):
            return []

        result = []
        for room in room_types_data:
            if not isinstance(room, dict):
                continue

            room_name = self._stringify(
                self._first_value(room, "typeName", "name", "title", "roomName")
            )
            if not room_name:
                continue

            room_price = self._safe_number(
                self._first_value(room, "basePrice", "price", "pricePerNight")
            )
            room_size = self._safe_number(
                self._first_value(room, "roomSize", "size", "area")
            )
            bed_type = self._stringify(
                self._first_value(room, "bedType", "bed")
            )
            max_occupancy = self._safe_number(
                self._first_value(room, "maxOccupancy", "capacity", "guests")
            )

            room_info = {
                "name": room_name,
                "price": f"¥{int(room_price)}/晚" if room_price else "",
                "size": f"{room_size}㎡" if room_size else "",
                "bedType": bed_type or "",
                "maxOccupancy": f"最多{int(max_occupancy)}人" if max_occupancy else "",
            }
            result.append(room_info)

        return result

    @staticmethod
    def _build_map_url(name, city="", address="", latitude=None, longitude=None):
        if latitude is not None and longitude is not None:
            return (
                "https://uri.amap.com/marker?position="
                f"{longitude},{latitude}&name={quote(str(name))}"
            )

        keyword = " ".join(part for part in (city, address or name) if part)
        if not keyword:
            return ""
        return f"https://uri.amap.com/search?keyword={quote(keyword)}"

    @staticmethod
    def _format_price_label(price_value):
        if price_value is None:
            return ""
        if float(price_value).is_integer():
            return f"¥{int(price_value)} 起/晚"
        return f"¥{price_value:.2f} 起/晚"

    @staticmethod
    def _recommendation_card_key(card):
        return str(card.get("id") or card.get("detailUrl") or card.get("name") or "")

    @classmethod
    def _merge_recommendation_card(cls, current, incoming):
        merged = dict(current)
        for key, value in incoming.items():
            if key == "highlights":
                merged[key] = cls._dedupe((current.get(key) or []) + (value or []))
                continue
            if key == "summary":
                current_summary = cls._stringify(current.get(key))
                incoming_summary = cls._stringify(value)
                if len(incoming_summary) > len(current_summary):
                    merged[key] = incoming_summary
                continue
            if cls._is_present(value) and not cls._is_present(current.get(key)):
                merged[key] = value
        return merged

    @staticmethod
    def _first_value(payload, *paths):
        for path in paths:
            value = ChatService._resolve_path(payload, path)
            if ChatService._is_present(value):
                return value
        return None

    @staticmethod
    def _resolve_path(payload, path):
        current = payload
        for chunk in str(path).split("."):
            if isinstance(current, list):
                if not chunk.isdigit():
                    return None
                index = int(chunk)
                if index >= len(current):
                    return None
                current = current[index]
                continue
            if not isinstance(current, dict):
                return None
            if chunk not in current:
                return None
            current = current.get(chunk)
        return current

    @staticmethod
    def _normalize_text_list(value):
        if value is None:
            return []
        if isinstance(value, str):
            if not value.strip():
                return []
            normalized = (
                value.replace("｜", "|")
                .replace("、", "|")
                .replace("/", "|")
                .replace(",", "|")
            )
            return [part.strip() for part in normalized.split("|") if part.strip()]
        if isinstance(value, list):
            parts = []
            for item in value:
                if isinstance(item, dict):
                    text = ChatService._stringify(
                        ChatService._first_value(item, "name", "label", "title", "value")
                    )
                    if text:
                        parts.append(text)
                    continue
                text = ChatService._stringify(item)
                if text:
                    parts.append(text)
            return parts
        if isinstance(value, dict):
            text = ChatService._stringify(
                ChatService._first_value(value, "name", "label", "title", "value")
            )
            return [text] if text else []
        text = ChatService._stringify(value)
        return [text] if text else []

    @staticmethod
    def _dedupe(values):
        result = []
        seen = set()
        for value in values:
            text = ChatService._stringify(value)
            if not text:
                continue
            lowered = text.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            result.append(text)
        return result

    @staticmethod
    def _safe_number(value):
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _stringify(value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()

    @staticmethod
    def _is_present(value):
        return value not in (None, "", [], {})

    @staticmethod
    def _extract_text(response):
        parts = []
        for block in response.content:
            if getattr(block, "type", "") == "text" and getattr(block, "text", ""):
                parts.append(block.text)
        return "\n".join(parts).strip()

    @staticmethod
    def _tool_label(tool_name):
        labels = {
            "tavily_search": "正在检索网页信息",
            "get_weather": "正在查询天气",
        }
        return labels.get(tool_name, f"正在调用 {tool_name}")

    @staticmethod
    def _summarize_tool_result(result):
        if not isinstance(result, dict):
            return "工具已返回结果"
        if result.get("error"):
            return str(result.get("error"))
        if result.get("answer"):
            return str(result.get("answer"))[:80]
        if result.get("location") and result.get("description"):
            return f"{result.get('location')}，{result.get('description')}"
        if result.get("items") is not None:
            return f"返回 {len(result.get('items') or [])} 条结果"
        if result.get("results"):
            return f"返回 {len(result.get('results') or [])} 条结果"
        return "工具已返回结果"
