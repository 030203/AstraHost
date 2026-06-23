package com.booking.system.service;

import com.booking.system.controller.dto.PropertySearchItemResponse;
import com.booking.system.controller.dto.PropertySearchReindexResponse;
import com.booking.system.controller.dto.PropertySearchRequest;
import com.booking.system.controller.dto.PropertySearchResponse;
import com.booking.system.entity.Property;
import com.booking.system.mapper.PropertyRepository;
import com.booking.system.search.PropertySearchDocument;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.data.elasticsearch.core.ElasticsearchOperations;
import org.springframework.data.elasticsearch.core.IndexOperations;
import org.springframework.data.elasticsearch.core.SearchHits;
import org.springframework.data.elasticsearch.core.geo.GeoPoint;
import org.springframework.data.elasticsearch.core.query.GeoDistanceOrder;
import org.springframework.data.elasticsearch.core.query.StringQuery;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.stream.Collectors;

@Slf4j
@Service
public class PropertySearchService {

    private static final int MAX_PAGE_SIZE = 50;
    private static final double EARTH_RADIUS_KM = 6371.0088d;

    @Value("${roomos.search.es.enabled:true}")
    private boolean elasticsearchEnabled;

    @Autowired
    private PropertyRepository propertyRepository;

    @Autowired(required = false)
    private ElasticsearchOperations elasticsearchOperations;

    @Autowired
    private ObjectMapper objectMapper;

    private final AtomicBoolean indexReady = new AtomicBoolean(false);

    public PropertySearchResponse search(PropertySearchRequest request) {
        PropertySearchRequest normalized = normalize(request);
        if (!canUseElasticsearch()) {
            return fallbackSearch(normalized, false);
        }

        try {
            ensureIndex();
            return searchWithElasticsearch(normalized);
        } catch (Exception ex) {
            log.warn("Elasticsearch search unavailable, falling back to database filtering", ex);
            return fallbackSearch(normalized, false);
        }
    }

    public void syncProperty(Property property) {
        if (!canUseElasticsearch() || property == null || property.getId() == null) {
            return;
        }

        try {
            ensureIndex();
            if (property.getStatus() == Property.PropertyStatus.APPROVED) {
                elasticsearchOperations.save(toDocument(property));
            } else {
                elasticsearchOperations.delete(String.valueOf(property.getId()), PropertySearchDocument.class);
            }
        } catch (Exception ex) {
            log.warn("Failed to sync property {} to Elasticsearch", property.getId(), ex);
        }
    }

    public void removeProperty(Long propertyId) {
        if (!canUseElasticsearch() || propertyId == null) {
            return;
        }

        try {
            ensureIndex();
            elasticsearchOperations.delete(String.valueOf(propertyId), PropertySearchDocument.class);
        } catch (Exception ex) {
            log.warn("Failed to remove property {} from Elasticsearch", propertyId, ex);
        }
    }

    public PropertySearchReindexResponse reindexAll() {
        if (!canUseElasticsearch()) {
            return new PropertySearchReindexResponse(0, 0, false);
        }

        int indexedCount = 0;
        int removedCount = 0;
        try {
            ensureIndex();
            for (Property property : propertyRepository.findAll()) {
                try {
                    if (property.getStatus() == Property.PropertyStatus.APPROVED) {
                        elasticsearchOperations.save(toDocument(property));
                        indexedCount++;
                    } else if (property.getId() != null) {
                        elasticsearchOperations.delete(String.valueOf(property.getId()), PropertySearchDocument.class);
                        removedCount++;
                    }
                } catch (Exception ex) {
                    log.warn("Skipped property {} while rebuilding Elasticsearch index", property.getId(), ex);
                }
            }
            IndexOperations indexOperations = elasticsearchOperations.indexOps(PropertySearchDocument.class);
            indexOperations.refresh();
            return new PropertySearchReindexResponse(indexedCount, removedCount, true);
        } catch (Exception ex) {
            log.warn("Failed to rebuild Elasticsearch property index", ex);
            return new PropertySearchReindexResponse(indexedCount, removedCount, false);
        }
    }

    private PropertySearchResponse searchWithElasticsearch(PropertySearchRequest request) {
        Sort sort = buildSort(request);
        PageRequest pageable = PageRequest.of(request.getPage() - 1, request.getSize());
        StringQuery query = new StringQuery(buildEsQuerySource(request), pageable, sort);
        query.setTrackTotalHits(true);

        SearchHits<PropertySearchDocument> hits = elasticsearchOperations.search(query, PropertySearchDocument.class);
        List<PropertySearchItemResponse> items = hits.getSearchHits().stream()
                .map(hit -> toResponse(hit.getContent(), request))
                .collect(Collectors.toList());

        return new PropertySearchResponse(
                items,
                hits.getTotalHits(),
                request.getPage(),
                request.getSize(),
                true
        );
    }

