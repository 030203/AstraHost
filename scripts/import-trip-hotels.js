const { execFileSync } = require("node:child_process");

const MYSQL_PATH =
  process.env.ROOMOS_MYSQL_PATH || "C:\\Program Files\\MySQL\\MySQL Server 9.4\\bin\\mysql.exe";
const DB_NAME = process.env.ROOMOS_DB_NAME || "booking_system";
const DB_USER = process.env.ROOMOS_DB_USERNAME || "root";
const DB_PASSWORD = process.env.ROOMOS_DB_PASSWORD || process.env.MYSQL_PASSWORD || "456456";
const IMPORT_PER_CITY = Number(process.env.ROOMOS_IMPORT_PER_CITY || 2);
const MAX_IMAGES = Number(process.env.ROOMOS_IMPORT_MAX_IMAGES || 8);
const USD_TO_CNY = Number(process.env.ROOMOS_USD_TO_CNY || 7.2);

const CITY_SOURCES = [
  {
    province: "上海",
    city: "上海",
    listUrl: "https://www.trip.com/hotels/shanghai-hotels-list-2/",
  },
  {
    province: "北京",
    city: "北京",
    listUrl: "https://www.trip.com/hotels/beijing-hotels-list-1/",
  },
  {
    province: "广东",
    city: "深圳",
    listUrl: "https://www.trip.com/hotels/shenzhen-hotels-list-30/",
  },
  {
    province: "广东",
    city: "广州",
    listUrl: "https://www.trip.com/hotels/guangzhou-hotels-list-32/",
  },
  {
    province: "浙江",
    city: "杭州",
    listUrl: "https://www.trip.com/hotels/hangzhou-hotels-list-17/",
  },
  {
    province: "四川",
    city: "成都",
    listUrl: "https://www.trip.com/hotels/chengdu-hotels-list-28/",
  },
];

const REQUEST_HEADERS = {
  "user-agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
  "accept-language": "en-US,en;q=0.9",
};

const FACILITY_TRANSLATIONS = {
  "24-hour front desk": "24小时前台",
  "Airport pick-up": "接机服务",
  "Airport drop-off": "送机服务",
  Bar: "酒吧",
  Breakfast: "早餐",
  "Business center": "商务中心",
  Cafe: "咖啡厅",
  "Car rentals": "租车服务",
  "Children's playground": "儿童乐园",
  "Conference room": "会议室",
  Currency: "货币兑换",
  Elevator: "电梯",
  Gym: "健身房",
  "Laundry room": "洗衣房",
  "Luggage storage": "行李寄存",
  Parking: "停车场",
  "Public parking": "公共停车场",
  Restaurant: "餐厅",
  "Room service": "客房服务",
  "Service robots": "机器人服务",
  "Station pick-up service": "接站服务",
  "Taxi booking service": "叫车服务",
  "Tea room": "茶室",
  WiFi: "Wi-Fi",
  "Wake-up call": "叫醒服务",
};

