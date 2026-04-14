package com.example.ms_products.infrastructure.entrypoints.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.UUID;

/**
 * DTO estándar para respuestas de error en la API.
 * Proporciona información estructurada sobre errores para facilitar debugging.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
@Schema(description = "Respuesta estándar de error de la API")
public class ErrorResponse {

    @Schema(description = "Timestamp del error en formato ISO-8601", example = "2026-04-14T17:30:00Z")
    private Instant timestamp;

    @Schema(description = "Código HTTP de error", example = "404")
    private int status;

    @Schema(description = "Código de error interno de la aplicación", example = "PRODUCT_NOT_FOUND")
    private String errorCode;

    @Schema(description = "Mensaje descriptivo del error", example = "Producto no encontrado con ID: PROD-999")
    private String message;

    @Schema(description = "Ruta de la solicitud que generó el error", example = "/api/v1/products/PROD-999")
    private String path;

    @Schema(description = "ID de trazabilidad único para debugging", example = "abc123-def456")
    private String traceId;

    @Schema(description = "Detalles adicionales del error (solo en desarrollo)", example = "Stack trace o información adicional")
    private String details;

    /**
     * Builder con valores por defecto.
     */
    public static class ErrorResponseBuilder {
        private Instant timestamp = Instant.now();
        private String traceId = UUID.randomUUID().toString().substring(0, 8);
    }
}
