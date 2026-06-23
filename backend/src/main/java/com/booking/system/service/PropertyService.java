package com.booking.system.service;

import com.booking.system.controller.dto.PropertyDetailResponse;
import com.booking.system.controller.dto.TopPropertyResponse;
import com.booking.system.entity.Property;
import com.booking.system.entity.RoomType;
import com.booking.system.mapper.BookingRepository;
import com.booking.system.mapper.MerchantRepository;
import com.booking.system.mapper.PropertyRepository;
import com.booking.system.mapper.RoomTypeRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.cache.annotation.Caching;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
public class PropertyService {

    @Autowired
    private PropertyRepository propertyRepository;

    @Autowired
    private RoomTypeRepository roomTypeRepository;

    @Autowired
    private MerchantRepository merchantRepository;

    @Autowired
    private BookingRepository bookingRepository;

    @Autowired
    private PropertySearchService propertySearchService;

    public List<Property> getAllProperties() {
        return propertyRepository.findAll();
    }

    public Optional<Property> getPropertyById(Long id) {
        return propertyRepository.findById(id);
    }

    public List<Property> getPropertiesByMerchantId(Long merchantId) {
        return propertyRepository.findByMerchantId(merchantId);
    }

    public List<Property> getPropertiesByCity(String city) {
        return propertyRepository.findByCity(city);
    }

    public List<Property> getPropertiesByStatus(String status) {
        try {
            Property.PropertyStatus s = Property.PropertyStatus.valueOf(status.toUpperCase());
            return propertyRepository.findByStatus(s);
        } catch (IllegalArgumentException ex) {
            throw new RuntimeException("非法状态: " + status);
        }
    }

    @Cacheable(cacheNames = PropertyCacheService.FEATURED_CACHE, key = "'all'")
    public List<Property> getFeaturedProperties() {
        return propertyRepository.findByIsFeatured(true);
    }

    @Cacheable(cacheNames = PropertyCacheService.TOP_CACHE, key = "'limit:' + #limit")
    public List<TopPropertyResponse> getTopProperties(int limit) {
        int top = Math.max(1, Math.min(limit, 20));
        List<Object[]> pairs = bookingRepository.findTopPropertyBookingCounts(
                Property.PropertyStatus.APPROVED,
                PageRequest.of(0, top)
        );
        if (pairs == null || pairs.isEmpty()) {
            return propertyRepository.findByStatus(Property.PropertyStatus.APPROVED).stream()
                    .sorted(Comparator.comparing(Property::getRating, Comparator.nullsLast(Comparator.naturalOrder())).reversed())
                    .limit(top)
                    .map(p -> new TopPropertyResponse(p, 0L))
                    .collect(Collectors.toList());
        }
        return pairs.stream()
                .map(pair -> {
                    Long pid = ((Number) pair[0]).longValue();
                    Long cnt = ((Number) pair[1]).longValue();
                    return propertyRepository.findById(pid)
                            .map(p -> new TopPropertyResponse(p, cnt))
                            .orElse(null);
                })
                .filter(r -> r != null)
                .collect(Collectors.toList());
    }

    @Cacheable(cacheNames = PropertyCacheService.DETAIL_CACHE, key = "#propertyId")
    public PropertyDetailResponse getPropertyDetail(Long propertyId) {
        Property property = propertyRepository.findById(propertyId)
                .orElseThrow(() -> new RuntimeException("Property not found"));
        List<RoomType> roomTypes = roomTypeRepository.findByProperty_Id(propertyId);
        return new PropertyDetailResponse(
                property,
                roomTypes.stream()
                        .map(rt -> new PropertyDetailResponse.SimpleRoomType(
                                rt.getId(),
                                rt.getTypeName(),
                                rt.getDescription(),
                                rt.getMaxOccupancy(),
                                rt.getBedType(),
                                rt.getRoomSize(),
                                rt.getAmenities(),
                                rt.getImages(),
                                rt.getBasePrice(),
                                rt.getStatus() != null ? rt.getStatus().name() : null,
                                rt.getSortOrder(),
                                rt.getCreatedAt()
                        ))
                        .collect(Collectors.toList())
        );
    }

    @Caching(evict = {
            @CacheEvict(cacheNames = PropertyCacheService.FEATURED_CACHE, allEntries = true),
            @CacheEvict(cacheNames = PropertyCacheService.TOP_CACHE, allEntries = true)
    })
    @Transactional
    public Property createProperty(Property property) {
        if (property.getMerchantId() == null) {
            throw new RuntimeException("商户ID不能为空");
        }
        merchantRepository.findById(property.getMerchantId())
                .orElseThrow(() -> new RuntimeException("商户不存在，请检查商户ID"));
        property.setStatus(Property.PropertyStatus.PENDING);
        if (property.getIsFeatured() == null) {
            property.setIsFeatured(false);
        }
        property.setCreatedAt(LocalDateTime.now());
        property.setUpdatedAt(LocalDateTime.now());
        Property saved = propertyRepository.save(property);
        propertySearchService.syncProperty(saved);
        return saved;
    }

    @Caching(evict = {
            @CacheEvict(cacheNames = PropertyCacheService.DETAIL_CACHE, key = "#id"),
            @CacheEvict(cacheNames = PropertyCacheService.FEATURED_CACHE, allEntries = true),
            @CacheEvict(cacheNames = PropertyCacheService.TOP_CACHE, allEntries = true)
    })
    @Transactional
    public Property updateProperty(Long id, Property property) {
        property.setId(id);
        property.setUpdatedAt(LocalDateTime.now());
        Property saved = propertyRepository.save(property);
        propertySearchService.syncProperty(saved);
        return saved;
    }

    @Caching(evict = {
            @CacheEvict(cacheNames = PropertyCacheService.DETAIL_CACHE, key = "#id"),
            @CacheEvict(cacheNames = PropertyCacheService.FEATURED_CACHE, allEntries = true),
            @CacheEvict(cacheNames = PropertyCacheService.TOP_CACHE, allEntries = true)
    })
    @Transactional
    public Property updateStatus(Long id, Property.PropertyStatus status) {
        Property property = propertyRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("民宿不存在"));
        property.setStatus(status);
        property.setUpdatedAt(LocalDateTime.now());
        Property saved = propertyRepository.save(property);
        propertySearchService.syncProperty(saved);
        return saved;
    }

    @Caching(evict = {
            @CacheEvict(cacheNames = PropertyCacheService.DETAIL_CACHE, key = "#id"),
            @CacheEvict(cacheNames = PropertyCacheService.FEATURED_CACHE, allEntries = true),
            @CacheEvict(cacheNames = PropertyCacheService.TOP_CACHE, allEntries = true)
    })
    @Transactional
    public void deleteProperty(Long id) {
        propertyRepository.deleteById(id);
        propertySearchService.removeProperty(id);
    }
}