const HIGHLIGHT_TRANSLATIONS = {
  "Airport drop-off available": "提供送机服务",
  "Clean and tidy": "环境整洁",
  "Delicious breakfast": "早餐口碑好",
  "Easy to reach": "交通便利",
  "Excellent Location": "位置出色",
  "Friendly front desk staff": "前台服务热情",
  "Great views": "景观视野佳",
  "Ideal location": "地段优越",
  "Lots to do": "周边配套丰富",
  "Most card payments accepted": "支持多种支付方式",
};

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchText(url) {
  let lastError = null;
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      const response = await fetch(url, { headers: REQUEST_HEADERS });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status} for ${url}`);
      }
      return await response.text();
    } catch (error) {
      lastError = error;
      if (attempt < 3) {
        await sleep(500 * attempt);
      }
    }
  }
  throw lastError;
}

function extractJsonValue(text, key) {
  const marker = `"${key}":`;
  const start = text.indexOf(marker);
  if (start < 0) {
    return null;
  }
  let index = start + marker.length;
  while (index < text.length && /\s/.test(text[index])) {
    index += 1;
  }
  const open = text[index];
  const close = open === "{" ? "}" : open === "[" ? "]" : null;
  if (!close) {
    return null;
  }
  const begin = index;
  let depth = 0;
  let inString = false;
  let escaped = false;
  for (; index < text.length; index += 1) {
    const ch = text[index];
    if (inString) {
      if (escaped) {
        escaped = false;
      } else if (ch === "\\") {
        escaped = true;
      } else if (ch === '"') {
        inString = false;
      }
      continue;
    }
    if (ch === '"') {
      inString = true;
      continue;
    }
    if (ch === open) {
      depth += 1;
    } else if (ch === close) {
      depth -= 1;
      if (depth === 0) {
        return text.slice(begin, index + 1);
      }
    }
  }
  return null;
}

function normalizeWhitespace(value) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .replace(/\s+([,.;:!?)])/g, "$1")
    .trim();
}

function uniq(values) {
  const seen = new Set();
  const result = [];
  for (const value of values) {
    const normalized = normalizeWhitespace(value);
    if (!normalized) {
      continue;
    }
    if (seen.has(normalized)) {
      continue;
    }
    seen.add(normalized);
    result.push(normalized);
  }
  return result;
}

function toChineseFacility(value) {
  return FACILITY_TRANSLATIONS[value] || value;
}

function toChineseHighlight(value) {
  return HIGHLIGHT_TRANSLATIONS[value] || value;
}

function sqlString(value) {
  if (value === null || value === undefined) {
    return "NULL";
  }
  if (typeof value === "number") {
    return Number.isFinite(value) ? String(value) : "NULL";
  }
  if (typeof value === "boolean") {
    return value ? "1" : "0";
  }
  return `'${String(value).replace(/\\/g, "\\\\").replace(/'/g, "''")}'`;
}

function runMysql(sql) {
  return execFileSync(
    MYSQL_PATH,
    ["--default-character-set=utf8mb4", "-N", "-B", "-u", DB_USER, DB_NAME, "-e", sql],
    {
      encoding: "utf8",
      env: {
        ...process.env,
        MYSQL_PWD: DB_PASSWORD,
      },
      stdio: ["ignore", "pipe", "pipe"],
    }
  ).trim();
}

function parseNumber(value, fallback = 0) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function roundPrice(value) {
  return Math.max(0, Math.round(value / 10) * 10);
}

function extractLocalName(nameInfo) {
  const tip = normalizeWhitespace(nameInfo?.localNameTip);
  if (!tip) {
    return "";
  }
  const match = tip.match(/[:：]\s*(.+)$/);
  return match ? normalizeWhitespace(match[1]) : "";
}

function bestImageUrl(image) {
  if (!image) {
    return "";
  }
  if (Array.isArray(image.diffPositionUrls)) {
    const preferred =
      image.diffPositionUrls.find((item) => item.position === 1)?.picUrl ||
      image.diffPositionUrls.find((item) => item.position === 28)?.picUrl ||
      image.diffPositionUrls[0]?.picUrl;
    if (preferred) {
      return preferred;
    }
  }
  return image.imgUrl || image.pictureUrl || image.picUrl || "";
}

function parseTimeFromPolicy(detail, type) {
  const entries = detail?.hotelPolicyInfo?.checkInAndOut?.content || [];
  const marker = type === "checkIn" ? /check-in/i : /check-out/i;
  const raw =
    entries.find((item) => marker.test(item.title || ""))?.description ||
    (type === "checkIn" ? "After 14:00" : "Before 12:00");
  const match = String(raw).match(/(\d{1,2}):(\d{2})/);
  if (!match) {
    return type === "checkIn" ? "14:00:00" : "12:00:00";
  }
  const hour = String(match[1]).padStart(2, "0");
  const minute = String(match[2]).padStart(2, "0");
  return `${hour}:${minute}:00`;
}

function buildFacilities(seed, detail) {
  const detailFacilities =
    detail?.hotelFacilityPopV2?.hotelPopularFacility?.list?.map((item) => item.facilityDesc) || [];
  const listFacilities = (seed.hotelHotFacilityTags || []).map((item) => item.facilityName);
  return uniq([...detailFacilities, ...listFacilities].map(toChineseFacility)).slice(0, 12);
}

