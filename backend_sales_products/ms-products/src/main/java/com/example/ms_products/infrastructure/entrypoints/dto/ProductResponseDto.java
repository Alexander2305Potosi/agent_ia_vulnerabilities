package com.example.ms_products.infrastructure.entrypoints.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.List;
import java.util.Map;

/**
 * DTO para respuesta de información completa de producto.
 * Incluye datos enriquecidos para la API REST.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
@Schema(description = "Respuesta con información completa del producto")
public class ProductResponseDto {

    // Identificación básica
    @Schema(description = "ID único del producto", example = "PROD-001")
    private String productId;

    @Schema(description = "Nombre del producto", example = "Laptop Dell XPS 15")
    private String name;

    @Schema(description = "Descripción completa del producto")
    private String description;

    @Schema(description = "Descripción corta del producto", example = "Laptop Dell XPS 15 9530")
    private String shortDescription;

    // Identificadores comerciales
    @Schema(description = "SKU del producto", example = "XPS15-9530-I9-32")
    private String sku;

    @Schema(description = "Código EAN", example = "1234567890123")
    private String ean;

    @Schema(description = "Código UPC", example = "884116340123")
    private String upc;

    @Schema(description = "Marca del producto", example = "Dell")
    private String brand;

    @Schema(description = "Modelo del producto", example = "XPS 15 9530")
    private String model;

    // Categorización
    @Schema(description = "Categoría principal", example = "Electronics")
    private String category;

    @Schema(description = "Subcategoría", example = "Laptops")
    private String subcategory;

    @Schema(description = "Código de categoría", example = "ELEC-LAP-001")
    private String categoryCode;

    // Precios
    @Schema(description = "Precio base", example = "2499.99")
    private Double price;

    @Schema(description = "Moneda", example = "USD")
    private String currency;

    @Schema(description = "Precio de venta (con descuento)", example = "2299.99")
    private Double salePrice;

    @Schema(description = "Porcentaje de descuento", example = "8.0")
    private Double discountPercent;

    @Schema(description = "Tasa de impuesto", example = "19.0")
    private Double taxRate;

    @Schema(description = "Monto de impuesto", example = "474.99")
    private Double taxAmount;

    @Schema(description = "Precio final con impuestos", example = "2774.98")
    private Double finalPrice;

    // Inventario
    @Schema(description = "Cantidad total en stock", example = "45")
    private Integer stockQuantity;

    @Schema(description = "Cantidad disponible para venta", example = "42")
    private Integer availableStock;

    @Schema(description = "Cantidad reservada", example = "3")
    private Integer reservedStock;

    @Schema(description = "ID del almacén", example = "WH-MAIN-001")
    private String warehouseId;

    @Schema(description = "Ubicación en almacén", example = "A-12-34")
    private String warehouseLocation;

    @Schema(description = "Punto de reorden", example = "10")
    private Integer reorderPoint;

    @Schema(description = "Cantidad de reorden", example = "50")
    private Integer reorderQuantity;

    @Schema(description = "Fecha última reposición", example = "2026-03-15T10:30:00Z")
    private Instant lastRestockDate;

    // Proveedor
    @Schema(description = "ID del proveedor", example = "SUPP-DELL-001")
    private String supplierId;

    @Schema(description = "Código del proveedor", example = "DTX001")
    private String supplierCode;

    @Schema(description = "Nombre del proveedor", example = "Dell Technologies")
    private String supplierName;

    // Estado
    @Schema(description = "Estado del producto", example = "ACTIVE")
    private String status;

    @Schema(description = "Indica si está activo", example = "true")
    private Boolean isActive;

    @Schema(description = "Indica si está disponible", example = "true")
    private Boolean isAvailable;

    // Dimensiones y peso
    @Schema(description = "Peso del producto", example = "1.86")
    private Double weight;

    @Schema(description = "Unidad de peso", example = "kg")
    private String weightUnit;

    @Schema(description = "Dimensiones del producto")
    private ProductDimensionsDto dimensions;

    // Garantía
    @Schema(description = "Período de garantía en meses", example = "24")
    private Integer warrantyPeriodMonths;

    @Schema(description = "Tipo de garantía", example = "Manufacturer")
    private String warrantyType;

    @Schema(description = "Descripción de la garantía")
    private String warrantyDescription;

    // Calificaciones
    @Schema(description = "Calificación promedio", example = "4.7")
    private Double averageRating;

    @Schema(description = "Total de reseñas", example = "128")
    private Integer totalReviews;

    @Schema(description = "Cantidad de 5 estrellas", example = "98")
    private Integer fiveStarCount;

    @Schema(description = "Cantidad de 4 estrellas", example = "22")
    private Integer fourStarCount;

    @Schema(description = "Cantidad de 3 estrellas", example = "6")
    private Integer threeStarCount;

    @Schema(description = "Cantidad de 2 estrellas", example = "1")
    private Integer twoStarCount;

    @Schema(description = "Cantidad de 1 estrella", example = "1")
    private Integer oneStarCount;

    // Multimedia
    @Schema(description = "URLs de imágenes del producto")
    private List<String> images;

    // Etiquetas y atributos
    @Schema(description = "Etiquetas del producto")
    private List<String> tags;

    @Schema(description = "Atributos adicionales del producto (especificaciones)")
    private Map<String, String> attributes;

    // Metadatos
    @Schema(description = "Fecha de creación", example = "2025-01-15T08:00:00Z")
    private Instant createdAt;

    @Schema(description = "Fecha de última actualización", example = "2026-04-10T14:30:00Z")
    private Instant updatedAt;

    @Schema(description = "Fecha última sincronización con SOAP", example = "2026-04-14T22:00:00Z")
    private Instant lastSyncAt;

    @Schema(description = "Sistema fuente de los datos", example = "SOAP_EXTERNAL_API")
    private String source;

    @Schema(description = "Sistema de origen", example = "LEGACY-ERP")
    private String sourceSystem;

    /**
     * DTO para dimensiones del producto.
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Dimensiones físicas del producto")
    public static class ProductDimensionsDto {
        @Schema(description = "Largo", example = "344.4")
        private Double length;

        @Schema(description = "Ancho", example = "230.1")
        private Double width;

        @Schema(description = "Alto", example = "18.0")
        private Double height;

        @Schema(description = "Unidad de medida", example = "mm")
        private String unit;
    }

    /**
     * DTO para información de precios.
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Información detallada de precios")
    public static class ProductPricingDto {
        @Schema(description = "Precio base", example = "2499.99")
        private Double basePrice;

        @Schema(description = "Precio de venta", example = "2299.99")
        private Double salePrice;

        @Schema(description = "Porcentaje de descuento", example = "8.0")
        private Double discountPercent;

        @Schema(description = "Tasa de impuesto", example = "19.0")
        private Double taxRate;

        @Schema(description = "Monto de impuesto", example = "474.99")
        private Double taxAmount;

        @Schema(description = "Precio final", example = "2774.98")
        private Double finalPrice;
    }
}
