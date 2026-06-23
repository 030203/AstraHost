package com.booking.system.controller.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class PropertySearchReindexResponse {
    private int indexedCount;
    private int removedCount;
    private boolean usedElasticsearch;
}
