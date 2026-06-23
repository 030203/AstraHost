const { execFileSync } = require("node:child_process");

const MYSQL_PATH =
  process.env.ROOMOS_MYSQL_PATH || "C:\\Program Files\\MySQL\\MySQL Server 9.4\\bin\\mysql.exe";
const DB_NAME = process.env.ROOMOS_DB_NAME || "booking_system";
const DB_USER = process.env.ROOMOS_DB_USERNAME || "root";
const DB_PASSWORD = process.env.ROOMOS_DB_PASSWORD || process.env.MYSQL_PASSWORD || "456456";

const TARGET_NEW = Number(process.env.ROOMOS_IMPORT_TARGET || 100);
const CANDIDATES_PER_CITY = Number(process.env.ROOMOS_IMPORT_PER_CITY || 7);
const DETAIL_CONCURRENCY = Number(process.env.ROOMOS_DETAIL_CONCURRENCY || 5);
const MAX_IMAGES = Number(process.env.ROOMOS_IMPORT_MAX_IMAGES || 8);
const MIN_REVIEWS = Number(process.env.ROOMOS_IMPORT_MIN_REVIEWS || 150);
const MIN_RATING = Number(process.env.ROOMOS_IMPORT_MIN_RATING || 8.8);
const USD_TO_CNY = Number(process.env.ROOMOS_USD_TO_CNY || 7.2);

const CITY_SOURCES = [
  { slug: "shanghai", cityId: 2, province: "上海", city: "上海" },
  { slug: "beijing", cityId: 1, province: "北京", city: "北京" },
  { slug: "shenzhen", cityId: 30, province: "广东", city: "深圳" },
  { slug: "guangzhou", cityId: 32, province: "广东", city: "广州" },
  { slug: "hangzhou", cityId: 17, province: "浙江", city: "杭州" },
  { slug: "chengdu", cityId: 28, province: "四川", city: "成都" },
  { slug: "nanjing", cityId: 12, province: "江苏", city: "南京" },
  { slug: "suzhou", cityId: 14, province: "江苏", city: "苏州" },
  { slug: "wuhan", cityId: 477, province: "湖北", city: "武汉" },
  { slug: "chongqing", cityId: 4, province: "重庆", city: "重庆" },
  { slug: "tianjin", cityId: 3, province: "天津", city: "天津" },
  { slug: "qingdao", cityId: 7, province: "山东", city: "青岛" },
  { slug: "xiamen", cityId: 25, province: "福建", city: "厦门" },
  { slug: "kunming", cityId: 34, province: "云南", city: "昆明" },
  { slug: "sanya", cityId: 43, province: "海南", city: "三亚" },
  { slug: "changsha", cityId: 206, province: "湖南", city: "长沙" },
  { slug: "zhengzhou", cityId: 559, province: "河南", city: "郑州" },
  { slug: "ningbo", cityId: 375, province: "浙江", city: "宁波" },
  { slug: "jinan", cityId: 144, province: "山东", city: "济南" },
  { slug: "harbin", cityId: 5, province: "黑龙江", city: "哈尔滨" },
  { slug: "dalian", cityId: 6, province: "辽宁", city: "大连" },
  { slug: "fuzhou", cityId: 258, province: "福建", city: "福州" },
  { slug: "shenyang", cityId: 451, province: "辽宁", city: "沈阳" },
  { slug: "hefei", cityId: 278, province: "安徽", city: "合肥" },
];

const REQUEST_HEADERS = {
  "user-agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
  "accept-language": "en-US,en;q=0.9",
};