    private PropertySearchResponse fallbackSearch(PropertySearchRequest request, boolean usedElasticsearch) {
        List<PropertySearchItemResponse> filtered = propertyRepository.findByStatus(Property.PropertyStatus.APPROVED).stream()
                .map(property -> toResponse(property, request))
                .filter(item -> matchesKeyword(item, request.getKeyword()))
                .filter(item -> matchesExact(item.getCity(), request.getCity()))
                .filter(item -> matchesExact(item.getDistrict(), request.getDistrict()))
                .filter(item -> matchesFeatured(item, request.getFeatured()))
                .filter(item -> matchesMinRating(item, request.getMinRating()))
                .filter(item -> matchesPrice(item, request.getMinPrice(), request.getMaxPrice()))
                .filter(item -> matchesFacilities(item, request.getFacilities()))
                .filter(item -> matchesGeo(item, request))
                .sorted(buildFallbackComparator(request))
                .collect(Collectors.toList());

        int fromIndex = Math.min((request.getPage() - 1) * request.getSize(), filtered.size());
        int toIndex = Math.min(fromIndex + request.getSize(), filtered.size());
        List<PropertySearchItemResponse> pageItems = filtered.subList(fromIndex, toIndex);

        return new PropertySearchResponse(
                pageItems,
                filtered.size(),
                request.getPage(),
                request.getSize(),
                usedElasticsearch
        );
    }

    private static final java.util.regex.Pattern CITY_SUFFIX =
            java.util.regex.Pattern.compile("(市|特别行政区|自治州|地区|盟)$");
    private static final java.util.regex.Pattern DISTRICT_SUFFIX =
            java.util.regex.Pattern.compile("(区|新区|县|县级市|自治县|旗)$");

    private PropertySearchRequest normalize(PropertySearchRequest request) {
        PropertySearchRequest normalized = request == null ? new PropertySearchRequest() : request;
        if (normalized.getPage() == null || normalized.getPage() < 1) {
            normalized.setPage(1);
        }
        if (normalized.getSize() == null || normalized.getSize() < 1) {
            normalized.setSize(10);
        }
        normalized.setSize(Math.min(normalized.getSize(), MAX_PAGE_SIZE));
        if (normalized.getDistanceKm() != null && normalized.getDistanceKm() <= 0) {
            normalized.setDistanceKm(null);
        }
        if (normalized.getFacilities() != null) {
            normalized.setFacilities(normalized.getFacilities().stream()
                    .filter(StringUtils::hasText)
                    .map(String::trim)
                    .distinct()
                    .collect(Collectors.toList()));
        }
        if (StringUtils.hasText(normalized.getCity())) {
            String city = CITY_SUFFIX.matcher(normalized.getCity().trim()).replaceAll("");
            if (StringUtils.hasText(city)) {
                normalized.setCity(city);
            }
        }
        if (StringUtils.hasText(normalized.getDistrict())) {
            String district = DISTRICT_SUFFIX.matcher(normalized.getDistrict().trim()).replaceAll("");
            if (StringUtils.hasText(district)) {
                normalized.setDistrict(district);
            }
        }
        return normalized;
    }

    private boolean canUseElasticsearch() {
        return elasticsearchEnabled && elasticsearchOperations != null;
    }

    private void ensureIndex() {
        if (indexReady.get()) {
            return;
        }

        synchronized (indexReady) {
            if (indexReady.get()) {
                return;
            }
            IndexOperations indexOperations = elasticsearchOperations.indexOps(PropertySearchDocument.class);
            if (!indexOperations.exists()) {
                indexOperations.createWithMapping();
            }
            populateIndexIfEmpty(indexOperations);
            indexReady.set(true);
        }
    }

    private void populateIndexIfEmpty(IndexOperations indexOperations) {
        if (!isIndexEmpty()) {
            return;
        }
        List<PropertySearchDocument> documents = propertyRepository.findByStatus(Property.PropertyStatus.APPROVED).stream()
                .map(this::toDocument)
                .collect(Collectors.toList());
        if (documents.isEmpty()) {
            return;
        }
        elasticsearchOperations.save(documents);
        indexOperations.refresh();
        log.info("Seeded Elasticsearch property index with {} approved properties", documents.size());
    }

