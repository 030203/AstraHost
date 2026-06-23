# RoomOS 后端接口与 SFT 工具构造参考

本文档汇总 RoomOS 当前后端接口，目标是辅助构造带工具调用的 SFT 数据集。

采集范围：

- Java 业务后端：`backend/src/main/java/com/booking/system/controller`
- Python AI 服务：`ai-service/app.py`
- AI 服务内部工具封装：`ai-service/services/backend_api_service.py`、`ai-service/services/tool_service.py`
- 前端调用入口：`frontend/src/api/index.js`、`frontend/src/api/auth.js`

## 1. 服务入口

| 服务 | 默认地址 | 说明 |
| --- | --- | --- |
| 业务后端 | `http://localhost:8080/api` | Spring Boot，`server.servlet.context-path=/api` |
| 网关 | `http://localhost:8088` | `/api/**` 转发到业务后端，`/ai-api/**` 转发到 AI 服务并去掉 `/ai-api` 前缀 |
| AI 服务 | `http://localhost:5001` | Flask，提供 `/chat`、`/skills` 等接口 |
| 前端业务 baseURL | `/api` | Axios 默认业务接口前缀 |
| 前端 AI baseURL | `/ai-api` | Axios 默认 AI 接口前缀 |

前端会把登录返回的 `token` 放入请求头：

```http
Authorization: Bearer dev-token-{userId}
```

当前业务后端控制器没有显式鉴权拦截逻辑；AI 服务工具层会根据 `userContext` 做角色访问约束。

## 2. SFT 构造建议

建议将 AI 服务中已经封装的后端工具作为 SFT 的 function tools，而不是直接把 HTTP 接口暴露给模型。原因：

- 工具名和参数名已经稳定为 snake_case。
- 工具返回值带有 `source`、`query`、`item/items` 等包装字段，更适合训练模型基于证据回答。
- 工具层已经处理了部分角色约束，例如普通用户只能看自己的订单，商家只能看自己的房源/订单。

推荐 system prompt 示例：

```json
{
  "role": "system",
  "content": "你是 RoomOS/FindMyBed 民宿预订平台的中文客服助手。涉及房源、订单、支付、评价、通知、优惠券、商家或用户的具体数据时，必须优先调用后端工具；不要编造订单状态、价格、支付结果、评分或通知数量。只有当用户明确要求执行取消、入住、离店、标记已读、回复评价等会改变状态的动作时，才调用 action 工具。",
  "tools": "[{\"type\":\"function\",\"function\":{\"name\":\"get_booking_by_number\",\"description\":\"按订单号查询订单详情\",\"parameters\":{\"type\":\"object\",\"properties\":{\"booking_number\":{\"type\":\"string\",\"description\":\"订单号\"}},\"required\":[\"booking_number\"]}}}]"
}
```

推荐 assistant tool call 示例：

```json
{
  "role": "assistant",
  "content": "",
  "tool_calls": "[{\"function\":{\"name\":\"get_booking_by_number\",\"arguments\":{\"booking_number\":\"BK202605080001\"}}}]"
}
```

工具返回后，建议在训练集中追加 tool 结果，再让 assistant 基于结果生成最终中文回复：

```json
{
  "role": "tool",
  "name": "get_booking_by_number",
  "content": "{\"ok\":true,\"tool\":\"get_booking_by_number\",\"result\":{\"item\":{\"bookingNumber\":\"BK202605080001\",\"status\":\"CONFIRMED\",\"paymentStatus\":\"PAID\"},\"source\":\"booking-service:/bookings/number/BK202605080001\"}}"
}
```

## 3. 角色与权限

| 角色 | 说明 |
| --- | --- |
| `USER` | 普通用户 |
| `MERCHANT` | 商家/房东 |
| `ADMIN` | 管理员 |
| anonymous | 未登录用户，仅建议使用公开查询类工具 |

AI 服务工具层的主要约束：

- `USER` 查询订单、支付、通知、用户信息时会收敛到当前用户。
- `MERCHANT` 查询订单、支付、评价、优惠券时会收敛到当前商家或其房源。
- `ADMIN` 可使用管理类列表工具，例如 `list_users`、`list_merchants`。
- action 工具只应在用户明确提出执行动作时调用。

`userContext` 示例：

```json
{
  "id": 12,
  "username": "alice",
  "role": "USER"
}
```

```json
{
  "id": 7,
  "username": "host_01",
  "role": "MERCHANT",
  "merchantId": 3
}
```

## 4. AI 服务接口

这些接口属于聊天服务，不是业务数据工具本身。

| 方法 | 路径 | Body / Params | 返回 | 用途 |
| --- | --- | --- | --- | --- |
| `GET` | `/health` | 无 | `{"status":"ok"}` | 健康检查 |
| `GET` | `/suggestions` | 无 | 字符串数组 | 默认问题建议 |
| `GET` | `/skills` | 无 | skill 列表 | 查看技能路由配置 |
| `POST` | `/skills/route` | `message`, `userContext?` | 命中的 skills/tools | 调试技能路由 |
| `POST` | `/chat` | `message`, `conversationId?`, `userContext?` | `conversationId`, `answer`, `source`, `route`, `requestId` | 同步聊天 |
| `POST` | `/chat/stream` | `message`, `conversationId?`, `userContext?` | SSE: `meta/chunk/done/error` | 流式聊天 |

`POST /chat` 请求示例：