const FACILITY_TRANSLATIONS = {
  "24-hour front desk": "24小时前台",
  "Airport drop-off": "送机服务",
  "Airport pick-up": "接机服务",
  Bar: "酒吧",
  Breakfast: "早餐",
  Cafe: "咖啡厅",
  Currency: "货币兑换",
  Elevator: "电梯",
  Gym: "健身房",
  Parking: "停车场",
  Restaurant: "餐厅",
  WiFi: "Wi-Fi",
  "Business center": "商务中心",
  "Car rentals": "租车服务",
  "Children's playground": "儿童乐园",
  "Conference room": "会议室",
  "Laundry room": "洗衣房",
  "Luggage storage": "行李寄存",
  "Public parking": "公共停车场",
  "Room service": "客房服务",
  "Service robots": "机器人服务",
  "Station pick-up service": "接站服务",
  "Taxi booking service": "叫车服务",
  "Tea room": "茶室",
  "Wake-up call": "叫醒服务",
};

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function normalizeWhitespace(value) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .trim();
}

function limitLength(value, max) {
  const text = normalizeWhitespace(value);
  if (text.length <= max) {
    return text;
  }
  return text.slice(0, max);
}

function normalizeCompareText(value) {
  return normalizeWhitespace(value)
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[\s\-_()（）[\]【】,.，。:：;；'"/\\|]/g, "");
}

function normalizeAddressCompare(value) {
  return normalizeWhitespace(value)
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[\s,.，。:：;；'"/\\|]/g, "");
}

function uniq(values) {
  const seen = new Set();
  const result = [];
  for (const item of values) {
    const value = normalizeWhitespace(item);
    if (!value || seen.has(value)) {
      continue;
    }
    seen.add(value);
    result.push(value);
  }
  return result;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function parseNumber(value, fallback = 0) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function roundPrice(value) {
  return Math.max(0, Math.round(value / 10) * 10);
}

function qualityScore(seed) {
  return parseNumber(seed.rating) * 100000 + parseNumber(seed.votes) * 10 + (seed.pictureList?.length || 0);
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
      env: { ...process.env, MYSQL_PWD: DB_PASSWORD },
      stdio: ["ignore", "pipe", "pipe"],
    }
  ).trim();
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
        await sleep(350 * attempt);
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

function seoListUrl(cityConfig) {
  return `https://www.trip.com/hotels/${cityConfig.slug}-hotels-list-${cityConfig.cityId}/`;
}

function parseHotelsFromSeoList(html) {
  const raw = extractJsonValue(html, "hotels");
  if (!raw) {
    throw new Error("Could not extract hotels list JSON");
  }
  const hotels = JSON.parse(raw);
  return hotels
    .filter((hotel) => {
      return (
        parseNumber(hotel.rating) >= MIN_RATING &&
        parseNumber(hotel.votes) >= MIN_REVIEWS &&
        Array.isArray(hotel.pictureList) &&
        hotel.pictureList.length >= 3 &&
        hotel.hotelJumpUrl
      );
    })
    .sort((left, right) => qualityScore(right) - qualityScore(left));
}

async function parseHotelDetail(url) {
  try {
    const html = await fetchText(url);
    const candidates = [];
    const raw = extractJsonValue(html, "hotelDetailResponse");
    if (raw) {
      candidates.push(raw);
    }
    const normalized = html.replace(/\\"/g, '"');
    const normalizedRaw = extractJsonValue(normalized, "hotelDetailResponse");
    if (normalizedRaw) {
      candidates.push(normalizedRaw);
    }
    for (const item of candidates) {
      try {
        return JSON.parse(item);
      } catch (error) {
        continue;
      }
    }
  } catch (error) {
    return null;
  }
  return null;
}

function bestImageUrl(image) {
  if (!image) {
    return "";
  }
  if (Array.isArray(image.diffPositionUrls) && image.diffPositionUrls.length) {
    const direct =
      image.diffPositionUrls.find((item) => item.position === 1)?.picUrl ||
      image.diffPositionUrls.find((item) => item.position === 28)?.picUrl ||
      image.diffPositionUrls[0]?.picUrl;
    if (direct) {
      return direct;
    }
  }
  return image.imgUrl || image.pictureUrl || image.picUrl || image.url || "";
}

function facilityLabel(value) {
  return FACILITY_TRANSLATIONS[value] || value;
}

function buildFacilities(seed, detail) {
  const fromDetail =
    detail?.hotelFacilityPopV2?.hotelPopularFacility?.list?.map((item) => facilityLabel(item.facilityDesc)) || [];
  const fromList = (seed.hotelHotFacilityTags || []).map((item) => facilityLabel(item.facilityName));
  return uniq([...fromDetail, ...fromList]).slice(0, 12);
}

function parseTimeFromDetail(detail, type) {
  const entries = detail?.hotelPolicyInfo?.checkInAndOut?.content || [];
  const target = type === "checkIn" ? /check-in/i : /check-out/i;
  const raw =
    entries.find((item) => target.test(item.title || ""))?.description ||
    (type === "checkIn" ? "After 14:00" : "Before 12:00");
  const match = String(raw).match(/(\d{1,2}):(\d{2})/);
  if (!match) {
    return type === "checkIn" ? "14:00:00" : "12:00:00";
  }
  return `${String(match[1]).padStart(2, "0")}:${String(match[2]).padStart(2, "0")}:00`;
}

function buildPolicies(seed, detail) {
  const policies = [];
  const checkInTime = parseTimeFromDetail(detail, "checkIn");
  const checkOutTime = parseTimeFromDetail(detail, "checkOut");
  policies.push(`入住时间 ${checkInTime.slice(0, 5)}，退房时间 ${checkOutTime.slice(0, 5)}。`);

  const breakfastEntries = detail?.hotelPolicyInfo?.breakfast?.content || [];
  const breakfastSummary = breakfastEntries
    .map((item) => [item.title, item.description].filter(Boolean).join(": "))
    .map((item) => normalizeWhitespace(item))
    .filter(Boolean)
    .slice(0, 3);
  if (breakfastSummary.length) {
    policies.push(`早餐信息：${breakfastSummary.join("；")}`);
  }

  const childPolicies = (detail?.hotelPolicyInfo?.childPolicy?.content || [])
    .map((item) => normalizeWhitespace(item.description))
    .filter(Boolean)
    .slice(0, 2);
  if (childPolicies.length) {
    policies.push(`儿童政策：${childPolicies.join("；")}`);
  }

  const guestPolicy = normalizeWhitespace(detail?.hotelPolicyInfo?.guestLimit?.content?.[0]?.description);
  if (guestPolicy) {
    policies.push(`接待政策：${guestPolicy}`);
  }

  const fallback = [
    "实际入住政策请以下单页实时说明为准。",
    "房型价格和早餐方案可能随日期变化。",
  ];

  if (!detail) {
    policies.push(...fallback);
  } else if (policies.length < 3) {
    policies.push(...fallback.slice(0, 3 - policies.length));
  }

  return uniq(policies).slice(0, 8);
}

function pickPropertyImages(seed, detail) {
  const topImages = (detail?.hotelTopImage?.imgUrlList || []).map(bestImageUrl);
  const listImages = (seed.pictureList || []).map((item) => item.pictureUrl);
  const fallback = seed.imgUrl ? [seed.imgUrl] : [];
  return uniq([...topImages, ...listImages, ...fallback]).slice(0, MAX_IMAGES);
}

function pickRoomImages(seed, propertyImages) {
  const fromList = (seed.pictureList || [])
    .filter((item) => /room/i.test(item.pictureTypeName || ""))
    .map((item) => item.pictureUrl);
  const merged = uniq([...fromList, ...propertyImages]);
  return merged.length ? merged : propertyImages;
}

function buildDescription(seed, detail, cityConfig, facilities) {
  const baseName = normalizeWhitespace(detail?.hotelBaseInfo?.nameInfo?.name || seed.hotelName);
  const nearPoi =
    detail?.hotelPositionInfo?.placeInfo?.poiList?.[0]?.poiName ||
    detail?.hotelPositionInfo?.zoneName ||
    seed.zoneName ||
    seed.districtName ||
    cityConfig.city;
  const reviewCount = parseNumber(detail?.hotelComment?.comment?.totalComment || seed.votes);
  const ratingTen = parseNumber(detail?.hotelComment?.comment?.score || seed.rating);
  const detailIntro = (detail?.hotelDescriptionInfo?.sectionList || [])
    .map((item) => normalizeWhitespace(item.desc))
    .filter(Boolean)
    .slice(0, 2)
    .join(" ");

  const sections = [
    `${baseName}位于${cityConfig.city}${nearPoi ? `，靠近${nearPoi}` : ""}，适合商务出行、城市观光与短住休闲。`,
  ];
  if (detailIntro) {
    sections.push(detailIntro);
  } else if (seed.brief) {
    sections.push(normalizeWhitespace(seed.brief));
  }
  sections.push(
    `公开页面显示住客评分约${(ratingTen / 2).toFixed(1)} / 5，累计评价约${reviewCount}条。`
  );
  if (facilities.length) {
    sections.push(`常见配套包括${facilities.slice(0, 6).join("、")}。`);
  }
  return normalizeWhitespace(sections.join(" ")).slice(0, 900);
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
          { name: "豪华双床房", bed: "2张单人床", size: 42, occupancy: 2, multiplier: 1.14, inventory: 5, extras: ["小冰箱"] },
          { name: "行政大床房", bed: "1张特大床", size: 48, occupancy: 2, multiplier: 1.32, inventory: 4, extras: ["沙发"] },
          { name: "景观套房", bed: "1张特大床", size: 62, occupancy: 3, multiplier: 1.65, inventory: 3, extras: ["会客区"] },
        ]
      : star >= 4
      ? [
          { name: "标准大床房", bed: "1张大床", size: 30, occupancy: 2, multiplier: 1.0, inventory: 6, extras: ["书桌"] },
          { name: "高级双床房", bed: "2张单人床", size: 34, occupancy: 2, multiplier: 1.12, inventory: 5, extras: ["小冰箱"] },
          { name: "豪华大床房", bed: "1张特大床", size: 40, occupancy: 2, multiplier: 1.26, inventory: 4, extras: ["沙发"] },
          { name: "行政套房", bed: "1张特大床", size: 54, occupancy: 3, multiplier: 1.56, inventory: 2, extras: ["会客区"] },
        ]
      : [
          { name: "舒适大床房", bed: "1张大床", size: 26, occupancy: 2, multiplier: 1.0, inventory: 5, extras: ["书桌"] },
          { name: "高级双床房", bed: "2张单人床", size: 30, occupancy: 2, multiplier: 1.1, inventory: 4, extras: ["小冰箱"] },
          { name: "家庭房", bed: "1张大床和1张单人床", size: 38, occupancy: 3, multiplier: 1.34, inventory: 3, extras: ["沙发"] },
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
      amenities,
      images: uniq([imagePrimary, imageSecondary]).slice(0, 2),
      inventory: template.inventory,
      status: "ACTIVE",
      sortOrder: index,
    };
  });
}

