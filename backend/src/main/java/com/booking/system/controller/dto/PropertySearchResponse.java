package com.booking.system.controller.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class PropertySearchResponse {
    private List<PropertySearchItemResponse> items;
    private long total;
    private int page;
    private int size;
    private boolean usedElasticsearch;
}