function buildPolicies(detail) {
  const policies = [];
  const policyInfo = detail?.hotelPolicyInfo || {};

  const checkEntries = policyInfo.checkInAndOut?.content || [];
  const checkIn = checkEntries.find((item) => /check-in/i.test(item.title || ""))?.description;
  const checkOut = checkEntries.find((item) => /check-out/i.test(item.title || ""))?.description;
  const frontDesk = checkEntries.find((item) => /front desk/i.test(item.description || ""))?.description;
  if (checkIn || checkOut) {
    policies.push(
      `入住与退房：${checkIn ? `入住 ${normalizeWhitespace(checkIn)}` : ""}${
        checkIn && checkOut ? "；" : ""
      }${checkOut ? `退房 ${normalizeWhitespace(checkOut)}` : ""}`.trim()
    );
  }
  if (frontDesk) {
    policies.push(`前台服务：${normalizeWhitespace(frontDesk)}`);
  }

  const breakfastEntries = policyInfo.breakfast?.content || [];
  const cuisine = breakfastEntries.find((item) => item.title === "Cuisine")?.description;
  const style = breakfastEntries.find((item) => item.title === "Style")?.description;
  const hours = breakfastEntries.find((item) => item.title === "Opening hours")?.description;
  if (cuisine || style || hours) {
    policies.push(
      `早餐信息：${[cuisine, style, hours].map(normalizeWhitespace).filter(Boolean).join("；")}`
    );
  }

  const childDescriptions = (policyInfo.childPolicy?.content || [])
    .map((item) => normalizeWhitespace(item.description))
    .filter(Boolean);
  if (childDescriptions.length) {
    policies.push(`儿童政策：${childDescriptions.slice(0, 2).join("；")}`);
  }

  const guestDescription = normalizeWhitespace(policyInfo.guestLimit?.content?.[0]?.description);
  if (guestDescription) {
    policies.push(`接待政策：${guestDescription}`);
  }

  const cribDescription = normalizeWhitespace(policyInfo.cribAndExtraBed?.content?.[0]?.description);
  if (cribDescription) {
    policies.push(`加床与婴儿床：${cribDescription}`);
  }

  const petDescription = normalizeWhitespace(policyInfo.pet?.content?.[0]?.description);
  if (petDescription) {
    policies.push(`宠物政策：${petDescription}`);
  }

  return uniq(policies).slice(0, 8);
}

function buildDescription(seed, detail, cityConfig, facilities) {
  const localName = extractLocalName(detail?.hotelBaseInfo?.nameInfo);
  const name = localName || normalizeWhitespace(detail?.hotelBaseInfo?.nameInfo?.name) || seed.hotelName;
  const nearPoi =
    detail?.hotelPositionInfo?.placeInfo?.poiList?.[0]?.poiName ||
    detail?.hotelPositionInfo?.zoneName ||
    seed.zoneName;
  const openYear = normalizeWhitespace(detail?.hotelBaseInfo?.openYear || seed.openYear);
  const fitmentYear = normalizeWhitespace(detail?.hotelBaseInfo?.fitmentYear || seed.fitmentYear);
  const ratingTen = parseNumber(detail?.hotelComment?.comment?.score || seed.rating);
  const ratingFive = ratingTen > 0 ? (ratingTen / 2).toFixed(1) : "";
  const reviewCount = parseNumber(detail?.hotelComment?.comment?.totalComment || seed.votes);
  const highlights = uniq(
    (detail?.hotelBaseInfo?.highlights?.list || []).map((item) => toChineseHighlight(item.title || item.desc))
  ).slice(0, 3);

  const sections = [
    `${name}位于${cityConfig.city}${nearPoi ? `，靠近${nearPoi}` : ""}，适合商务出行和城市观光。`,
  ];
  if (openYear || fitmentYear) {
    const historyBits = [];
    if (openYear) {
      historyBits.push(`${openYear}年开业`);
    }
    if (fitmentYear && fitmentYear !== openYear) {
      historyBits.push(`${fitmentYear}年完成装修升级`);
    }
    if (historyBits.length) {
      sections.push(`${historyBits.join("，")}。`);
    }
  }
  if (ratingFive || reviewCount) {
    sections.push(
      `公开页面显示住客评分约${ratingFive || "4.5"} / 5${reviewCount ? `，累计评价约${reviewCount}条` : ""}。`
    );
  }
  if (highlights.length) {
    sections.push(`亮点包括${highlights.join("、")}。`);
  }
  if (facilities.length) {
    sections.push(`酒店常见配套有${facilities.slice(0, 6).join("、")}。`);
  }
  return normalizeWhitespace(sections.join(" "));
}