function buildPropertyPayload(seed, detail, cityConfig) {
  const facilities = buildFacilities(seed, detail);
  const propertyImages = pickPropertyImages(seed, detail);
  const roomImages = pickRoomImages(seed, propertyImages);
  const displayPriceUsd = parseNumber(seed.displayPrice?.taxPrice || seed.displayPrice?.price || seed.prices?.priceInfos?.[0]?.price, 0);
  const baseNightlyPrice = Math.max(
    parseNumber(seed.star) >= 5 ? 980 : parseNumber(seed.star) >= 4 ? 520 : 280,
    roundPrice((displayPriceUsd || 40) * USD_TO_CNY)
  );
  const roomPlans = buildRoomPlans(seed, facilities, roomImages, baseNightlyPrice);
  const totalRooms = roomPlans.reduce((sum, item) => sum + item.inventory, 0);
  const minPrice = Math.min(...roomPlans.map((item) => item.basePrice));
  const maxPrice = Math.max(...roomPlans.map((item) => item.basePrice));
  const ratingFive = clamp(Number((parseNumber(detail?.hotelComment?.comment?.score || seed.rating, 9) / 2).toFixed(2)), 3.8, 5);
  const totalReviews = parseNumber(detail?.hotelComment?.comment?.totalComment || seed.votes);
  const address = normalizeWhitespace(
    detail?.hotelPositionInfo?.address ||
      seed.address ||
      `${cityConfig.city}${seed.districtName ? seed.districtName : ""}${seed.zoneName ? ` ${seed.zoneName}` : ""}`
  );

  return {
    property: {
      propertyName: limitLength(detail?.hotelBaseInfo?.nameInfo?.name || seed.hotelName, 100),
      propertyType: "HOTEL",
      description: buildDescription(seed, detail, cityConfig, facilities),
      address,
      province: cityConfig.province,
      city: cityConfig.city,
      district: limitLength(seed.districtName || detail?.hotelPositionInfo?.zoneName || "", 50),
      longitude: parseNumber(seed.lon, 0),
      latitude: parseNumber(seed.lat, 0),
      checkInTime: parseTimeFromDetail(detail, "checkIn"),
      checkOutTime: parseTimeFromDetail(detail, "checkOut"),
      totalRooms,
      availableRooms: totalRooms,
      rating: ratingFive,
      totalReviews,
      priceRangeMin: minPrice,
      priceRangeMax: maxPrice,
      facilities,
      images: propertyImages,
      policies: buildPolicies(seed, detail),
      status: "APPROVED",
      isFeatured: ratingFive >= 4.75 || totalReviews >= 5000,
      viewCount: 0,
    },
    roomPlans,
  };
}