```json
{
  "conversationId": "conv-001",
  "message": "帮我查一下订单 BK202605080001 的状态",
  "userContext": {
    "id": 12,
    "username": "alice",
    "role": "USER"
  }
}
```

## 5. 推荐用于 SFT 的后端工具清单

下面工具来自 `ai-service/services/tool_service.py` 和 `ai-service/services/backend_api_service.py`。参数名应按表中 snake_case 使用。

### 5.1 房源与房型工具

#### `list_properties`

查询房源列表。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /properties` |
| mode | `read` |
| 角色 | 公开 |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `merchant_id` | integer | 否 | 商家 ID |
| `city` | string | 否 | 城市 |
| `status` | string | 否 | 房源状态：`DRAFT`、`PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED` |
| `featured` | boolean | 否 | 是否仅查询精选房源 |

#### `search_properties`

搜索房源，适合城市、区域、价格、评分、设施、附近房源等问题。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /properties/search` |
| mode | `read` |
| 角色 | 公开 |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `keyword` | string | 否 | 关键词，例如“海景”“亲子”“地铁口” |
| `city` | string | 否 | 城市 |
| `district` | string | 否 | 区县 |
| `min_price` | number | 否 | 最低价格 |
| `max_price` | number | 否 | 最高价格 |
| `min_rating` | number | 否 | 最低评分 |
| `featured` | boolean | 否 | 是否仅看精选 |
| `facilities` | array[string] | 否 | 设施列表 |
| `latitude` | number | 否 | 纬度 |
| `longitude` | number | 否 | 经度 |
| `distance_km` | number | 否 | 距离半径，单位公里 |
| `page` | integer | 否 | 页码，默认 1 |
| `size` | integer | 否 | 每页数量，默认 10，工具层最多 20 |

返回核心字段：

```json
{
  "query": {},
  "items": [
    {
      "id": 1,
      "propertyName": "南山海景民宿",
      "propertyType": "HOMESTAY",
      "city": "深圳",
      "district": "南山区",
      "priceRangeMin": 399,
      "priceRangeMax": 899,
      "rating": 4.8,
      "featured": true,
      "facilities": ["wifi", "parking"],
      "distanceKm": 1.2
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10,
  "used_elasticsearch": true,
  "source": "booking-service:/properties/search"
}
```

#### `get_property_detail`

查询房源详情和房型信息。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /properties/{property_id}/detail` |
| mode | `read` |
| 角色 | 公开 |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `property_id` | integer | 是 | 房源 ID |

#### `get_top_properties`

查询热门房源排行榜。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /properties/top?limit={limit}` |
| mode | `read` |
| 角色 | 公开 |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `limit` | integer | 否 | 返回数量，默认 5，工具层最多 20 |

#### `list_room_types`

查询房型列表。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /room-types` |
| mode | `read` |
| 角色 | 公开 |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `property_id` | integer | 否 | 房源 ID |

#### `get_room_type_detail`

查询单个房型详情。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /room-types/{room_type_id}` |
| mode | `read` |
| 角色 | 公开 |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `room_type_id` | integer | 是 | 房型 ID |

#### `get_active_room_types`

查询某个房源当前可用的房型。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /room-types/property/{property_id}/active` |
| mode | `read` |
| 角色 | 公开 |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `property_id` | integer | 是 | 房源 ID |

### 5.2 订单工具

#### `list_bookings`

查询订单列表。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /bookings` |
| mode | `read` |
| 角色 | `USER`、`MERCHANT`、`ADMIN` |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | integer | 否 | 用户 ID；普通用户会被工具层收敛为当前用户 |
| `property_id` | integer | 否 | 房源 ID |
| `merchant_id` | integer | 否 | 商家 ID；商家会被工具层收敛为当前商家 |
| `status` | string | 否 | 订单状态：`PENDING`、`CONFIRMED`、`CHECKED_IN`、`CHECKED_OUT`、`CANCELLED`、`REFUNDED` |

#### `get_booking_detail`

按订单 ID 查询详情。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /bookings/{booking_id}` |
| mode | `read` |
| 角色 | `USER`、`MERCHANT`、`ADMIN` |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `booking_id` | integer | 是 | 订单 ID |

#### `get_booking_by_number`

按订单号查询详情。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /bookings/number/{booking_number}` |
| mode | `read` |
| 角色 | `USER`、`MERCHANT`、`ADMIN` |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `booking_number` | string | 是 | 订单号 |

#### `cancel_booking`

取消订单，会修改后端状态。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `POST /bookings/{booking_id}/cancel`，text body 为取消原因 |
| mode | `action` |
| 角色 | `USER`、`MERCHANT`、`ADMIN` |
| 调用条件 | 只有用户明确要求取消订单时调用 |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `booking_id` | integer | 是 | 订单 ID |
| `reason` | string | 是 | 取消原因 |

#### `check_in_booking`

办理入住，会修改后端状态。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `POST /bookings/{booking_id}/check-in` |
| mode | `action` |
| 角色 | `USER`、`MERCHANT`、`ADMIN` |
| 调用条件 | 只有用户明确要求办理入住时调用 |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `booking_id` | integer | 是 | 订单 ID |

#### `check_out_booking`

办理离店，会修改后端状态。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `POST /bookings/{booking_id}/check-out` |
| mode | `action` |
| 角色 | `USER`、`MERCHANT`、`ADMIN` |
| 调用条件 | 只有用户明确要求办理离店时调用 |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `booking_id` | integer | 是 | 订单 ID |

