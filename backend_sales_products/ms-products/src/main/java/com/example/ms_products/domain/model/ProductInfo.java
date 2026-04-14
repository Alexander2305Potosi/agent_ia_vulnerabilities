package com.example.ms_products.domain.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductInfo {
    private String productId;
    private String name;
    private String description;
    private Double price;
    private Integer stockQuantity;
    private String category;
    private String supplier;
}
