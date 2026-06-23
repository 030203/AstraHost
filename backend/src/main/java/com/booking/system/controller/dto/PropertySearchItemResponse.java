package com.booking.system.controller.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class PropertySearchItemResponse {
    private Long id;
    private String propertyName;
    private String propertyType;
    private String description;
    private String images;
    private String province;
    private String city;
    private String district;
    private String address;
    private BigDecimal priceRangeMin;
    private BigDecimal priceRangeMax;
    private BigDecimal rating;
    private Boolean featured;
    private Double latitude;
    private Double longitude;
    private List<String> facilities;
    private Double distanceKm;
}