### 5.3 支付工具

#### `list_payments`

查询支付记录列表。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /payments` |
| mode | `read` |
| 角色 | `USER`、`MERCHANT`、`ADMIN` |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `booking_id` | integer | 否 | 订单 ID |
| `user_id` | integer | 否 | 用户 ID；普通用户会被收敛为当前用户 |
| `merchant_id` | integer | 否 | 商家 ID；商家会被收敛为当前商家 |
| `status` | string | 否 | 支付状态：`PENDING`、`SUCCESS`、`FAILED`、`CANCELLED` |

#### `get_payment_detail`

按支付 ID 查询详情。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /payments/{payment_id}` |
| mode | `read` |
| 角色 | `USER`、`MERCHANT`、`ADMIN` |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `payment_id` | integer | 是 | 支付 ID |

#### `get_payment_by_number`

按支付单号查询详情。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /payments/number/{payment_number}` |
| mode | `read` |
| 角色 | `USER`、`MERCHANT`、`ADMIN` |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `payment_number` | string | 是 | 支付单号 |

### 5.4 评价工具

#### `list_reviews`

查询评价列表。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /reviews` |
| mode | `read` |
| 角色 | 公开；商家会被限制到自己的房源 |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `property_id` | integer | 否 | 房源 ID |
| `user_id` | integer | 否 | 用户 ID |
| `status` | string | 否 | 评价状态：`PENDING`、`APPROVED`、`REJECTED`、`HIDDEN` |

#### `get_review_detail`

按评价 ID 查询详情。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /reviews/{review_id}` |
| mode | `read` |
| 角色 | 公开；商家会被限制到自己的房源 |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `review_id` | integer | 是 | 评价 ID |

#### `get_review_by_booking`

按订单 ID 查询对应评价。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /reviews/booking/{booking_id}` |
| mode | `read` |
| 角色 | `USER`、`MERCHANT`、`ADMIN` |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `booking_id` | integer | 是 | 订单 ID |

#### `reply_review`

回复评价，会修改后端状态。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `POST /reviews/{review_id}/reply`，text body 为回复内容 |
| mode | `action` |
| 角色 | `MERCHANT`、`ADMIN` |
| 调用条件 | 只有用户明确要求回复评价时调用 |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `review_id` | integer | 是 | 评价 ID |
| `reply_content` | string | 是 | 回复内容 |

### 5.5 通知工具

#### `list_notifications`

查询通知列表。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /notifications` |
| mode | `read` |
| 角色 | `USER`、`MERCHANT`、`ADMIN` |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | integer | 否 | 用户 ID；普通用户和商家会被收敛为当前用户 |
| `unread_only` | boolean | 否 | 是否只看未读通知，默认 false |

#### `get_unread_notification_count`

查询未读通知数量。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /notifications/unread-count?userId={user_id}` |
| mode | `read` |
| 角色 | `USER`、`MERCHANT`、`ADMIN` |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | integer | 是 | 用户 ID；普通用户和商家会被收敛为当前用户 |

#### `mark_notification_read`

将单条通知标记为已读，会修改后端状态。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `POST /notifications/{notification_id}/read` |
| mode | `action` |
| 角色 | `USER`、`MERCHANT`、`ADMIN` |
| 调用条件 | 只有用户明确要求标记已读时调用 |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `notification_id` | integer | 是 | 通知 ID |

#### `mark_all_notifications_read`

将某个用户的通知全部标记为已读，会修改后端状态。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `POST /notifications/read-all?userId={user_id}` |
| mode | `action` |
| 角色 | `USER`、`MERCHANT`、`ADMIN` |
| 调用条件 | 只有用户明确要求全部标记已读时调用 |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | integer | 是 | 用户 ID；普通用户和商家会被收敛为当前用户 |

### 5.6 商家工具

#### `list_merchants`

查询商家列表。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /merchants` |
| mode | `read` |
| 角色 | `ADMIN` |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `status` | string | 否 | 商家状态：`PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED` |
| `city` | string | 否 | 城市 |

#### `get_merchant_detail`

按商家 ID 查询详情。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /merchants/{merchant_id}` |
| mode | `read` |
| 角色 | `MERCHANT`、`ADMIN` |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `merchant_id` | integer | 是 | 商家 ID；商家角色会被收敛为当前商家 |

#### `get_merchant_by_user`

按用户 ID 查询关联商家信息。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /merchants/user/{user_id}` |
| mode | `read` |
| 角色 | `MERCHANT`、`ADMIN` |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | integer | 是 | 用户 ID；商家角色会被收敛为当前用户 |

### 5.7 用户工具

#### `list_users`

查询用户列表。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /users` |
| mode | `read` |
| 角色 | `ADMIN` |

参数：无。

#### `get_user_detail`

按用户 ID 查询用户详情。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /users/{user_id}` |
| mode | `read` |
| 角色 | `USER`、`MERCHANT`、`ADMIN` |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `user_id` | integer | 是 | 用户 ID；普通用户和商家会被收敛为当前用户 |

### 5.8 优惠券工具

#### `list_coupons`

查询优惠券列表。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /coupons` |
| mode | `read` |
| 角色 | 公开；商家会被限制到当前商家 |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `merchant_id` | integer | 否 | 商家 ID；商家角色会被收敛为当前商家 |
| `status` | string | 否 | 优惠券状态：`ACTIVE`、`INACTIVE`、`EXPIRED` |

