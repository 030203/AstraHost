package com.booking.system.controller;

import com.booking.system.controller.dto.PropertyDetailResponse;
import com.booking.system.controller.dto.PropertySearchReindexResponse;
import com.booking.system.controller.dto.PropertySearchRequest;
import com.booking.system.controller.dto.PropertySearchResponse;
import com.booking.system.controller.dto.TopPropertyResponse;
import com.booking.system.entity.Property;
import com.booking.system.service.PropertySearchService;
import com.booking.system.service.PropertyService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/properties")
public class PropertyController {
    
    @Autowired
    private PropertyService propertyService;

    @Autowired
    private PropertySearchService propertySearchService;
    
    @GetMapping
    public ResponseEntity<List<Property>> getAllProperties(
            @RequestParam(required = false) Long merchantId,
            @RequestParam(required = false) String city,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) Boolean featured) {
        if (merchantId != null) {
            return ResponseEntity.ok(propertyService.getPropertiesByMerchantId(merchantId));
        }
        if (city != null) {
            return ResponseEntity.ok(propertyService.getPropertiesByCity(city));
        }
        if (status != null) {
            return ResponseEntity.ok(propertyService.getPropertiesByStatus(status));
        }
        if (featured != null && featured) {
            return ResponseEntity.ok(propertyService.getFeaturedProperties());
        }
        return ResponseEntity.ok(propertyService.getAllProperties());
    }

    @GetMapping("/search")
    public ResponseEntity<PropertySearchResponse> searchProperties(@ModelAttribute PropertySearchRequest request) {
        return ResponseEntity.ok(propertySearchService.search(request));
    }

    @PostMapping("/search/reindex")
    public ResponseEntity<PropertySearchReindexResponse> reindexSearchIndex() {
        return ResponseEntity.ok(propertySearchService.reindexAll());
    }
    
    @GetMapping("/{id}")
    public ResponseEntity<Property> getPropertyById(@PathVariable Long id) {
        Optional<Property> property = propertyService.getPropertyById(id);
        return property.map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @GetMapping("/{id}/detail")
    public ResponseEntity<PropertyDetailResponse> getPropertyDetail(@PathVariable Long id) {
        try {
            return ResponseEntity.ok(propertyService.getPropertyDetail(id));
        } catch (RuntimeException ex) {
            return ResponseEntity.notFound().build();
        }
    }

    @GetMapping("/top")
    public ResponseEntity<List<TopPropertyResponse>> getTop(@RequestParam(defaultValue = "5") int limit) {
        return ResponseEntity.ok(propertyService.getTopProperties(limit));
    }
    
    @PostMapping
    public ResponseEntity<Property> createProperty(@RequestBody Property property) {
        return ResponseEntity.ok(propertyService.createProperty(property));
    }
    
    @PutMapping("/{id}")
    public ResponseEntity<Property> updateProperty(@PathVariable Long id, @RequestBody Property property) {
        return ResponseEntity.ok(propertyService.updateProperty(id, property));
    }

    @PostMapping("/{id}/approve")
    public ResponseEntity<Property> approve(@PathVariable Long id) {
        return ResponseEntity.ok(propertyService.updateStatus(id, Property.PropertyStatus.APPROVED));
    }

    @PostMapping("/{id}/reject")
    public ResponseEntity<Property> reject(@PathVariable Long id) {
        return ResponseEntity.ok(propertyService.updateStatus(id, Property.PropertyStatus.REJECTED));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteProperty(@PathVariable Long id) {
        propertyService.deleteProperty(id);
        return ResponseEntity.ok().build();
    }
}