    private boolean isIndexEmpty() {
        StringQuery countQuery = new StringQuery("{\"match_all\":{}}");
        return elasticsearchOperations.count(countQuery, PropertySearchDocument.class) == 0;
    }

    private Sort buildSort(PropertySearchRequest request) {
        List<Sort.Order> orders = new ArrayList<>();
        if (hasGeoFilter(request)) {
            orders.add(new GeoDistanceOrder("location", new GeoPoint(request.getLatitude(), request.getLongitude()))
                    .with(Sort.Direction.ASC)
                    .withUnit("km"));
        }
        if (StringUtils.hasText(request.getKeyword())) {
            orders.add(Sort.Order.desc("_score"));
        }
        orders.add(Sort.Order.desc("rating"));
        orders.add(Sort.Order.desc("featured"));
        return Sort.by(orders);
    }

    private String buildEsQuerySource(PropertySearchRequest request) {
        ObjectNode root = objectMapper.createObjectNode();
        ObjectNode boolNode = root.putObject("bool");
        ArrayNode mustArray = boolNode.putArray("must");
        ArrayNode filterArray = boolNode.putArray("filter");

        filterArray.add(termNode("status", Property.PropertyStatus.APPROVED.name()));

        if (StringUtils.hasText(request.getKeyword())) {
            mustArray.add(multiMatchNode(request.getKeyword().trim()));
        }
        if (StringUtils.hasText(request.getCity())) {
            filterArray.add(termNode("city", request.getCity().trim()));
        }
        if (StringUtils.hasText(request.getDistrict())) {
            filterArray.add(termNode("district", request.getDistrict().trim()));
        }
        if (request.getFeatured() != null) {
            filterArray.add(termNode("featured", request.getFeatured()));
        }
        if (request.getMinRating() != null) {
            filterArray.add(rangeNode("rating", "gte", request.getMinRating()));
        }
        if (request.getMinPrice() != null) {
            filterArray.add(rangeNode("priceRangeMax", "gte", request.getMinPrice()));
        }
        if (request.getMaxPrice() != null) {
            filterArray.add(rangeNode("priceRangeMin", "lte", request.getMaxPrice()));
        }
        if (request.getFacilities() != null) {
            for (String facility : request.getFacilities()) {
                filterArray.add(termNode("facilities", facility));
            }
        }
        if (hasGeoFilter(request)) {
            filterArray.add(geoDistanceNode(request.getLatitude(), request.getLongitude(), request.getDistanceKm()));
        }

        return root.toString();
    }

    private ObjectNode multiMatchNode(String keyword) {
        ObjectNode node = objectMapper.createObjectNode();
        ObjectNode multiMatch = node.putObject("multi_match");
        multiMatch.put("query", keyword);
        ArrayNode fields = multiMatch.putArray("fields");
        fields.add("propertyName^4");
        fields.add("province^2");
        fields.add("city^2");
        fields.add("district^2");
        fields.add("address^2");
        fields.add("description");
        fields.add("facilitiesText");
        multiMatch.put("type", "cross_fields");
        multiMatch.put("operator", "and");
        multiMatch.put("fuzziness", "AUTO");
        return node;
    }

    private ObjectNode termNode(String field, String value) {
        ObjectNode node = objectMapper.createObjectNode();
        ObjectNode term = node.putObject("term");
        term.put(field, value);
        return node;
    }

    private ObjectNode termNode(String field, Boolean value) {
        ObjectNode node = objectMapper.createObjectNode();
        ObjectNode term = node.putObject("term");
        term.put(field, value);
        return node;
    }

    private ObjectNode rangeNode(String field, String operator, BigDecimal value) {
        ObjectNode node = objectMapper.createObjectNode();
        ObjectNode range = node.putObject("range");
        ObjectNode targetField = range.putObject(field);
        targetField.put(operator, value);
        return node;
    }

    private ObjectNode geoDistanceNode(Double latitude, Double longitude, Double distanceKm) {
        ObjectNode node = objectMapper.createObjectNode();
        ObjectNode geoDistance = node.putObject("geo_distance");
        geoDistance.put("distance", BigDecimal.valueOf(distanceKm).setScale(2, RoundingMode.HALF_UP).stripTrailingZeros().toPlainString() + "km");
        ObjectNode location = geoDistance.putObject("location");
        location.put("lat", latitude);
        location.put("lon", longitude);
        return node;
    }

