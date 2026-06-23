<template>
  <div class="hotel-card-test">
    <h1>酒店卡片网格测试</h1>

    <section class="test-section">
      <h2>示例 1：多分类酒店推荐</h2>
      <div class="test-content">
        <HotelCardGrid :categories="mockCategories1" />
      </div>
    </section>

    <section class="test-section">
      <h2>示例 2：单分类酒店推荐</h2>
      <div class="test-content">
        <HotelCardGrid :categories="mockCategories2" />
      </div>
    </section>

    <section class="test-section">
      <h2>示例 3：解析器测试</h2>
      <div class="test-parser">
        <h3>输入 AI 文本：</h3>
        <textarea v-model="testText" rows="12" placeholder="粘贴 AI 返回的酒店推荐文本..."></textarea>
        <button @click="parseText">解析</button>

        <div v-if="parsedResult">
          <h3>解析结果：</h3>
          <pre>{{ JSON.stringify(parsedResult, null, 2) }}</pre>

          <h3>渲染效果：</h3>
          <HotelCardGrid :categories="parsedResult" />
        </div>
        <div v-else-if="parseAttempted">
          <p style="color: red;">未能解析出酒店推荐内容</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import HotelCardGrid from '../components/hotel/HotelCardGrid.vue'
import { parseHotelRecommendations } from '../utils/hotelParser'

const mockCategories1 = [
  {
    name: '新开业',
    hotels: [
      {
        name: '深圳湾万怡酒店',
        location: '南山区深圳湾',
        highlight: '2024年全新开业，现代设计与智能科技完美融合',
        facilities: ['免费WiFi', '健身房', '游泳池', '停车场'],
        price: '¥680起',
        rating: '9.2'
      },
      {
        name: '前海希尔顿花园酒店',
        location: '前海自贸区',
        highlight: '紧邻前海湾地铁站，商务出行首选',
        facilities: ['会议室', '餐厅', '24小时前台'],
        price: '¥580起',
        rating: '8.9'
      }
    ]
  },
  {
    name: '口岸首选',
    hotels: [
      {
        name: '皇岗口岸速8酒店',
        location: '福田区皇岗口岸',
        highlight: '步行3分钟到口岸，过关最便捷',
        facilities: ['免费WiFi', '行李寄存', '接送服务'],
        price: '¥320起',
        rating: '8.5'
      },
      {
        name: '深圳湾口岸亚朵酒店',
        location: '南山区深圳湾口岸',
        highlight: '口岸旁高品质连锁，环境舒适',
        facilities: ['免费WiFi', '停车场', '餐厅', '洗衣服务'],
        price: '¥480起',
        rating: '9.0'
      },
      {
        name: '福田口岸如家酒店',
        location: '福田区福田口岸',
        highlight: '性价比之选，近地铁4号线',
        facilities: ['免费WiFi', '24小时前台'],
        price: '¥280起',
        rating: '8.3'
      }
    ]
  },
  {
    name: '高端奢华',
    hotels: [
      {
        name: '深圳瑞吉酒店',
        location: '福田区中心区',
        highlight: '国际五星级奢华体验，管家式服务',
        facilities: ['SPA', '温泉', '米其林餐厅', '游泳池', '健身房'],
        price: '¥1680起',
        rating: '9.6'
      },
      {
        name: '柏悦酒店',
        location: '福田CBD',
        highlight: '位于平安金融中心高层，俯瞰深圳全景',
        facilities: ['SPA', '游泳池', '西餐厅', '行政酒廊'],
        price: '¥1980起',
        rating: '9.7'
      }
    ]
  }
]

const mockCategories2 = [
  {
    name: '商务酒店',
    hotels: [
      {
        name: '深圳会展中心希尔顿',
        location: '福田区会展中心',
        highlight: '紧邻会展中心，商务活动便利',
        facilities: ['会议室', '商务中心', '健身房', '餐厅'],
        price: '¥780起',
        rating: '9.1'
      },
      {
        name: '科技园智选假日酒店',
        location: '南山区科技园',
        highlight: '科技企业聚集区，交通便捷',
        facilities: ['免费WiFi', '停车场', '24小时前台'],
        price: '¥450起',
        rating: '8.7'
      }
    ]
  }
]

const testText = ref(`根据您的需求，为您推荐以下深圳南山区的优质酒店：

【新开业】

1. 深圳湾万怡酒店
位于：南山区深圳湾
亮点：2024年全新开业，现代设计与智能科技完美融合
设施：免费WiFi、健身房、游泳池、停车场
价格：¥680起
评分：9.2分

2. 前海希尔顿花园酒店
位于：前海自贸区
亮点：紧邻前海湾地铁站，商务出行首选
设施：会议室、餐厅、24小时前台
价格：¥580起
评分：8.9分

【口岸首选】

1. 深圳湾口岸亚朵酒店
位于：南山区深圳湾口岸
亮点：口岸旁高品质连锁，环境舒适
设施：免费WiFi、停车场、餐厅、洗衣服务
价格：¥480起
评分：9.0分`)

const parsedResult = ref(null)
const parseAttempted = ref(false)

const parseText = () => {
  parseAttempted.value = true
  parsedResult.value = parseHotelRecommendations(testText.value)
}
</script>

<style scoped>
.hotel-card-test {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 20px;
}

h1 {
  font-size: 32px;
  margin-bottom: 40px;
  color: #0f172a;
}

.test-section {
  margin-bottom: 60px;
}

.test-section h2 {
  font-size: 24px;
  margin-bottom: 20px;
  color: #334155;
  padding-bottom: 12px;
  border-bottom: 2px solid #e2e8f0;
}

.test-content {
  background: #f8fafc;
  padding: 24px;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
}

.test-parser {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.test-parser h3 {
  font-size: 18px;
  color: #475569;
  margin: 16px 0 8px;
}

.test-parser textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  resize: vertical;
}

.test-parser button {
  align-self: flex-start;
  padding: 10px 24px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.test-parser button:hover {
  background: #2563eb;
}

.test-parser pre {
  background: #1e293b;
  color: #e2e8f0;
  padding: 16px;
  border-radius: 8px;
  overflow: auto;
  font-size: 12px;
  max-height: 400px;
}
</style>
