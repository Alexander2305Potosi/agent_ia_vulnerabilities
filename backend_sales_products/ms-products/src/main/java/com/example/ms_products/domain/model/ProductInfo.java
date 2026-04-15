package com.example.ms_products.domain.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.List;
import java.util.Map;

/**
 * Modelo de dominio para información completa de producto.
 * Incluye datos enriquecidos provenientes del servicio SOAP externo.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductInfo {

    // Identificación básica
    private String productId;
    private String name;
    private String description;
    private String shortDescription;

    // Identificadores comerciales
    private String sku;
    private String ean;
    private String upc;
    private String brand;
    private String model;

    // Categorización
    private String category;
    private String subcategory;
    private String categoryCode;

    // Precios y moneda
    private Double price;
    private String currency;
    private Double salePrice;
    private Double discountPercent;
    private Double taxRate;
    private Double taxAmount;
    private Double finalPrice;

    // Inventario
    private Integer stockQuantity;
    private Integer availableStock;
    private Integer reservedStock;
    private String warehouseId;
    private String warehouseLocation;
    private Integer reorderPoint;
    private Integer reorderQuantity;
    private Instant lastRestockDate;

    // Proveedor
    private String supplierId;
    private String supplierCode;
    private String supplierName;

    // Estado
    private String status;
    private Boolean isActive;
    private Boolean isAvailable;

    // Dimensiones y peso
    private Double weight;
    private String weightUnit;
    private ProductDimensions dimensions;

    // Garantía
    private Integer warrantyPeriodMonths;
    private String warrantyType;
    private String warrantyDescription;

    // Calificaciones
    private Double averageRating;
    private Integer totalReviews;
    private Integer fiveStarCount;
    private Integer fourStarCount;
    private Integer threeStarCount;
    private Integer twoStarCount;
    private Integer oneStarCount;

    // Multimedia
    private List<String> images;

    // Etiquetas y atributos
    private List<String> tags;
    private Map<String, String> attributes;

    // Metadatos
    private Instant createdAt;
    private Instant updatedAt;
    private Instant lastSyncAt;
    private String sourceSystem;

    /**
     * Clase interna para dimensiones del producto.
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ProductDimensions {
        private Double length;
        private Double width;
        private Double height;
        private String unit;
    }
}