function buildInsertSql(merchantId, payload) {
  const property = payload.property;
  const roomPlans = payload.roomPlans;
  const statements = [
    "START TRANSACTION",
    `INSERT INTO properties (
merchant_id, property_name, property_type, description, address, province, city, district,
longitude, latitude, check_in_time, check_out_time, total_rooms, available_rooms, rating, total_reviews,
price_range_min, price_range_max, facilities, images, policies, status, is_featured, view_count, created_at, updated_at
) VALUES (
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
)`,
    "SET @property_id := LAST_INSERT_ID()",
  ];

  let roomOffset = 0;
  roomPlans.forEach((plan, index) => {
    const roomTypeVar = `@room_type_id_${index + 1}`;
    statements.push(
      `INSERT INTO room_types (
property_id, type_name, description, max_occupancy, bed_type, room_size, amenities, images, base_price, status, sort_order, created_at, updated_at
) VALUES (
@property_id,
${sqlString(limitLength(plan.typeName, 50))},
${sqlString(plan.description)},
${sqlString(plan.maxOccupancy)},
${sqlString(limitLength(plan.bedType, 50))},
${sqlString(plan.roomSize)},
${sqlString(JSON.stringify(plan.amenities))},
${sqlString(JSON.stringify(plan.images))},
${sqlString(plan.basePrice)},
${sqlString(plan.status)},
${sqlString(plan.sortOrder)},
NOW(),
NOW()
)`,
      `SET ${roomTypeVar} := LAST_INSERT_ID()`
    );

    const roomValues = [];
    for (let roomIndex = 0; roomIndex < plan.inventory; roomIndex += 1) {
      const serial = roomOffset + roomIndex;
      const floor = 3 + Math.floor(serial / 10);
      const roomSequence = String((serial % 10) + 1).padStart(2, "0");
      roomValues.push(
        `(@property_id, ${roomTypeVar}, ${sqlString(`${floor}${roomSequence}`)}, ${sqlString(floor)}, 'AVAILABLE', NOW(), NOW())`
      );
    }
    roomOffset += plan.inventory;
    statements.push(
      `INSERT INTO rooms (property_id, room_type_id, room_number, floor_number, status, created_at, updated_at) VALUES
${roomValues.join(",\n")}`
    );
  });

  statements.push("COMMIT", "SELECT @property_id");
  return `${statements.join(";\n")};`;
}