function pickPropertyImages(seed, detail) {
  const topImages = (detail?.hotelTopImage?.imgUrlList || []).map(bestImageUrl);
  const listImages = (seed.pictureList || []).map((item) => item.pictureUrl);
  const fallback = seed.imgUrl ? [seed.imgUrl] : [];
  return uniq([...topImages, ...listImages, ...fallback]).slice(0, MAX_IMAGES);
}

function pickRoomImages(seed, propertyImages) {
  const roomImages = (seed.pictureList || [])
    .filter((item) => /room/i.test(item.pictureTypeName || ""))
    .map((item) => item.pictureUrl);
  const images = uniq([...roomImages, ...propertyImages]);
  return images.length ? images : propertyImages;
}

function buildRoomAmenities(facilities, extras) {
  return uniq(["免费Wi-Fi", "空调", "独立卫浴", "电视", ...extras, ...facilities.slice(0, 2)]).slice(0, 6);
}

function buildRoomPlans(seed, facilities, roomImages, baseNightlyPrice) {
  const star = parseNumber(seed.star);
  const templates =
    star >= 5
      ? [
          { name: "高级大床房", bed: "1张大床", size: 36, occupancy: 2, multiplier: 1.0, inventory: 6, extras: ["书桌"] },
          { name: "豪华双床房", bed: "2张单人床", size: 42, occupancy: 2, multiplier: 1.15, inventory: 5, extras: ["沙发"] },
          { name: "行政大床房", bed: "1张特大床", size: 48, occupancy: 2, multiplier: 1.35, inventory: 4, extras: ["迷你吧"] },
          { name: "景观套房", bed: "1张特大床", size: 62, occupancy: 3, multiplier: 1.7, inventory: 3, extras: ["会客区"] },
        ]
      : star >= 4
      ? [
          { name: "标准大床房", bed: "1张大床", size: 30, occupancy: 2, multiplier: 1.0, inventory: 6, extras: ["书桌"] },
          { name: "高级双床房", bed: "2张单人床", size: 34, occupancy: 2, multiplier: 1.12, inventory: 5, extras: ["小冰箱"] },
          { name: "豪华大床房", bed: "1张特大床", size: 40, occupancy: 2, multiplier: 1.28, inventory: 4, extras: ["沙发"] },
          { name: "行政套房", bed: "1张特大床", size: 54, occupancy: 3, multiplier: 1.58, inventory: 2, extras: ["会客区"] },
        ]
      : [
          { name: "舒适大床房", bed: "1张大床", size: 26, occupancy: 2, multiplier: 1.0, inventory: 5, extras: ["书桌"] },
          { name: "高级双床房", bed: "2张单人床", size: 30, occupancy: 2, multiplier: 1.1, inventory: 4, extras: ["小冰箱"] },
          { name: "家庭房", bed: "1张大床和1张单人床", size: 38, occupancy: 3, multiplier: 1.35, inventory: 3, extras: ["沙发"] },
        ];

  return templates.map((template, index) => {
    const imagePrimary = roomImages[index % roomImages.length];
    const imageSecondary = roomImages[(index + 1) % roomImages.length];
    const amenities = buildRoomAmenities(facilities, template.extras);
    return {
      typeName: template.name,
      description: `${template.name}提供${amenities.slice(0, 4).join("、")}等常用配置，适合${
        template.occupancy === 2 ? "双人入住" : "家庭或多人同住"
      }。`,
      maxOccupancy: template.occupancy,
      bedType: template.bed,
      roomSize: template.size,
      basePrice: roundPrice(baseNightlyPrice * template.multiplier),
      amenities: amenities,
      images: uniq([imagePrimary, imageSecondary]).slice(0, 2),
      status: "ACTIVE",
      sortOrder: index,
      inventory: template.inventory,
    };
  });
}

