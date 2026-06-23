"""Location name normalization utilities.

Strips common administrative suffixes from city/district names so that
user-provided names are more likely to match stored database values.

Examples:
    normalize_city_name("上海市")  -> "上海"
    normalize_city_name("北京")    -> "北京"
    normalize_district_name("浦东新区") -> "浦东"
    normalize_district_name("朝阳区")   -> "朝阳"
"""

CITY_SUFFIXES = (
    "市",
    "特别行政区",
    "自治州",
    "地区",
    "盟",
)

DISTRICT_SUFFIXES = (
    "区",
    "县",
    "县级市",
    "自治县",
    "旗",
)


def normalize_city_name(name):
    """Strip common city administrative suffixes.

    '上海市' -> '上海'
    '北京市' -> '北京'
    '香港特别行政区' -> '香港'
    """
    if not name or not isinstance(name, str):
        return name
    name = name.strip()
    for suffix in sorted(CITY_SUFFIXES, key=len, reverse=True):
        if name.endswith(suffix) and len(name) > len(suffix):
            return name[: -len(suffix)]
    return name


def normalize_district_name(name):
    """Strip common district administrative suffixes.

    '浦东新区' -> '浦东'
    '朝阳区' -> '朝阳'
    '延庆县' -> '延庆'
    """
    if not name or not isinstance(name, str):
        return name
    name = name.strip()
    for suffix in sorted(DISTRICT_SUFFIXES, key=len, reverse=True):
        if name.endswith(suffix) and len(name) > len(suffix):
            return name[: -len(suffix)]
    return name
