package com.example.ms_products.domain.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Modelo de dominio para request SOAP de producto.
 * Incluye parámetros enriquecidos para la consulta al servicio SOAP externo.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SoapProductRequest {

    // Identificación del producto
    private String productId;

    // Operación a realizar
    private String operation;

    // Identificador de la solicitud (para trazabilidad)
    private String requestId;

    // Timestamp de la solicitud
    private String timestamp;

    // Opciones de inclusión de datos
    private Boolean includeHistory;
    private Boolean includePricing;
    private Boolean includeInventory;
    private Boolean includeSupplierInfo;
    private Boolean includeRatings;
    private Boolean includeImages;

    // Filtros adicionales
    private String preferredCurrency;
    private String warehouseFilter;

    // Metadatos del request
    private String sourceSystem;
    private String userId;
    private String sessionId;
}
