package com.booking.system.controller.dto;

import lombok.Data;

import java.math.BigDecimal;
import java.util.List;

@Data
public class PropertySearchRequest {
    private String keyword;
    private String city;
    private String district;
    private BigDecimal minPrice;
    private BigDecimal maxPrice;
    private BigDecimal minRating;
    private Boolean featured;
    private List<String> facilities;
    private Double latitude;
    private Double longitude;
    private Double distanceKm;
    private Integer page = 1;
    private Integer size = 10;
}
