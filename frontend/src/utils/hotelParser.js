const HOTEL_KEYWORDS = [
  '酒店',
  '民宿',
  '公寓',
  '客栈',
  '旅馆',
  '度假村',
  '住宿',
  'hotel',
  'resort',
  'apartment',
  'inn'
]

const CATEGORY_HINT_RE = /(推荐|精选|首选|新开|高端|奢华|商务|亲子|度假|热门|口岸|Top|TOP|榜单|必住|高性价比|海景|机场|市中心)/
const HOTEL_NAME_HINT_RE = /(酒店|公寓|民宿|客栈|旅馆|度假村|hotel|resort|apartment|inn)/i
const NUMBER_PREFIX_RE = /^(?:#{1,6}\s*)?(?:[-*•]+\s*)?(?:(?:\d+|[①②③④⑤⑥⑦⑧⑨⑩]|[一二三四五六七八九十]+|[0-9]+⃣)[\.\)、:：]?\s*)+/
const CITY_LIST = [
  '北京', '上海', '广州', '深圳', '杭州', '成都', '重庆', '西安', '苏州', '南京',
  '武汉', '长沙', '厦门', '珠海', '三亚', '青岛', '天津', '昆明', '大理', '佛山',
  '东莞', '惠州', '宁波', '福州', '郑州', '济南', '合肥', '南昌', '哈尔滨', '沈阳'
]

function normalizeLine(line) {
  return String(line || '')
    .replace(/\r/g, '')
    .replace(/^\s*>\s?/, '')
    .trim()
}

function stripDecorators(line) {
  return normalizeLine(line)
    .replace(/^#{1,6}\s*/, '')
    .replace(/^\s*[-*•]+\s*/, '')
    .replace(/^\s*[🏨🏡⭐✨🔥📍💰💵💴💎🛏️🛎️]+\s*/u, '')
    .trim()
}

function cleanCategoryName(line) {
  const stripped = stripDecorators(line)
  const bracketMatch = stripped.match(/^[【\[](.+?)[】\]]$/)
  if (bracketMatch) return bracketMatch[1].trim()
  return stripped.replace(/^[\-–—\s]+|[\-–—\s]+$/g, '').trim()
}

function cleanHotelName(line) {
  const stripped = stripDecorators(line)
    .replace(NUMBER_PREFIX_RE, '')
    .replace(/\*\*/g, '')
    .replace(/[（(]\s*(推荐|首选|精选)\s*[)）]$/i, '')

  const splitMatch = stripped.split(/\s+(?=(?:位于|位置|地址|亮点|特色|推荐理由|价格|房价|评分|评星|¥|￥))/)
  return String(splitMatch[0] || stripped).trim()
}

function inferCityFromText(text) {
  const value = String(text || '')
  for (const city of CITY_LIST) {
    if (value.includes(city)) return city
  }

  const cityMatch = value.match(/([\u4e00-\u9fa5]{2,8})市/)
  if (cityMatch) return cityMatch[1]

  return ''
}

function extractPriceLabel(text) {
  const source = String(text || '')
  const match = source.match(/(?:约|¥|￥)?\s*(\d{2,5}(?:[.,]\d+)?)\s*(?:[-~至到]\s*(\d{2,5}(?:[.,]\d+)?))?\s*元?(?:\s*\/\s*晚|\s*每晚|\s*起)?/i)
  if (!match) return ''
  const low = match[1]?.replace(/,/g, '')
  const high = match[2]?.replace(/,/g, '')
  if (low && high) return `￥${low}-${high}`
  if (low) return `￥${low}`
  return ''
}

function extractRating(text) {
  const source = String(text || '')
  const match = source.match(/([3-9](?:\.\d)?|10(?:\.0)?)(?=\s*(?:分|\/5|\/10|$|[）)]))/)
  return match ? match[1] : ''
}

function splitFacilities(text) {
  return String(text || '')
    .split(/[、，,\/|｜]/)
    .map((item) =>
      item
        .replace(/^(设施|配套|服务|特色|亮点|推荐理由)\s*[:：]?\s*/i, '')
        .trim()
    )
    .filter(Boolean)
    .filter((item, index, list) => list.indexOf(item) === index)
    .slice(0, 5)
}

function cleanTableCell(cell) {
  return String(cell || '')
    .replace(/\*\*/g, '')
    .replace(/`/g, '')
    .replace(/^[🏖️🏨⭐✨🔥📍💰💵💴💎🛏️🛎️\s]+/u, '')
    .replace(/\s+/g, ' ')
    .trim()
}

function splitMarkdownRow(line) {
  const normalized = normalizeLine(line)
  if (!normalized.includes('|')) return []
  return normalized
    .replace(/^\|/, '')
    .replace(/\|$/, '')
    .split('|')
    .map((cell) => cleanTableCell(cell))
}

function isMarkdownDividerRow(cells) {
  return cells.length > 0 && cells.every((cell) => /^:?-{3,}:?$/.test(cell.replace(/\s/g, '')))
}

function findTableColumnIndex(cells, pattern) {
  return cells.findIndex((cell) => pattern.test(cleanTableCell(cell)))
}

function looksLikeHotelTableHeader(cells) {
  if (cells.length < 2) return false
  const hasNameColumn = findTableColumnIndex(cells, /(酒店名称|酒店|推荐酒店|hotel)/i) >= 0
  const hasSupportColumn =
    findTableColumnIndex(cells, /(区域|位置|地段|片区|商圈|口岸|靠近|亮点|特色|推荐理由|参考价|价格|房价|评分|星级)/i) >= 0
  return hasNameColumn && hasSupportColumn
}

function extractTableLocation(text) {
  const value = cleanTableCell(text)
  if (!value) return ''
  const matched = value.match(
    /(亚龙湾|大东海|海棠湾|三亚湾|免税城|机场|市区|前海|南山|福田|罗湖|宝安|龙岗|龙华|盐田|大鹏新区|[\u4e00-\u9fa5]{2,8}[·・][\u4e00-\u9fa5A-Za-z0-9]{1,18})/
  )
  return matched?.[1] || value
}

function splitHotelNameCandidates(text) {
  const source = cleanTableCell(text)
  if (!source) return []

  if (!/[、，,]/.test(source)) return [source]

  const candidates = source
    .split(/[、，,]/)
    .map((item) => cleanTableCell(item))
    .filter(Boolean)

  return candidates.length > 1 ? candidates : [source]
}

function pushTableCategory(categories, categoryIndex, categoryName, hotels) {
  if (!Array.isArray(hotels) || !hotels.length) return
  if (!categoryIndex.has(categoryName)) {
    categoryIndex.set(categoryName, categories.length)
    categories.push({ name: categoryName, hotels: [] })
  }

  categories[categoryIndex.get(categoryName)].hotels.push(...hotels)
}

function parseMarkdownHotelTable(text) {
  const lines = String(text || '')
    .split('\n')
    .map((line) => normalizeLine(line))
    .filter(Boolean)

  const categories = []
  const categoryIndex = new Map()
  let currentCategory = '精选推荐'

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i]
    const nextLine = lines[i + 1] || ''

    if (isCategoryLine(line, nextLine) || /^#{1,6}\s+/.test(line)) {
      currentCategory = cleanCategoryName(line) || currentCategory
    }

    const headerCells = splitMarkdownRow(line)
    const dividerCells = splitMarkdownRow(nextLine)
    if (!looksLikeHotelTableHeader(headerCells) || !isMarkdownDividerRow(dividerCells)) continue

    const nameIndex = findTableColumnIndex(headerCells, /(酒店名称|酒店|推荐酒店|hotel)/i)
    const locationIndex = findTableColumnIndex(headerCells, /(区域|位置|地段|片区|商圈|口岸|靠近)/i)
    const highlightIndex = findTableColumnIndex(headerCells, /(亮点|特色|推荐理由|简介|说明)/i)
    const priceIndex = findTableColumnIndex(headerCells, /(参考价|价格|房价|每晚|价位|人均)/i)
    const ratingIndex = findTableColumnIndex(headerCells, /(评分|星级|rating)/i)

    const hotels = []
    let endIndex = i + 1
    for (let rowIndex = i + 2; rowIndex < lines.length; rowIndex += 1) {
      const cells = splitMarkdownRow(lines[rowIndex])
      if (!cells.length) break
      if (isMarkdownDividerRow(cells)) continue

      endIndex = rowIndex

      const nameCandidates = splitHotelNameCandidates(cells[nameIndex] || '')
      if (!nameCandidates.length) continue

      const highlight = cleanTableCell(highlightIndex >= 0 ? cells[highlightIndex] : '')
      const location = extractTableLocation(locationIndex >= 0 ? cells[locationIndex] : highlight)
      const priceLabel = extractPriceLabel(priceIndex >= 0 ? cells[priceIndex] : '')
      const rating = extractRating(ratingIndex >= 0 ? cells[ratingIndex] : '')

      nameCandidates.forEach((nameCell) => {
        const name = cleanHotelName(nameCell)
        if (!name || /^推荐酒店$/i.test(name) || name.length > 40) return

        hotels.push({
          name,
          location,
          address: '',
          city: inferCityFromText(`${name} ${location} ${highlight}`),
          highlight,
          facilities: [],
          tags: splitFacilities(highlight || location).slice(0, 4),
          price: priceLabel,
          priceLabel,
          rating,
          category: currentCategory || '精选推荐'
        })
      })
    }

    pushTableCategory(categories, categoryIndex, currentCategory || '精选推荐', hotels)
    i = Math.max(i, endIndex)
  }

  const filtered = categories.filter((category) => Array.isArray(category.hotels) && category.hotels.length)
  return filtered.length ? filtered : null
}

function looksLikeDivider(line) {
  return /^[-_*~]{3,}$/.test(String(line || '').replace(/\s/g, ''))
}

function looksLikeMetaLine(line) {
  const value = stripDecorators(line)
  return (
    /(位于|位置|地址|地区|靠近|商圈|亮点|特色|推荐理由|价格|房价|评分|评星|设施|配套|服务|早餐|房型|每晚|元\/晚|¥|￥)/i.test(value) ||
    /^[\u4e00-\u9fa5]{2,6}[·・][\u4e00-\u9fa5]{2,10}$/.test(value)
  )
}

function isCategoryLine(line, nextLine = '') {
  const value = normalizeLine(line)
  if (!value || looksLikeDivider(value)) return false
  if (NUMBER_PREFIX_RE.test(value)) return false

  const stripped = stripDecorators(value)
  if (!stripped || stripped.length > 28) return false
  if (HOTEL_NAME_HINT_RE.test(stripped)) return false
  if (/^[【\[](.+?)[】\]]$/.test(stripped)) return true
  if (/^#{1,6}\s+/.test(value) && CATEGORY_HINT_RE.test(stripped)) return true
  if (CATEGORY_HINT_RE.test(stripped) && looksLikeHotelStart(nextLine)) return true

  return false
}

function looksLikeHotelStart(line, nextLine = '') {
  const value = normalizeLine(line)
  if (!value || looksLikeDivider(value)) return false

  const cleanedName = cleanHotelName(value)
  if (!cleanedName || cleanedName.length > 48) return false

  if (HOTEL_NAME_HINT_RE.test(cleanedName)) {
    if (NUMBER_PREFIX_RE.test(value)) return true
    if (!/[：:]/.test(cleanedName) && looksLikeMetaLine(nextLine)) return true
    if (cleanedName.length <= 28 && !/[。；;，,]/.test(cleanedName)) return true
  }

  return false
}

function parseHotelBlock(categoryName, lines) {
  if (!Array.isArray(lines) || !lines.length) return null

  const hotel = {
    name: cleanHotelName(lines[0]),
    location: '',
    address: '',
    city: '',
    highlight: '',
    facilities: [],
    tags: [],
    price: '',
    priceLabel: '',
    rating: '',
    category: categoryName || '精选推荐'
  }

  if (!hotel.name || !HOTEL_NAME_HINT_RE.test(hotel.name)) return null

  for (let i = 1; i < lines.length; i += 1) {
    const raw = stripDecorators(lines[i])
    if (!raw) continue

    if (!hotel.location) {
      const locationMatch = raw.match(/(?:位于|位置|地址|地区|靠近|商圈|📍)\s*[:：]?\s*(.+)$/i)
      if (locationMatch) {
        hotel.location = locationMatch[1].trim()
        hotel.city = inferCityFromText(hotel.location)
        continue
      }
      if (/^[\u4e00-\u9fa5]{2,6}[·・][\u4e00-\u9fa5]{2,12}$/.test(raw) || /(?:区|县|镇|口岸|机场|CBD|商圈|地铁|湾|站)$/.test(raw)) {
        hotel.location = raw
        hotel.city = inferCityFromText(hotel.location)
        continue
      }
    }

    if (!hotel.priceLabel) {
      const priceLabel = extractPriceLabel(raw)
      if (priceLabel) {
        hotel.priceLabel = priceLabel
        hotel.price = priceLabel
      }
    }

    if (!hotel.rating) {
      const rating = extractRating(raw)
      if (rating) hotel.rating = rating
    }

    if (!hotel.highlight) {
      const highlightMatch = raw.match(/(?:亮点|特色|推荐理由|适合人群)\s*[:：]?\s*(.+)$/i)
      if (highlightMatch) {
        hotel.highlight = highlightMatch[1].trim()
      } else if (
        raw.length >= 10 &&
        raw.length <= 80 &&
        !/(价格|房价|评分|设施|配套|服务|早餐|房型)/i.test(raw)
      ) {
        hotel.highlight = raw
      }
    }

    if (!hotel.address) {
      const addressMatch = raw.match(/(?:详细地址|地址)\s*[:：]?\s*(.+)$/i)
      if (addressMatch) hotel.address = addressMatch[1].trim()
    }

    if (/(设施|配套|服务)/i.test(raw)) {
      hotel.facilities = splitFacilities(raw)
      hotel.tags = hotel.facilities.slice(0, 4)
      continue
    }

    if (!hotel.tags.length && /(?:免费|接送机|停车场|茶室|设计感|地铁|海景|亲子|温泉|泳池|健身)/.test(raw)) {
      hotel.tags = splitFacilities(raw)
    }
  }

  if (!hotel.tags.length && hotel.facilities.length) {
    hotel.tags = hotel.facilities.slice(0, 4)
  }

  if (!hotel.city) {
    hotel.city = inferCityFromText(`${hotel.location} ${hotel.address} ${hotel.highlight}`)
  }

  return hotel
}

export function containsHotelRecommendation(text) {
  if (!text || typeof text !== 'string') return false
  const value = text.toLowerCase()
  const hasKeyword = HOTEL_KEYWORDS.some((keyword) => value.includes(keyword.toLowerCase()))
  if (!hasKeyword) return false

  return /(?:^|\n)\s*(?:#{1,6}\s*)?(?:[-*•]+\s*)?(?:(?:\d+|[①②③④⑤⑥⑦⑧⑨⑩]|[一二三四五六七八九十]+|[0-9]+⃣)[\.\)、:：]?\s*)?.{0,32}(酒店|公寓|民宿|客栈|度假村)/i.test(text)
}

export function parseHotelRecommendations(text) {
  if (!containsHotelRecommendation(text)) return null

  const tableParsed = parseMarkdownHotelTable(text)
  if (tableParsed?.length) return tableParsed

  const lines = String(text || '')
    .split('\n')
    .map((line) => normalizeLine(line))

  const categories = []
  const categoryIndex = new Map()
  let currentCategory = '精选推荐'
  let currentHotelLines = []

  const pushHotel = () => {
    const hotel = parseHotelBlock(currentCategory, currentHotelLines)
    currentHotelLines = []
    if (!hotel) return

    if (!categoryIndex.has(currentCategory)) {
      categoryIndex.set(currentCategory, categories.length)
      categories.push({ name: currentCategory, hotels: [] })
    }

    categories[categoryIndex.get(currentCategory)].hotels.push(hotel)
  }

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i]
    const nextLine = lines[i + 1] || ''

    if (!line || looksLikeDivider(line)) continue

    if (isCategoryLine(line, nextLine)) {
      pushHotel()
      currentCategory = cleanCategoryName(line) || '精选推荐'
      continue
    }

    if (looksLikeHotelStart(line, nextLine)) {
      pushHotel()
      currentHotelLines = [line]
      continue
    }

    if (currentHotelLines.length) {
      currentHotelLines.push(line)
    }
  }

  pushHotel()

  const filtered = categories.filter((category) => Array.isArray(category.hotels) && category.hotels.length)
  return filtered.length ? filtered : null
}

export { inferCityFromText }