function resolveMerchantId() {
  const preferred = process.env.ROOMOS_IMPORT_MERCHANT_ID || "178";
  const preferredExists = runMysql(
    `SELECT COUNT(*) FROM merchants WHERE id = ${sqlString(preferred)} AND status = 'APPROVED'`
  );
  if (preferredExists === "1") {
    return Number(preferred);
  }
  const fallback = runMysql("SELECT id FROM merchants WHERE status = 'APPROVED' ORDER BY id LIMIT 1");
  if (!fallback) {
    throw new Error("No approved merchant available");
  }
  return Number(fallback);
}

function loadExistingRecords() {
  const output = runMysql(
    "SELECT id, property_name, city, IFNULL(address,''), IFNULL(longitude,''), IFNULL(latitude,'') FROM properties"
  );
  if (!output) {
    return [];
  }
  return output
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => {
      const [id, propertyName, city, address, longitude, latitude] = line.split("\t");
      return {
        id: Number(id),
        propertyName,
        city,
        address,
        longitude: parseNumber(longitude, null),
        latitude: parseNumber(latitude, null),
      };
    });
}

function buildDuplicateIndex(records) {
  const nameCity = new Set();
  const addressCity = new Set();
  const coords = [];

  const add = (record) => {
    const city = normalizeCompareText(record.city);
    if (!city) {
      return;
    }
    const nameKey = `${city}|${normalizeCompareText(record.propertyName)}`;
    if (!nameKey.endsWith("|")) {
      nameCity.add(nameKey);
    }
    const addressKey = `${city}|${normalizeAddressCompare(record.address)}`;
    if (!addressKey.endsWith("|")) {
      addressCity.add(addressKey);
    }
    if (Number.isFinite(record.longitude) && Number.isFinite(record.latitude)) {
      coords.push({
        city,
        longitude: Number(record.longitude),
        latitude: Number(record.latitude),
      });
    }
  };

  const match = (record) => {
    const city = normalizeCompareText(record.city);
    const nameKey = `${city}|${normalizeCompareText(record.propertyName)}`;
    if (nameCity.has(nameKey)) {
      return "name+city";
    }
    const addressKey = `${city}|${normalizeAddressCompare(record.address)}`;
    if (normalizeAddressCompare(record.address) && addressCity.has(addressKey)) {
      return "address+city";
    }
    if (Number.isFinite(record.longitude) && Number.isFinite(record.latitude)) {
      const hit = coords.find((item) => {
        return (
          item.city === city &&
          Math.abs(item.longitude - record.longitude) < 0.001 &&
          Math.abs(item.latitude - record.latitude) < 0.001
        );
      });
      if (hit) {
        return "nearby-coordinates";
      }
    }
    return null;
  };

  records.forEach(add);
  return { add, match };
}