    private PropertySearchDocument toDocument(Property property) {
        List<String> facilities = parseFacilities(property.getFacilities());
        PropertySearchDocument document = new PropertySearchDocument();
        document.setId(String.valueOf(property.getId()));
        document.setPropertyId(property.getId());
        document.setPropertyName(property.getPropertyName());
        document.setPropertyType(property.getPropertyType() != null ? property.getPropertyType().name() : null);
        document.setDescription(property.getDescription());
        document.setImages(property.getImages());
        document.setProvince(property.getProvince());
        document.setCity(property.getCity());
        document.setDistrict(property.getDistrict());
        document.setAddress(property.getAddress());
        document.setPriceRangeMin(property.getPriceRangeMin());
        document.setPriceRangeMax(property.getPriceRangeMax());
        document.setRating(property.getRating());
        document.setFeatured(Boolean.TRUE.equals(property.getIsFeatured()));
        document.setFacilities(facilities);
        document.setFacilitiesText(String.join(" ", facilities));
        document.setStatus(property.getStatus() != null ? property.getStatus().name() : null);
        document.setLatitude(property.getLatitude() != null ? property.getLatitude().doubleValue() : null);
        document.setLongitude(property.getLongitude() != null ? property.getLongitude().doubleValue() : null);
        if (isValidCoordinate(document.getLatitude(), document.getLongitude())) {
            document.setLocation(new GeoPoint(document.getLatitude(), document.getLongitude()));
        }
        return document;
    }

    private boolean isValidCoordinate(Double latitude, Double longitude) {
        return latitude != null && longitude != null
                && latitude >= -90d && latitude <= 90d
                && longitude >= -180d && longitude <= 180d;
    }

    private PropertySearchItemResponse toResponse(PropertySearchDocument document, PropertySearchRequest request) {
        return new PropertySearchItemResponse(
                document.getPropertyId(),
                document.getPropertyName(),
                document.getPropertyType(),
                document.getDescription(),
                document.getImages(),
                document.getProvince(),
                document.getCity(),
                document.getDistrict(),
                document.getAddress(),
                document.getPriceRangeMin(),
                document.getPriceRangeMax(),
                document.getRating(),
                document.getFeatured(),
                document.getLatitude(),
                document.getLongitude(),
                document.getFacilities(),
                calculateDistance(document.getLatitude(), document.getLongitude(), request)
        );
    }

    private PropertySearchItemResponse toResponse(Property property, PropertySearchRequest request) {
        List<String> facilities = parseFacilities(property.getFacilities());
        Double latitude = property.getLatitude() != null ? property.getLatitude().doubleValue() : null;
        Double longitude = property.getLongitude() != null ? property.getLongitude().doubleValue() : null;
        return new PropertySearchItemResponse(
                property.getId(),
                property.getPropertyName(),
                property.getPropertyType() != null ? property.getPropertyType().name() : null,
                property.getDescription(),
                property.getImages(),
                property.getProvince(),
                property.getCity(),
                property.getDistrict(),
                property.getAddress(),
                property.getPriceRangeMin(),
                property.getPriceRangeMax(),
                property.getRating(),
                property.getIsFeatured(),
                latitude,
                longitude,
                facilities,
                calculateDistance(latitude, longitude, request)
        );
    }

    private List<String> parseFacilities(String facilitiesRaw) {
        if (!StringUtils.hasText(facilitiesRaw)) {
            return List.of();
        }

        try {
            JsonNode root = objectMapper.readTree(facilitiesRaw);
            if (root.isArray()) {
                Set<String> values = new LinkedHashSet<>();
                for (JsonNode node : root) {
                    if (node.isTextual()) {
                        values.add(node.asText());
                    } else if (node.isObject()) {
                        node.fields().forEachRemaining(entry -> {
                            JsonNode value = entry.getValue();
                            if (value.isTextual()) {
                                values.add(value.asText());
                            } else if (value.isBoolean() && value.asBoolean()) {
                                values.add(entry.getKey());
                            }
                        });
                    } else if (!node.isNull()) {
                        values.add(node.asText());
                    }
                }
                return values.stream()
                        .filter(StringUtils::hasText)
                        .map(String::trim)
                        .collect(Collectors.toList());
            }
        } catch (Exception ignored) {
        }

        return List.of(facilitiesRaw.split("[,，、\\s]+")).stream()
                .filter(StringUtils::hasText)
                .map(String::trim)
                .distinct()
                .collect(Collectors.toList());
    }

