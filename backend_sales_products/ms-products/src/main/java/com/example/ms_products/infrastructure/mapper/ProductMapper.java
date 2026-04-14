package com.example.ms_products.infrastructure.mapper;

import com.example.ms_products.domain.model.ProductInfo;
import com.example.ms_products.infrastructure.entrypoints.dto.ProductResponseDto;
import org.springframework.stereotype.Component;

@Component
public class ProductMapper {

    public ProductResponseDto toDto(ProductInfo productInfo) {
        if (productInfo == null) {
            return null;
        }

        return ProductResponseDto.builder()
                .productId(productInfo.getProductId())
                .name(productInfo.getName())
                .description(productInfo.getDescription())
                .price(productInfo.getPrice())
                .stockQuantity(productInfo.getStockQuantity())
                .category(productInfo.getCategory())
                .supplier(productInfo.getSupplier())
                .source("SOAP_EXTERNAL_API")
                .build();
    }
}