#### `get_coupon_detail`

按优惠券 ID 查询详情。

| 属性 | 值 |
| --- | --- |
| REST 来源 | `GET /coupons/{coupon_id}` |
| mode | `read` |
| 角色 | 公开；商家会被限制到当前商家 |

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `coupon_id` | integer | 是 | 优惠券 ID |

### 5.9 外部信息工具

这两个工具不属于业务后端，但 AI 服务默认会注册，可按需加入 SFT。

#### `tavily_search`

搜索实时网页信息。

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `query` | string | 是 | 搜索查询 |

#### `get_weather`

查询城市当前天气。

参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `location` | string | 是 | 城市或目的地名称 |

## 6. 业务 REST 接口总表

如果要训练“HTTP API 调用型”模型，可使用下表作为原始接口参考。实际 SFT 更推荐使用第 5 节的工具层。

### 6.1 Auth

| 方法 | 路径 | 参数 / Body | 返回 | 说明 |
| --- | --- | --- | --- | --- |
| `POST` | `/auth/login` | body: `LoginRequest` | 用户信息、`token`、可选 `merchantId` | 登录 |
| `POST` | `/auth/register` | body: `RegisterRequest` | `id`、`username`、`role`、可选 `merchantId`、`message` | 注册 |

`LoginRequest`：

```json
{
  "username": "alice",
  "password": "123456",
  "role": "USER"
}
```

`RegisterRequest`：

```json
{
  "username": "host_01",
  "password": "123456",
  "email": "host@example.com",
  "phone": "13800138000",
  "role": "MERCHANT",
  "merchantName": "山海民宿",
  "merchantContactName": "张三",
  "merchantContactPhone": "13800138000",
  "merchantContactEmail": "host@example.com",
  "merchantAddress": "深圳市南山区",
  "merchantProvince": "广东省",
  "merchantCity": "深圳市",
  "merchantDistrict": "南山区",
  "businessLicense": "LICENSE001"
}
```

### 6.2 Users

| 方法 | 路径 | 参数 / Body | 返回 | 说明 |
| --- | --- | --- | --- | --- |
| `GET` | `/users` | 无 | `List<User>` | 用户列表 |
| `GET` | `/users/{id}` | path: `id` | `User` | 用户详情 |
| `POST` | `/users` | body: `User` | `User` 或 `{"error":...}` | 创建用户 |
| `PUT` | `/users/{id}` | path: `id`, body: `User` | `User` 或 `{"error":...}` | 更新用户 |
| `DELETE` | `/users/{id}` | path: `id` | 空 | 删除用户 |

`User` 字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | integer | 用户 ID |
| `username` | string | 用户名，3-20 位，仅字母数字下划线 |
| `password` | string | 密码，创建时必填，保存时会 BCrypt 加密 |
| `role` | enum | `USER`、`ADMIN`、`MERCHANT` |
| `email` | string | 邮箱 |
| `phone` | string | 中国大陆手机号格式 |
| `avatar` | string | 头像 |
| `status` | enum | `ACTIVE`、`INACTIVE`、`BANNED` |
| `lastLoginTime` | datetime | 最近登录时间 |
| `lastLoginIp` | string | 最近登录 IP |
| `createdAt` | datetime | 创建时间 |
| `updatedAt` | datetime | 更新时间 |

### 6.3 Merchants

| 方法 | 路径 | 参数 / Body | 返回 | 说明 |
| --- | --- | --- | --- | --- |
| `GET` | `/merchants` | query: `status?`, `city?` | `List<Merchant>` | 商家列表 |
| `GET` | `/merchants/{id}` | path: `id` | `Merchant` | 商家详情 |
| `GET` | `/merchants/user/{userId}` | path: `userId` | `Merchant` | 按用户查询商家 |
| `POST` | `/merchants` | body: `Merchant` | `Merchant` | 创建商家 |
| `PUT` | `/merchants/{id}` | path: `id`, body: `Merchant` | `Merchant` | 更新商家 |
| `POST` | `/merchants/{id}/approve` | query: `auditBy`, `remark?` | `Merchant` | 审核通过 |
| `POST` | `/merchants/{id}/reject` | query: `auditBy`, `remark?` | `Merchant` | 审核拒绝 |
| `DELETE` | `/merchants/{id}` | path: `id` | 空 | 删除商家 |

`Merchant` 主要字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | integer | 商家 ID |
| `user` | object | 关联用户，常用 `{"id": 7}` |
| `merchantName` | string | 商家名称 |
| `businessLicense` | string | 营业执照 |
| `legalPerson` | string | 法人 |
| `contactName` | string | 联系人 |
| `contactPhone` | string | 联系电话 |
| `contactEmail` | string | 联系邮箱 |
| `address` | string | 地址 |
| `province` / `city` / `district` | string | 省市区 |
| `status` | enum | `PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED` |
| `auditRemark` / `auditTime` / `auditBy` | string/datetime/integer | 审核信息 |
| `commissionRate` / `balance` / `rating` | number | 佣金、余额、评分 |
| `totalReviews` | integer | 评论数 |

### 6.4 Properties

