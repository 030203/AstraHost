# Elasticsearch 房源搜索接入说明

## 目标

房源搜索已从单一的 MySQL 条件查询扩展为可选的 Elasticsearch 搜索链路，支持：

- 关键词搜索：`propertyName`、`province`、`city`、`district`、`address`、`description`、`facilities`
- 复合筛选：城市、行政区、价格区间、评分、精选标记、设施列表
- 地理位置搜索：按经纬度 + 半径（公里）筛选附近房源
- 索引同步：房源新增、修改、审核、删除时自动同步索引
- 平滑降级：ES 未启用或不可用时，自动回退到数据库过滤

## 启用方式

后端新增了以下配置项，默认不开启 ES：

```properties
spring.elasticsearch.uris=${ROOMOS_ES_URIS:http://127.0.0.1:9200}
spring.elasticsearch.username=${ROOMOS_ES_USERNAME:}
spring.elasticsearch.password=${ROOMOS_ES_PASSWORD:}
roomos.search.es.enabled=${ROOMOS_ES_ENABLED:false}
```

先启动 Elasticsearch：

```bash
docker compose -f docker-compose.elasticsearch.yml up -d
```

也可以单独使用 `docker run`，但仓库里已经提供了 compose 文件，优先建议直接复用。

启动后再通过环境变量开启：

```bash
set ROOMOS_ES_ENABLED=true
set ROOMOS_ES_URIS=http://127.0.0.1:9200
```

如果 ES 开启后是首次接入，建议执行一次全量重建索引。

## 搜索接口

### 1. 房源搜索

```http
GET /api/properties/search
```

支持的查询参数：

- `keyword`：关键词
- `city`：城市
- `district`：行政区
- `minPrice`：最低价格
- `maxPrice`：最高价格
- `minRating`：最低评分
- `featured`：是否精选
- `facilities`：设施，可重复传参
- `latitude`：纬度
- `longitude`：经度
- `distanceKm`：搜索半径（公里）
- `page`：页码，默认 `1`
- `size`：每页数量，默认 `10`，最大 `50`

示例：

```http
GET /api/properties/search?city=杭州&minPrice=300&maxPrice=800&facilities=投影仪&facilities=浴缸&latitude=30.2741&longitude=120.1551&distanceKm=3
```

返回结构：

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "size": 10,
  "usedElasticsearch": true
}
```

### 2. 全量重建索引

```http
POST /api/properties/search/reindex
```

用途：

- 首次启用 ES 后，把历史房源数据写入索引
- 索引异常时做一次修复

返回结构：

```json
{
  "indexedCount": 0,
  "removedCount": 0,
  "usedElasticsearch": true
}
```

## 索引同步规则

- `APPROVED` 房源：写入 / 更新 ES 索引
- 非 `APPROVED` 房源：从 ES 索引移除
- 删除房源：从 ES 索引移除

这样可以保证面向用户的搜索结果只包含已审核通过的房源。
