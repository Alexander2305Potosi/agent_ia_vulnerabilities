package com.example.ms_products.infrastructure.entrypoints.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductResponseDto {
    private String productId;
    private String name;
    private String description;
    private Double price;
    private Integer stockQuantity;
    private String category;
    private String supplier;
    private String source;
}