| 方法 | 路径 | 参数 / Body | 返回 | 说明 |
| --- | --- | --- | --- | --- |
| `GET` | `/properties` | query: `merchantId?`, `city?`, `status?`, `featured?` | `List<Property>` | 房源列表 |
| `GET` | `/properties/search` | query: `PropertySearchRequest` | `PropertySearchResponse` | 搜索房源 |
| `POST` | `/properties/search/reindex` | 无 | `PropertySearchReindexResponse` | 重建搜索索引 |
| `GET` | `/properties/{id}` | path: `id` | `Property` | 房源详情 |
| `GET` | `/properties/{id}/detail` | path: `id` | `PropertyDetailResponse` | 房源详情 + 房型 |
| `GET` | `/properties/top` | query: `limit=5` | `List<TopPropertyResponse>` | 热门房源 |
| `POST` | `/properties` | body: `Property` | `Property` | 创建房源，状态会置为 `PENDING` |
| `PUT` | `/properties/{id}` | path: `id`, body: `Property` | `Property` | 更新房源 |
| `POST` | `/properties/{id}/approve` | path: `id` | `Property` | 房源审核通过 |
| `POST` | `/properties/{id}/reject` | path: `id` | `Property` | 房源审核拒绝 |
| `DELETE` | `/properties/{id}` | path: `id` | 空 | 删除房源 |

`Property` 主要字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | integer | 房源 ID |
| `merchantId` | integer | 商家 ID，创建时必填 |
| `propertyName` | string | 房源名称 |
| `propertyType` | enum | `HOMESTAY`、`HOTEL`、`APARTMENT`、`VILLA`、`OTHER` |
| `description` | string | 描述 |
| `address` | string | 地址 |
| `province` / `city` / `district` | string | 省市区 |
| `longitude` / `latitude` | number | 经纬度 |
| `checkInTime` / `checkOutTime` | time | 入住/离店时间，默认 `14:00` / `12:00` |
| `totalRooms` / `availableRooms` | integer | 总房间数/可用房间数 |
| `rating` / `totalReviews` | number/integer | 评分/评论数 |
| `priceRangeMin` / `priceRangeMax` | number | 价格区间 |
| `facilities` / `images` / `policies` | string(JSON) | 设施、图片、政策 |
| `status` | enum | `DRAFT`、`PENDING`、`APPROVED`、`REJECTED`、`SUSPENDED` |
| `isFeatured` | boolean | 是否精选 |
| `viewCount` | integer | 浏览量 |

`PropertySearchRequest`：

| 字段 | 类型 |
| --- | --- |
| `keyword` | string |
| `city` | string |
| `district` | string |
| `minPrice` / `maxPrice` | number |
| `minRating` | number |
| `featured` | boolean |
| `facilities` | array[string] |
| `latitude` / `longitude` | number |
| `distanceKm` | number |
| `page` / `size` | integer |

### 6.5 Room Types

| 方法 | 路径 | 参数 / Body | 返回 | 说明 |
| --- | --- | --- | --- | --- |
| `GET` | `/room-types` | query: `propertyId?` | `List<RoomType>` | 房型列表 |
| `GET` | `/room-types/{id}` | path: `id` | `RoomType` | 房型详情 |
| `GET` | `/room-types/property/{propertyId}/active` | path: `propertyId` | `List<RoomType>` | 某房源可用房型 |
| `POST` | `/room-types` | body: `RoomType` | `RoomType` | 创建房型 |
| `PUT` | `/room-types/{id}` | path: `id`, body: `RoomType` | `RoomType` | 更新房型 |
| `DELETE` | `/room-types/{id}` | path: `id` | 空 | 删除房型 |

`RoomType` 主要字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | integer | 房型 ID |
| `property` | object | 关联房源，常用 `{"id": 1}` |
| `propertyId` | integer | 便捷字段，创建/更新时可用 |
| `typeName` | string | 房型名称 |
| `description` | string | 描述 |
| `maxOccupancy` | integer | 最大入住人数，默认 2 |
| `bedType` | string | 床型 |
| `roomSize` | number | 面积 |
| `amenities` / `images` | string(JSON) | 设施、图片 |
| `basePrice` | number | 基础价格 |
| `status` | enum | `ACTIVE`、`INACTIVE` |
| `sortOrder` | integer | 排序 |

创建房型 body 示例：

```json
{
  "propertyId": 1,
  "typeName": "豪华大床房",
  "description": "适合两人入住",
  "maxOccupancy": 2,
  "bedType": "大床",
  "roomSize": 32,
  "amenities": "[\"wifi\",\"空调\"]",
  "images": "[]",
  "basePrice": 399,
  "status": "ACTIVE",
  "sortOrder": 1
}
```

### 6.6 Bookings

| 方法 | 路径 | 参数 / Body | 返回 | 说明 |
| --- | --- | --- | --- | --- |
| `GET` | `/bookings` | query: `userId?`, `propertyId?`, `merchantId?`, `status?` | `List<Booking>` | 订单列表 |
| `GET` | `/bookings/{id}` | path: `id` | `Booking` | 订单详情 |
| `GET` | `/bookings/number/{bookingNumber}` | path: `bookingNumber` | `Booking` | 按订单号查询 |
| `POST` | `/bookings` | body: `Booking` | `Booking` 或 `{"error":...}` | 创建订单 |
| `PUT` | `/bookings/{id}` | path: `id`, body: `Booking` | `Booking` 或 `{"error":...}` | 更新订单 |
| `DELETE` | `/bookings/{id}` | path: `id` | 空 | 删除订单 |
| `POST` | `/bookings/{id}/cancel` | text body: `reason` | `Booking` | 取消订单 |
| `POST` | `/bookings/{id}/check-in` | path: `id` | `Booking` 或 `{"error":...}` | 入住 |
| `POST` | `/bookings/{id}/check-out` | path: `id` | `Booking` 或 `{"error":...}` | 离店 |