    private boolean matchesKeyword(PropertySearchItemResponse item, String keyword) {
        if (!StringUtils.hasText(keyword)) {
            return true;
        }

        String normalizedKeyword = keyword.trim().toLowerCase(Locale.ROOT);
        String searchableText = String.join(" ",
                        safe(item.getPropertyName()),
                        safe(item.getDescription()),
                        safe(item.getProvince()),
                        safe(item.getCity()),
                        safe(item.getDistrict()),
                        safe(item.getAddress()),
                        String.join(" ", item.getFacilities() == null ? List.of() : item.getFacilities()))
                .toLowerCase(Locale.ROOT);

        // Exact substring match first (fast path)
        if (searchableText.contains(normalizedKeyword)) {
            return true;
        }

        // Split into words and require each word to appear somewhere (cross-field logic)
        String[] words = normalizedKeyword.split("[\\s,，、]+");
        for (String word : words) {
            if (word.isEmpty()) {
                continue;
            }
            if (!searchableText.contains(word)) {
                return false;
            }
        }
        return true;
    }

    private boolean matchesExact(String actual, String expected) {
        if (!StringUtils.hasText(expected)) {
            return true;
        }
        String trimmed = expected.trim();
        String safeActual = safe(actual);
        if (safeActual.equalsIgnoreCase(trimmed)) {
            return true;
        }
        // Fallback: contains match (e.g. "上海市" contains "上海")
        if (safeActual.toLowerCase(Locale.ROOT).contains(trimmed.toLowerCase(Locale.ROOT))) {
            return true;
        }
        return false;
    }

    private boolean matchesFeatured(PropertySearchItemResponse item, Boolean featured) {
        if (featured == null) {
            return true;
        }
        return featured.equals(Boolean.TRUE.equals(item.getFeatured()));
    }

    private boolean matchesMinRating(PropertySearchItemResponse item, BigDecimal minRating) {
        if (minRating == null) {
            return true;
        }
        return item.getRating() != null && item.getRating().compareTo(minRating) >= 0;
    }

    private boolean matchesPrice(PropertySearchItemResponse item, BigDecimal minPrice, BigDecimal maxPrice) {
        if (minPrice != null) {
            if (item.getPriceRangeMax() == null || item.getPriceRangeMax().compareTo(minPrice) < 0) {
                return false;
            }
        }
        if (maxPrice != null) {
            if (item.getPriceRangeMin() == null || item.getPriceRangeMin().compareTo(maxPrice) > 0) {
                return false;
            }
        }
        return true;
    }

    private boolean matchesFacilities(PropertySearchItemResponse item, List<String> facilities) {
        if (facilities == null || facilities.isEmpty()) {
            return true;
        }
        List<String> actualFacilities = item.getFacilities() == null ? List.of() : item.getFacilities();
        return facilities.stream().allMatch(required ->
                actualFacilities.stream().anyMatch(actual -> actual.equalsIgnoreCase(required)));
    }

    private boolean matchesGeo(PropertySearchItemResponse item, PropertySearchRequest request) {
        if (!hasGeoFilter(request)) {
            return true;
        }
        return item.getDistanceKm() != null && item.getDistanceKm() <= request.getDistanceKm();
    }

    private Comparator<PropertySearchItemResponse> buildFallbackComparator(PropertySearchRequest request) {
        Comparator<PropertySearchItemResponse> comparator;
        if (hasGeoFilter(request)) {
            comparator = Comparator.comparing(PropertySearchItemResponse::getDistanceKm,
                    Comparator.nullsLast(Comparator.naturalOrder()));
        } else {
            comparator = Comparator.comparing(PropertySearchItemResponse::getRating,
                    Comparator.nullsLast(Comparator.reverseOrder()));
        }
        return comparator.thenComparing(PropertySearchItemResponse::getRating,
                Comparator.nullsLast(Comparator.reverseOrder()));
    }

    private Double calculateDistance(Double latitude, Double longitude, PropertySearchRequest request) {
        if (!hasGeoFilter(request) || latitude == null || longitude == null) {
            return null;
        }

        double latDistance = Math.toRadians(request.getLatitude() - latitude);
        double lonDistance = Math.toRadians(request.getLongitude() - longitude);
        double startLat = Math.toRadians(latitude);
        double endLat = Math.toRadians(request.getLatitude());

        double a = Math.pow(Math.sin(latDistance / 2), 2)
                + Math.cos(startLat) * Math.cos(endLat) * Math.pow(Math.sin(lonDistance / 2), 2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return BigDecimal.valueOf(EARTH_RADIUS_KM * c).setScale(2, RoundingMode.HALF_UP).doubleValue();
    }

    private boolean hasGeoFilter(PropertySearchRequest request) {
        return request.getLatitude() != null
                && request.getLongitude() != null
                && request.getDistanceKm() != null;
    }

    private String safe(String value) {
        return value == null ? "" : value;
    }
}