async function collectCandidateSeeds(index) {
  const candidates = [];
  const seenHotelIds = new Set();
  for (const cityConfig of CITY_SOURCES) {
    console.log(`Scanning city ${cityConfig.city}...`);
    const html = await fetchText(seoListUrl(cityConfig));
    const list = parseHotelsFromSeoList(html);
    let picked = 0;
    for (const seed of list) {
      const duplicateReason = index.match({
        propertyName: seed.hotelName,
        city: cityConfig.city,
        address: seed.address || seed.zoneName || seed.districtName || "",
        longitude: parseNumber(seed.lon, null),
        latitude: parseNumber(seed.lat, null),
      });
      if (duplicateReason || seenHotelIds.has(seed.hotelId)) {
        continue;
      }
      seenHotelIds.add(seed.hotelId);
      candidates.push({ cityConfig, seed });
      picked += 1;
      if (picked >= CANDIDATES_PER_CITY) {
        break;
      }
    }
  }
  return candidates.sort((left, right) => qualityScore(right.seed) - qualityScore(left.seed));
}

async function enrichCandidates(candidates) {
  const enriched = [];
  for (let index = 0; index < candidates.length; index += DETAIL_CONCURRENCY) {
    const batch = candidates.slice(index, index + DETAIL_CONCURRENCY);
    const result = await Promise.all(
      batch.map(async (item) => {
        const detail = await parseHotelDetail(item.seed.hotelJumpUrl);
        return { ...item, detail };
      })
    );
    enriched.push(...result);
    console.log(`Fetched details for ${Math.min(index + DETAIL_CONCURRENCY, candidates.length)}/${candidates.length}`);
  }
  return enriched;
}