function buildPropertyPayload(seed, detail, cityConfig) {
  const localName = extractLocalName(detail?.hotelBaseInfo?.nameInfo);
  const name =
    localName ||
    normalizeWhitespace(detail?.hotelBaseInfo?.nameInfo?.name) ||
    normalizeWhitespace(seed.hotelName) ||
    `${cityConfig.city}精选酒店`;
  const facilities = buildFacilities(seed, detail);
  const policies = buildPolicies(detail);
  const propertyImages = pickPropertyImages(seed, detail);
  const roomImages = pickRoomImages(seed, propertyImages);
  const basePriceUsd = parseNumber(seed.displayPrice?.taxPrice || seed.displayPrice?.price || seed.prices?.priceInfos?.[0]?.price, 0);
  const baseNightlyPrice = Math.max(
    parseNumber(seed.star) >= 5 ? 980 : parseNumber(seed.star) >= 4 ? 520 : 280,
    roundPrice((basePriceUsd || 40) * USD_TO_CNY)
  );
  const roomPlans = buildRoomPlans(seed, facilities, roomImages, baseNightlyPrice);
  const priceRangeMin = Math.min(...roomPlans.map((plan) => plan.basePrice));
  const priceRangeMax = Math.max(...roomPlans.map((plan) => plan.basePrice));
  const totalRooms = roomPlans.reduce((sum, plan) => sum + plan.inventory, 0);
  const ratingTen = parseNumber(detail?.hotelComment?.comment?.score || seed.rating, 9);
  const ratingFive = Math.max(3.8, Math.min(5, Number((ratingTen / 2).toFixed(2))));
  const totalReviews = parseNumber(detail?.hotelComment?.comment?.totalComment || seed.votes);
  const district = normalizeWhitespace(seed.districtName || detail?.hotelPositionInfo?.zoneName || "");

  return {
    property: {
      propertyName: name,
      propertyType: "HOTEL",
      description: buildDescription(seed, detail, cityConfig, facilities),
      address: normalizeWhitespace(detail?.hotelPositionInfo?.address || seed.address || `${cityConfig.city}核心商圈`),
      province: cityConfig.province,
      city: cityConfig.city,
      district,
      longitude: parseNumber(seed.lon, 0),
      latitude: parseNumber(seed.lat, 0),
      checkInTime: parseTimeFromPolicy(detail, "checkIn"),
      checkOutTime: parseTimeFromPolicy(detail, "checkOut"),
      totalRooms,
      availableRooms: totalRooms,
      rating: ratingFive,
      totalReviews,
      priceRangeMin,
      priceRangeMax,
      facilities,
      images: propertyImages,
      policies: policies.length ? policies : ["入住前请以页面实际政策为准。"],
      status: "APPROVED",
      isFeatured: ratingFive >= 4.75 || totalReviews >= 3000,
      viewCount: 0,
    },
    roomPlans,
  };
}

function buildRoomInsert(plan, roomTypeVar) {
  return `INSERT INTO room_types (
property_id, type_name, description, max_occupancy, bed_type, room_size, amenities, images, base_price, status, sort_order, created_at, updated_at
) VALUES (
@property_id,
${sqlString(plan.typeName)},
${sqlString(plan.description)},
${sqlString(plan.maxOccupancy)},
${sqlString(plan.bedType)},
${sqlString(plan.roomSize)},
${sqlString(JSON.stringify(plan.amenities))},
${sqlString(JSON.stringify(plan.images))},
${sqlString(plan.basePrice)},
${sqlString(plan.status)},
${sqlString(plan.sortOrder)},
NOW(),
NOW()
);
SET ${roomTypeVar} := LAST_INSERT_ID();`;
}

function buildRoomValues(plan, roomTypeVar, startOffset) {
  const values = [];
  for (let index = 0; index < plan.inventory; index += 1) {
    const serial = startOffset + index;
    const floor = 3 + Math.floor(serial / 10);
    const roomSequence = String((serial % 10) + 1).padStart(2, "0");
    const roomNumber = `${floor}${roomSequence}`;
    values.push(
      `(@property_id, ${roomTypeVar}, ${sqlString(roomNumber)}, ${sqlString(floor)}, 'AVAILABLE', NOW(), NOW())`
    );
  }
  return values.join(",\n");
}

