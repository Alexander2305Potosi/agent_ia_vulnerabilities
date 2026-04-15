package com.example.ms_products.domain.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Modelo de dominio para respuesta del servicio SOAP.
 * Soporta respuestas de consulta de producto y de subida de archivos.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SoapProductResponse {

    // Campos comunes de respuesta
    private Boolean success;
    private String message;

    // Campos para respuesta de consulta de producto
    private ProductInfo productInfo;

    // Campos para respuesta de subida de archivo
    private String fileId;
    private String fileUrl;
    private String requestId;
    private String errorCode;
    private String status;
    private Long processingTimeMs;
}