async function main() {
  const merchantId = resolveMerchantId();
  const beforeHotels = parseNumber(runMysql("SELECT COUNT(*) FROM properties WHERE property_type = 'HOTEL'"), 0);
  const beforeProperties = parseNumber(runMysql("SELECT COUNT(*) FROM properties"), 0);
  const duplicateIndex = buildDuplicateIndex(loadExistingRecords());

  console.log(`Using merchant_id=${merchantId}`);
  console.log(`Current hotel count=${beforeHotels}, target new imports=${TARGET_NEW}`);

  const candidateSeeds = await collectCandidateSeeds(duplicateIndex);
  if (!candidateSeeds.length) {
    throw new Error("No candidate seeds collected");
  }

  const enrichedCandidates = await enrichCandidates(candidateSeeds);
  const imported = [];
  const skipped = [];

  for (const item of enrichedCandidates) {
    if (imported.length >= TARGET_NEW) {
      break;
    }

    const payload = buildPropertyPayload(item.seed, item.detail || {}, item.cityConfig);
    const duplicateReason = duplicateIndex.match(payload.property);
    if (duplicateReason) {
      skipped.push({ name: payload.property.propertyName, city: payload.property.city, reason: duplicateReason });
      continue;
    }

    const propertyId = Number(runMysql(buildInsertSql(merchantId, payload)).split(/\r?\n/).pop());
    duplicateIndex.add(payload.property);
    imported.push({
      propertyId,
      name: payload.property.propertyName,
      city: payload.property.city,
      rating: payload.property.rating,
      images: payload.property.images.length,
      facilities: payload.property.facilities.length,
      roomTypes: payload.roomPlans.length,
      rooms: payload.property.totalRooms,
      detailMode: item.detail ? "detail+list" : "list-only",
    });
    console.log(
      `Imported #${propertyId} ${payload.property.propertyName} (${payload.property.city}) [${item.detail ? "detail" : "list"}]`
    );
  }

  if (imported.length < TARGET_NEW) {
    console.warn(`Imported ${imported.length} new hotels, below target ${TARGET_NEW}.`);
  }

  const afterHotels = parseNumber(runMysql("SELECT COUNT(*) FROM properties WHERE property_type = 'HOTEL'"), 0);
  const afterProperties = parseNumber(runMysql("SELECT COUNT(*) FROM properties"), 0);
  const byCity = runMysql(
    `SELECT city, COUNT(*) FROM properties WHERE property_type='HOTEL' AND id > ${beforeProperties} GROUP BY city ORDER BY COUNT(*) DESC, city`
  );

  console.log("Summary:");
  console.log(`- properties: ${beforeProperties} -> ${afterProperties}`);
  console.log(`- hotels: ${beforeHotels} -> ${afterHotels}`);
  console.log(`- imported: ${imported.length}`);
  console.log(`- skipped: ${skipped.length}`);
  console.log("New hotels by city:");
  console.log(byCity || "(none)");
  console.log("Sample imports:");
  imported.slice(0, 15).forEach((item) => {
    console.log(
      `  [${item.propertyId}] ${item.city} ${item.name} / rating ${item.rating} / ${item.images} imgs / ${item.roomTypes} room types / ${item.rooms} rooms / ${item.detailMode}`
    );
  });
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