function buildUpsertSql(merchantId, payload) {
  const property = payload.property;
  const roomPlans = payload.roomPlans;
  const statements = [];
  statements.push("START TRANSACTION");
  statements.push(
    `SET @existing_id := (SELECT id FROM properties WHERE merchant_id = ${sqlString(
      merchantId
    )} AND property_name = ${sqlString(property.propertyName)} AND city = ${sqlString(property.city)} LIMIT 1)`
  );
  statements.push(
    `INSERT INTO properties (
merchant_id, property_name, property_type, description, address, province, city, district,
longitude, latitude, check_in_time, check_out_time, total_rooms, available_rooms, rating, total_reviews,
price_range_min, price_range_max, facilities, images, policies, status, is_featured, view_count, created_at, updated_at
) SELECT
${sqlString(merchantId)},
${sqlString(property.propertyName)},
${sqlString(property.propertyType)},
${sqlString(property.description)},
${sqlString(property.address)},
${sqlString(property.province)},
${sqlString(property.city)},
${sqlString(property.district || null)},
${sqlString(property.longitude)},
${sqlString(property.latitude)},
${sqlString(property.checkInTime)},
${sqlString(property.checkOutTime)},
${sqlString(property.totalRooms)},
${sqlString(property.availableRooms)},
${sqlString(property.rating)},
${sqlString(property.totalReviews)},
${sqlString(property.priceRangeMin)},
${sqlString(property.priceRangeMax)},
${sqlString(JSON.stringify(property.facilities))},
${sqlString(JSON.stringify(property.images))},
${sqlString(JSON.stringify(property.policies))},
${sqlString(property.status)},
${sqlString(property.isFeatured)},
${sqlString(property.viewCount)},
NOW(),
NOW()
FROM DUAL
WHERE @existing_id IS NULL`
  );
  statements.push("SET @property_id := COALESCE(@existing_id, LAST_INSERT_ID())");
  statements.push(
    `UPDATE properties SET
merchant_id = ${sqlString(merchantId)},
property_name = ${sqlString(property.propertyName)},
property_type = ${sqlString(property.propertyType)},
description = ${sqlString(property.description)},
address = ${sqlString(property.address)},
province = ${sqlString(property.province)},
city = ${sqlString(property.city)},
district = ${sqlString(property.district || null)},
longitude = ${sqlString(property.longitude)},
latitude = ${sqlString(property.latitude)},
check_in_time = ${sqlString(property.checkInTime)},
check_out_time = ${sqlString(property.checkOutTime)},
total_rooms = ${sqlString(property.totalRooms)},
available_rooms = ${sqlString(property.availableRooms)},
rating = ${sqlString(property.rating)},
total_reviews = ${sqlString(property.totalReviews)},
price_range_min = ${sqlString(property.priceRangeMin)},
price_range_max = ${sqlString(property.priceRangeMax)},
facilities = ${sqlString(JSON.stringify(property.facilities))},
images = ${sqlString(JSON.stringify(property.images))},
policies = ${sqlString(JSON.stringify(property.policies))},
status = ${sqlString(property.status)},
is_featured = ${sqlString(property.isFeatured)},
view_count = ${sqlString(property.viewCount)},
updated_at = NOW()
WHERE id = @property_id`
  );
  statements.push("DELETE FROM rooms WHERE property_id = @property_id");
  statements.push("DELETE FROM room_types WHERE property_id = @property_id");

  let roomOffset = 0;
  roomPlans.forEach((plan, index) => {
    const roomTypeVar = `@room_type_id_${index + 1}`;
    statements.push(buildRoomInsert(plan, roomTypeVar));
    statements.push(
      `INSERT INTO rooms (
property_id, room_type_id, room_number, floor_number, status, created_at, updated_at
) VALUES
${buildRoomValues(plan, roomTypeVar, roomOffset)}`
    );
    roomOffset += plan.inventory;
  });

  statements.push("COMMIT");
  statements.push("SELECT @property_id");
  return `${statements.join(";\n")};`;
}

