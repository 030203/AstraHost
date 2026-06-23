# 酒店卡片渲染系统 - 快速使用指南

## 快速开始

### 1. 测试页面预览

访问测试页面查看效果：
```
http://localhost:5400/hotel-card-test
```

### 2. 在 AI 助手中使用

系统已自动集成到 AI 助手中，直接提问即可：

**示例查询**：
- "深圳南山有哪些评分高的酒店？"
- "推荐几家深圳湾口岸附近的酒店"
- "深圳有哪些新开的高端酒店？"

AI 返回包含酒店推荐的回复时，会自动渲染为卡片网格。

### 3. 手动集成到其他组件

```vue
<template>
  <HotelCardGrid :categories="hotelData" />
</template>

<script setup>
import HotelCardGrid from '@/components/hotel/HotelCardGrid.vue'
import { parseHotelRecommendations } from '@/utils/hotelParser'

// 解析 AI 文本
const aiResponse = "【新开业】\n\n1. 深圳湾万怡酒店..."
const hotelData = parseHotelRecommendations(aiResponse)
</script>
```

## AI 文本格式要求

为确保正确解析，AI 返回的文本应符合以下格式：

### 基本格式
```
【分类名称】

1. 酒店名称
位于：具体位置
亮点：一句话描述
设施：设施1、设施2、设施3
价格：¥XXX起
评分：X.X分

2. 酒店名称
...
```

### 关键要素

**必填**：
- ✅ 酒店名称

**可选**：
- 位置（支持关键词：位于、地址、坐标、靠近）
- 亮点（支持关键词：亮点、特色、推荐理由）
- 设施（自动识别常见设施关键词）
- 价格（支持：¥、￥、元、起）
- 评分（支持：评分、评价、得分）

### 分类标签

**预设分类**（自动配色）：
- 新开业 → 绿色
- 口岸首选 / 口岸 → 蓝色
- 高端奢华 / 奢华 → 金色
- 商务 → 靛蓝色
- 亲子 → 粉色
- 度假 → 紫色

**其他分类** → 默认灰色

## 数据结构

### 输入格式（解析器输出）

```javascript
[
  {
    name: '新开业',          // 分类名称
    hotels: [
      {
        name: '深圳湾万怡酒店',        // 必填
        location: '南山区深圳湾',       // 可选
        highlight: '2024年全新开业...',  // 可选
        facilities: ['WiFi', '停车场'],   // 可选
        price: '¥680起',               // 可选
        rating: '9.2'                  // 可选
      }
    ]
  }
]
```

### 组件 Props

```typescript
interface HotelCardGridProps {
  categories: Array<{
    name: string
    hotels: Array<{
      name: string
      location?: string
      highlight?: string
      facilities?: string[]
      price?: string
      rating?: string
    }>
  }>
}
```

## 常见场景

### 场景 1: AI 助手自动渲染

**用户提问**：
```
深圳南山有哪些评分高的酒店？
```

**AI 回复**：
```
根据您的需求，为您推荐以下深圳南山区的优质酒店：

【新开业】

1. 深圳湾万怡酒店
位于：南山区深圳湾
亮点：2024年全新开业，现代设计与智能科技完美融合
设施：免费WiFi、健身房、游泳池、停车场
价格：¥680起
评分：9.2分
```

**结果**：自动渲染为卡片网格

### 场景 2: 手动调用解析器

```javascript
import { parseHotelRecommendations, containsHotelRecommendation } from '@/utils/hotelParser'

const aiText = "【新开业】\n\n1. 深圳湾万怡酒店..."

// 检测是否包含酒店推荐
if (containsHotelRecommendation(aiText)) {
  // 解析文本
  const hotelData = parseHotelRecommendations(aiText)
  
  if (hotelData) {
    console.log('解析成功', hotelData)
    // 渲染卡片
  } else {
    console.log('解析失败')
    // 显示原始文本
  }
}
```

### 场景 3: 静态数据渲染