`Booking` 主要字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | integer | 订单 ID |
| `bookingNumber` | string | 订单号；创建时可为空，后端自动生成 |
| `user` | object | 关联用户，常用 `{"id": 12}` |
| `property` | object | 关联房源；后端会根据 roomType 自动补齐 |
| `roomType` | object | 关联房型，创建时必须包含 `{"id": 3}` |
| `room` | object | 关联具体房间，可选 |
| `checkInDate` / `checkOutDate` | date | 入住/离店日期，必填 |
| `nights` | integer | 晚数；后端会按日期计算 |
| `numberOfGuests` | integer | 入住人数，默认 1 |
| `adultCount` / `childCount` | integer | 成人/儿童数量 |
| `basePrice` | number | 基础单晚价格；可由房型补齐 |
| `discountAmount` / `couponDiscount` / `serviceFee` | number | 优惠、券优惠、服务费 |
| `coupon` | object | 关联优惠券，可选 |
| `totalAmount` | number | 总金额；后端会计算 |
| `paidAmount` / `refundAmount` | number | 已付/退款金额 |
| `status` | enum | `PENDING`、`CONFIRMED`、`CHECKED_IN`、`CHECKED_OUT`、`CANCELLED`、`REFUNDED` |
| `paymentStatus` | enum | `UNPAID`、`PARTIAL`、`PAID`、`REFUNDED` |
| `cancellationReason` / `cancellationTime` | string/datetime | 取消原因/时间 |
| `specialRequests` | string | 特殊要求 |
| `contactName` / `contactPhone` / `contactEmail` | string | 联系人信息 |
| `checkInTime` / `checkOutTime` | datetime | 实际入住/离店时间 |

创建订单 body 示例：

```json
{
  "user": {"id": 12},
  "roomType": {"id": 3},
  "checkInDate": "2026-05-20",
  "checkOutDate": "2026-05-22",
  "numberOfGuests": 2,
  "adultCount": 2,
  "childCount": 0,
  "specialRequests": "希望安排高楼层",
  "contactName": "李四",
  "contactPhone": "13800138000",
  "contactEmail": "guest@example.com"
}
```

### 6.7 Payments

| 方法 | 路径 | 参数 / Body | 返回 | 说明 |
| --- | --- | --- | --- | --- |
| `GET` | `/payments` | query: `bookingId?`, `userId?`, `merchantId?`, `status?` | `List<Payment>` | 支付列表 |
| `GET` | `/payments/{id}` | path: `id` | `Payment` | 支付详情 |
| `GET` | `/payments/number/{paymentNumber}` | path: `paymentNumber` | `Payment` | 按支付单号查询 |
| `POST` | `/payments` | body: `Payment` | `Payment` | 创建支付记录 |
| `PUT` | `/payments/{id}` | path: `id`, body: `Payment` | `Payment` | 更新支付记录 |
| `POST` | `/payments/{id}/process` | query: `transactionId` | `Payment` | 支付成功处理，同时更新订单支付状态 |
| `DELETE` | `/payments/{id}` | path: `id` | 空 | 删除支付记录 |

`Payment` 主要字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | integer | 支付 ID |
| `paymentNumber` | string | 支付单号；创建时可为空，后端自动生成 |
| `booking` | object | 关联订单，常用 `{"id": 10}` |
| `paymentMethod` | enum | `ALIPAY`、`WECHAT`、`BANK_CARD`、`CASH`、`OTHER` |
| `paymentType` | enum | `DEPOSIT`、`FULL`、`REFUND` |
| `amount` | number | 支付金额 |
| `status` | enum | `PENDING`、`SUCCESS`、`FAILED`、`CANCELLED` |
| `transactionId` | string | 第三方交易号 |
| `paidAt` | datetime | 支付时间 |
| `remark` | string | 备注 |

创建支付 body 示例：

```json
{
  "booking": {"id": 10},
  "paymentMethod": "ALIPAY",
  "paymentType": "FULL",
  "amount": 798,
  "status": "PENDING",
  "remark": "用户发起支付"
}
```

### 6.8 Reviews

| 方法 | 路径 | 参数 / Body | 返回 | 说明 |
| --- | --- | --- | --- | --- |
| `GET` | `/reviews` | query: `propertyId?`, `userId?`, `status?` | `List<Review>` | 评价列表 |
| `GET` | `/reviews/{id}` | path: `id` | `Review` | 评价详情 |
| `GET` | `/reviews/booking/{bookingId}` | path: `bookingId` | `Review` | 按订单查询评价 |
| `POST` | `/reviews` | body: `Review` | `Review` | 创建评价 |
| `PUT` | `/reviews/{id}` | path: `id`, body: `Review` | `Review` | 更新评价 |
| `POST` | `/reviews/{id}/approve` | path: `id` | `Review` | 审核通过 |
| `POST` | `/reviews/{id}/reply` | text body: `replyContent` | `Review` | 回复评价 |
| `DELETE` | `/reviews/{id}` | path: `id` | 空 | 删除评价 |