function parseHotelsFromList(html) {
  const raw = extractJsonValue(html, "hotels");
  if (!raw) {
    throw new Error("Could not locate hotel list JSON");
  }
  const hotels = JSON.parse(raw);
  return hotels.filter((hotel) => {
    return (
      parseNumber(hotel.votes) >= 150 &&
      Array.isArray(hotel.pictureList) &&
      hotel.pictureList.length >= 3 &&
      parseNumber(hotel.rating) > 0 &&
      hotel.hotelJumpUrl
    );
  });
}

async function parseHotelDetail(url) {
  const html = await fetchText(url);
  const candidates = [];
  const directRaw = extractJsonValue(html, "hotelDetailResponse");
  if (directRaw) {
    candidates.push(directRaw);
  }
  const normalized = html.replace(/\\"/g, '"');
  const normalizedRaw = extractJsonValue(normalized, "hotelDetailResponse");
  if (normalizedRaw) {
    candidates.push(normalizedRaw);
  }
  for (const raw of candidates) {
    try {
      return JSON.parse(raw);
    } catch (error) {
      continue;
    }
  }
  if (!candidates.length) {
    return null;
  }
  throw new Error("Unable to parse hotel detail JSON");
}

function resolveMerchantId() {
  const preferred = process.env.ROOMOS_IMPORT_MERCHANT_ID || "178";
  const preferredExists = runMysql(
    `SELECT COUNT(*) FROM merchants WHERE id = ${sqlString(preferred)} AND status = 'APPROVED'`
  );
  if (preferredExists === "1") {
    return Number(preferred);
  }
  const fallback = runMysql(
    "SELECT id FROM merchants WHERE status = 'APPROVED' ORDER BY id LIMIT 1"
  );
  if (!fallback) {
    throw new Error("No approved merchant available for imported hotels");
  }
  return Number(fallback);
}

async function collectHotels() {
  const results = [];
  for (const cityConfig of CITY_SOURCES) {
    console.log(`Fetching list for ${cityConfig.city}...`);
    const html = await fetchText(cityConfig.listUrl);
    const hotels = parseHotelsFromList(html).slice(0, IMPORT_PER_CITY);
    for (const seed of hotels) {
      console.log(`  Crawling detail: ${seed.hotelName}`);
      let detail = null;
      try {
        detail = await parseHotelDetail(seed.hotelJumpUrl);
      } catch (error) {
        console.warn(`  Detail crawl failed for ${seed.hotelName}: ${error.message}`);
      }
      results.push({
        cityConfig,
        seed,
        detail,
      });
      await sleep(250);
    }
  }
  return results;
}

async function main() {
  const merchantId = resolveMerchantId();
  console.log(`Using merchant_id=${merchantId}`);

  const crawled = await collectHotels();
  if (!crawled.length) {
    throw new Error("No hotels were collected");
  }

  const imported = [];
  for (const item of crawled) {
    const payload = buildPropertyPayload(item.seed, item.detail || {}, item.cityConfig);
    const propertyId = Number(runMysql(buildUpsertSql(merchantId, payload)).split(/\r?\n/).pop());
    imported.push({
      propertyId,
      name: payload.property.propertyName,
      city: payload.property.city,
      images: payload.property.images.length,
      roomTypes: payload.roomPlans.length,
      rooms: payload.property.totalRooms,
    });
    console.log(
      `Imported #${propertyId} ${payload.property.propertyName} (${payload.property.city}) with ${payload.property.images.length} images, ${payload.roomPlans.length} room types and ${payload.property.totalRooms} rooms`
    );
  }

  const summary = runMysql(
    "SELECT COUNT(*), SUM(property_type = 'HOTEL'), SUM(status = 'APPROVED') FROM properties"
  );
  console.log("Property totals (all, hotels, approved):", summary);
  console.log("Imported hotels:");
  for (const item of imported) {
    console.log(
      `- [${item.propertyId}] ${item.name} / ${item.city} / ${item.images} images / ${item.roomTypes} room types / ${item.rooms} rooms`
    );
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