```vue
<template>
  <HotelCardGrid :categories="staticHotels" />
</template>

<script setup>
const staticHotels = [
  {
    name: '商务酒店',
    hotels: [
      {
        name: '深圳会展中心希尔顿',
        location: '福田区会展中心',
        highlight: '紧邻会展中心，商务活动便利',
        facilities: ['会议室', '商务中心', '健身房'],
        price: '¥780起',
        rating: '9.1'
      }
    ]
  }
]
</script>
```

## 样式定制

### 自定义分类颜色

编辑 `HotelCardGrid.vue`：

```javascript
const categoryColors = {
  '我的分类': 'linear-gradient(135deg, #起始色 0%, #结束色 100%)'
}
```

### 调整卡片尺寸

编辑 `HotelCardGrid.vue`：

```css
.hotel-card-grid {
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); /* 改变最小宽度 */
}

.hotel-card-image {
  height: 120px; /* 改变图片区高度 */
}
```

### 调整字体大小

```css
.hotel-card-name {
  font-size: 15px; /* 默认 14px */
}

.hotel-card-price {
  font-size: 15px; /* 默认 14px */
}
```

## 故障排查

### 问题：卡片不显示

**检查步骤**：
1. 打开浏览器控制台
2. 检查 `parseHotelRecommendations()` 返回值
   ```javascript
   console.log(parseHotelRecommendations(aiText))
   ```
3. 确认是否返回 `null`

**常见原因**：
- AI 文本不包含酒店关键词
- 格式不符合解析规则
- 酒店名称缺失

### 问题：解析不完整

**检查步骤**：
1. 访问 `/hotel-card-test`
2. 粘贴 AI 文本到解析器测试
3. 查看 JSON 输出

**常见原因**：
- 关键词拼写错误（位于 vs 位置）
- 分隔符不一致（中英文冒号）
- 特殊字符干扰

### 问题：样式错乱

**检查步骤**：
1. 检查父容器宽度
2. 验证是否有全局 CSS 冲突
3. 检查浏览器兼容性

**解决方法**：
```css
/* 确保父容器有足够宽度 */
.parent-container {
  width: 100%;
  max-width: 1400px;
}
```

## API 参考

### parseHotelRecommendations(text)

解析 AI 文本，提取酒店信息。

**参数**：
- `text` (string): AI 返回的文本

**返回**：
- `Array<Category>`: 解析成功
- `null`: 未检测到酒店推荐或解析失败

**示例**：
```javascript
const result = parseHotelRecommendations("【新开业】\n\n1. 深圳湾万怡酒店...")
// [{ name: '新开业', hotels: [...] }]
```

### containsHotelRecommendation(text)

检测文本是否包含酒店推荐内容。

**参数**：
- `text` (string): 待检测文本

**返回**：
- `boolean`: true 表示包含酒店推荐

**示例**：
```javascript
containsHotelRecommendation("深圳有哪些酒店？") // true
containsHotelRecommendation("今天天气真好") // false
```

## 性能提示

1. **按需解析**：仅在检测到酒店关键词时才调用解析器
2. **缓存结果**：对于静态数据，可以预先解析并缓存
3. **懒加载**：大量酒店时可以考虑分页或虚拟滚动
4. **避免重复解析**：在组件挂载时解析一次即可

## 浏览器支持

- ✅ Chrome 88+
- ✅ Firefox 85+
- ✅ Safari 14+
- ✅ Edge 88+

## 更新日志

### v1.0.0 (2026-06-19)
- ✅ 初始版本
- ✅ 支持多分类酒店推荐
- ✅ 智能文本解析
- ✅ 响应式卡片布局
- ✅ 集成到 AI 助手
- ✅ 测试页面

## 技术支持

遇到问题？
1. 查看 `docs/hotel-card-rendering.md` 完整文档
2. 访问 `/hotel-card-test` 测试页面调试
3. 检查浏览器控制台错误信息