`Review` 主要字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | integer | 评价 ID |
| `booking` | object | 关联订单，常用 `{"id": 10}` |
| `user` | object | 关联用户，常用 `{"id": 12}` |
| `property` | object | 关联房源，常用 `{"id": 1}` |
| `overallRating` | integer | 总评分，必填 |
| `cleanlinessRating` / `serviceRating` / `locationRating` / `valueRating` | integer | 分项评分 |
| `comment` | string | 评论内容 |
| `images` | string(JSON) | 图片 |
| `isAnonymous` | boolean | 是否匿名 |
| `isVerified` | boolean | 是否已验证 |
| `helpfulCount` | integer | 有用数 |
| `replyContent` / `replyTime` | string/datetime | 商家回复内容/时间 |
| `status` | enum | `PENDING`、`APPROVED`、`REJECTED`、`HIDDEN` |

### 6.9 Coupons

| 方法 | 路径 | 参数 / Body | 返回 | 说明 |
| --- | --- | --- | --- | --- |
| `GET` | `/coupons` | query: `merchantId?`, `status?` | `List<Coupon>` | 优惠券列表 |
| `GET` | `/coupons/{id}` | path: `id` | `Coupon` | 优惠券详情 |
| `POST` | `/coupons` | body: `Coupon` | `Coupon` | 创建优惠券 |
| `PUT` | `/coupons/{id}` | path: `id`, body: `Coupon` | `Coupon` | 更新优惠券 |
| `DELETE` | `/coupons/{id}` | path: `id` | 空 | 删除优惠券 |

`Coupon` 主要字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | integer | 优惠券 ID |
| `merchant` | object | 关联商家，常用 `{"id": 3}` |
| `couponName` | string | 优惠券名称 |
| `couponType` | enum | `FIXED`、`PERCENTAGE` |
| `discountValue` | number | 优惠金额或折扣值 |
| `minAmount` | number | 最低使用金额 |
| `maxDiscount` | number | 最大优惠 |
| `totalQuantity` / `usedQuantity` | integer | 总量/已使用 |
| `startTime` / `endTime` | datetime | 生效/过期时间 |
| `applicableProperties` | string(JSON) | 适用房源 |
| `status` | enum | `ACTIVE`、`INACTIVE`、`EXPIRED` |

### 6.10 Notifications

| 方法 | 路径 | 参数 / Body | 返回 | 说明 |
| --- | --- | --- | --- | --- |
| `GET` | `/notifications` | query: `userId?`, `unreadOnly=false` | `List<Notification>` | 通知列表 |
| `GET` | `/notifications/unread-count` | query: `userId` | `{"count": number}` | 未读数量 |
| `POST` | `/notifications/{id}/read` | path: `id` | `Notification` | 单条标记已读 |
| `POST` | `/notifications/read-all` | query: `userId` | `{"updated": number}` | 全部标记已读 |

`Notification` 主要字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | integer | 通知 ID |
| `user` | object | 关联用户 |
| `notificationType` | enum | `SYSTEM`、`BOOKING`、`PAYMENT`、`REVIEW`、`PROMOTION` |
| `title` | string | 标题 |
| `content` | string | 内容 |
| `relatedId` | integer | 关联业务 ID |
| `isRead` | boolean | 是否已读 |
| `readAt` | datetime | 阅读时间 |
| `createdAt` | datetime | 创建时间 |

## 7. 可直接放入 SFT 的 function tool schema 示例

以下是高频工具的 OpenAI function 风格 schema 示例。完整工具可按第 5 节表格扩展。

### 查询订单号

```json
{
  "type": "function",
  "function": {
    "name": "get_booking_by_number",
    "description": "按订单号查询订单详情，返回订单状态、支付状态、入住离店日期、联系人和关联房源等信息。",
    "parameters": {
      "type": "object",
      "properties": {
        "booking_number": {
          "type": "string",
          "description": "订单号，例如 BK202605080001"
        }
      },
      "required": ["booking_number"]
    }
  }
}
```

### 搜索房源

```json
{
  "type": "function",
  "function": {
    "name": "search_properties",
    "description": "搜索房源，支持城市、区域、价格、评分、设施、关键词和附近距离等条件。",
    "parameters": {
      "type": "object",
      "properties": {
        "keyword": {"type": "string", "description": "关键词，例如海景、亲子、地铁口"},
        "city": {"type": "string", "description": "城市"},
        "district": {"type": "string", "description": "区县"},
        "min_price": {"type": "number", "description": "最低价格"},
        "max_price": {"type": "number", "description": "最高价格"},
        "min_rating": {"type": "number", "description": "最低评分"},
        "featured": {"type": "boolean", "description": "是否只看精选房源"},
        "facilities": {
          "type": "array",
          "items": {"type": "string"},
          "description": "设施列表"
        },
        "latitude": {"type": "number", "description": "纬度"},
        "longitude": {"type": "number", "description": "经度"},
        "distance_km": {"type": "number", "description": "距离半径，单位公里"},
        "page": {"type": "integer", "description": "页码，默认 1"},
        "size": {"type": "integer", "description": "每页数量，默认 10"}
      },
      "required": []
    }
  }
}
```

### 取消订单

```json
{
  "type": "function",
  "function": {
    "name": "cancel_booking",
    "description": "取消订单，会修改订单状态。只有当用户明确要求取消订单时才调用。",
    "parameters": {
      "type": "object",
      "properties": {
        "booking_id": {"type": "integer", "description": "订单 ID"},
        "reason": {"type": "string", "description": "取消原因"}
      },
      "required": ["booking_id", "reason"]
    }
  }
}
```

### 未读通知数量

