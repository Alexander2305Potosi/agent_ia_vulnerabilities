package com.example.ms_products.infrastructure.mapper;

import com.example.ms_products.domain.model.ProductInfo;
import com.example.ms_products.infrastructure.entrypoints.dto.ProductResponseDto;
import org.springframework.stereotype.Component;

import java.util.Collections;

/**
 * Mapper para convertir entre modelos de dominio y DTOs.
 * Mapea información completa del producto desde ProductInfo hacia ProductResponseDto.
 */
@Component
public class ProductMapper {

    /**
     * Convierte ProductInfo (dominio) a ProductResponseDto (REST API).
     *
     * @param productInfo Información del producto desde el servicio SOAP
     * @return DTO para respuesta REST
     */
    public ProductResponseDto toDto(ProductInfo productInfo) {
        if (productInfo == null) {
            return null;
        }

        // Mapear dimensiones
        ProductResponseDto.ProductDimensionsDto dimensionsDto = null;
        if (productInfo.getDimensions() != null) {
            dimensionsDto = ProductResponseDto.ProductDimensionsDto.builder()
                    .length(productInfo.getDimensions().getLength())
                    .width(productInfo.getDimensions().getWidth())
                    .height(productInfo.getDimensions().getHeight())
                    .unit(productInfo.getDimensions().getUnit())
                    .build();
        }

        return ProductResponseDto.builder()
                // Identificación básica
                .productId(productInfo.getProductId())
                .name(productInfo.getName())
                .description(productInfo.getDescription())
                .shortDescription(productInfo.getShortDescription())

                // Identificadores comerciales
                .sku(productInfo.getSku())
                .ean(productInfo.getEan())
                .upc(productInfo.getUpc())
                .brand(productInfo.getBrand())
                .model(productInfo.getModel())

                // Categorización
                .category(productInfo.getCategory())
                .subcategory(productInfo.getSubcategory())
                .categoryCode(productInfo.getCategoryCode())

                // Precios
                .price(productInfo.getPrice())
                .currency(productInfo.getCurrency())
                .salePrice(productInfo.getSalePrice())
                .discountPercent(productInfo.getDiscountPercent())
                .taxRate(productInfo.getTaxRate())
                .taxAmount(productInfo.getTaxAmount())
                .finalPrice(productInfo.getFinalPrice())

                // Inventario
                .stockQuantity(productInfo.getStockQuantity())
                .availableStock(productInfo.getAvailableStock())
                .reservedStock(productInfo.getReservedStock())
                .warehouseId(productInfo.getWarehouseId())
                .warehouseLocation(productInfo.getWarehouseLocation())
                .reorderPoint(productInfo.getReorderPoint())
                .reorderQuantity(productInfo.getReorderQuantity())
                .lastRestockDate(productInfo.getLastRestockDate())

                // Proveedor
                .supplierId(productInfo.getSupplierId())
                .supplierCode(productInfo.getSupplierCode())
                .supplierName(productInfo.getSupplierName())

                // Estado
                .status(productInfo.getStatus())
                .isActive(productInfo.getIsActive())
                .isAvailable(productInfo.getIsAvailable())

                // Dimensiones
                .weight(productInfo.getWeight())
                .weightUnit(productInfo.getWeightUnit())
                .dimensions(dimensionsDto)

                // Garantía
                .warrantyPeriodMonths(productInfo.getWarrantyPeriodMonths())
                .warrantyType(productInfo.getWarrantyType())
                .warrantyDescription(productInfo.getWarrantyDescription())

                // Calificaciones
                .averageRating(productInfo.getAverageRating())
                .totalReviews(productInfo.getTotalReviews())
                .fiveStarCount(productInfo.getFiveStarCount())
                .fourStarCount(productInfo.getFourStarCount())
                .threeStarCount(productInfo.getThreeStarCount())
                .twoStarCount(productInfo.getTwoStarCount())
                .oneStarCount(productInfo.getOneStarCount())

                // Multimedia y atributos
                .images(productInfo.getImages() != null ? productInfo.getImages() : Collections.emptyList())
                .tags(productInfo.getTags() != null ? productInfo.getTags() : Collections.emptyList())
                .attributes(productInfo.getAttributes() != null ? productInfo.getAttributes() : Collections.emptyMap())

                // Metadatos
                .createdAt(productInfo.getCreatedAt())
                .updatedAt(productInfo.getUpdatedAt())
                .lastSyncAt(productInfo.getLastSyncAt())
                .source("SOAP_EXTERNAL_API")
                .sourceSystem(productInfo.getSourceSystem())
                .build();
    }
}
