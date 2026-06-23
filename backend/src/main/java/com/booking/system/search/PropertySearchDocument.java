package com.booking.system.search;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.elasticsearch.annotations.Document;
import org.springframework.data.elasticsearch.annotations.Field;
import org.springframework.data.elasticsearch.annotations.FieldType;
import org.springframework.data.elasticsearch.annotations.GeoPointField;
import org.springframework.data.elasticsearch.core.geo.GeoPoint;

import java.math.BigDecimal;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Document(indexName = "roomos-property")
public class PropertySearchDocument {
    @Id
    private String id;

    @Field(type = FieldType.Long)
    private Long propertyId;

    @Field(type = FieldType.Text)
    private String propertyName;

    @Field(type = FieldType.Keyword)
    private String propertyType;

    @Field(type = FieldType.Text)
    private String description;

    @Field(type = FieldType.Keyword)
    private String province;

    @Field(type = FieldType.Keyword)
    private String city;

    @Field(type = FieldType.Keyword)
    private String district;

    @Field(type = FieldType.Text)
    private String address;

    @Field(type = FieldType.Keyword, index = false)
    private String images;

    @Field(type = FieldType.Double)
    private BigDecimal priceRangeMin;

    @Field(type = FieldType.Double)
    private BigDecimal priceRangeMax;

    @Field(type = FieldType.Double)
    private BigDecimal rating;

    @Field(type = FieldType.Boolean)
    private Boolean featured;

    @Field(type = FieldType.Keyword)
    private List<String> facilities;

    @Field(type = FieldType.Text)
    private String facilitiesText;

    @Field(type = FieldType.Keyword)
    private String status;

    @Field(type = FieldType.Double)
    private Double latitude;

    @Field(type = FieldType.Double)
    private Double longitude;

    @GeoPointField
    private GeoPoint location;
}