```json
{
  "type": "function",
  "function": {
    "name": "get_unread_notification_count",
    "description": "查询用户未读通知数量。",
    "parameters": {
      "type": "object",
      "properties": {
        "user_id": {"type": "integer", "description": "用户 ID；普通用户和商家会被收敛为当前用户"}
      },
      "required": ["user_id"]
    }
  }
}
```

## 8. SFT 样例

### 8.1 订单状态查询

```json
{
  "conversations": [
    {
      "role": "system",
      "content": "你是 RoomOS 民宿预订平台的中文客服助手。涉及具体订单、支付、房源、评价、通知等平台数据时，必须调用工具确认后再回答。",
      "tools": "[{\"type\":\"function\",\"function\":{\"name\":\"get_booking_by_number\",\"description\":\"按订单号查询订单详情\",\"parameters\":{\"type\":\"object\",\"properties\":{\"booking_number\":{\"type\":\"string\",\"description\":\"订单号\"}},\"required\":[\"booking_number\"]}}}]"
    },
    {
      "role": "user",
      "content": "帮我查一下订单 BK202605080001 现在是什么状态"
    },
    {
      "role": "assistant",
      "content": "",
      "tool_calls": "[{\"function\":{\"name\":\"get_booking_by_number\",\"arguments\":{\"booking_number\":\"BK202605080001\"}}}]"
    },
    {
      "role": "tool",
      "name": "get_booking_by_number",
      "content": "{\"ok\":true,\"tool\":\"get_booking_by_number\",\"result\":{\"item\":{\"id\":10,\"bookingNumber\":\"BK202605080001\",\"status\":\"CONFIRMED\",\"paymentStatus\":\"PAID\",\"checkInDate\":\"2026-05-20\",\"checkOutDate\":\"2026-05-22\"},\"source\":\"booking-service:/bookings/number/BK202605080001\"}}"
    },
    {
      "role": "assistant",
      "content": "这笔订单当前是已确认状态，支付状态为已支付。入住日期是 2026-05-20，离店日期是 2026-05-22。"
    }
  ]
}
```

### 8.2 搜索房源

```json
{
  "conversations": [
    {
      "role": "system",
      "content": "你是 RoomOS 民宿预订平台的中文客服助手。需要查询房源、价格、评分或库存时优先调用后端工具。",
      "tools": "[{\"type\":\"function\",\"function\":{\"name\":\"search_properties\",\"description\":\"搜索房源，支持城市、区域、价格、评分、设施和关键词等条件\",\"parameters\":{\"type\":\"object\",\"properties\":{\"keyword\":{\"type\":\"string\"},\"city\":{\"type\":\"string\"},\"district\":{\"type\":\"string\"},\"min_price\":{\"type\":\"number\"},\"max_price\":{\"type\":\"number\"},\"min_rating\":{\"type\":\"number\"},\"featured\":{\"type\":\"boolean\"},\"facilities\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}},\"page\":{\"type\":\"integer\"},\"size\":{\"type\":\"integer\"}},\"required\":[]}}}]"
    },
    {
      "role": "user",
      "content": "深圳南山区有没有评分 4.5 以上、800 以下的民宿？"
    },
    {
      "role": "assistant",
      "content": "",
      "tool_calls": "[{\"function\":{\"name\":\"search_properties\",\"arguments\":{\"city\":\"深圳\",\"district\":\"南山区\",\"max_price\":800,\"min_rating\":4.5,\"keyword\":\"民宿\",\"page\":1,\"size\":10}}}]"
    }
  ]
}
```

### 8.3 动作类工具调用

动作类工具要训练模型先识别“用户明确要求执行动作”，而不是只在用户询问可不可以时直接执行。

正例：

```json
{
  "role": "user",
  "content": "帮我取消订单 10，原因是行程变化"
}
```

```json
{
  "role": "assistant",
  "content": "",
  "tool_calls": "[{\"function\":{\"name\":\"cancel_booking\",\"arguments\":{\"booking_id\":10,\"reason\":\"行程变化\"}}}]"
}
```

负例：

```json
{
  "role": "user",
  "content": "订单 10 可以取消吗？"
}
```

这类问题应先调用查询工具，例如 `get_booking_detail`，不要直接调用 `cancel_booking`。

## 9. 构造数据时的注意事项

- 查询具体平台数据时，优先训练模型调用 read 工具，再基于工具结果回答。
- 修改状态的工具包括：`cancel_booking`、`check_in_booking`、`check_out_booking`、`reply_review`、`mark_notification_read`、`mark_all_notifications_read`。
- action 工具的训练样本应包含明确用户授权，比如“帮我取消”“现在办理入住”“全部标记已读”。
- 角色相关样本建议在 system 或额外上下文中加入 `userContext`，否则普通用户、商家、管理员的可见数据范围会混淆。
- 后端 enum 值区分大小写，训练工具参数时建议使用大写枚举值。
- 日期字段使用 ISO 格式，例如 `2026-05-20`；时间字段使用 `HH:mm:ss` 或后端可解析格式；日期时间使用 ISO datetime。
- 关联实体在 REST body 中通常用简化对象传 ID，例如 `{"user":{"id":12}}`、`{"booking":{"id":10}}`、`{"roomType":{"id":3}}`。
- `facilities`、`images`、`policies`、`amenities` 等字段在实体中是 JSON 字符串，不是后端强类型数组；搜索工具的 `facilities` 参数才是数组。

