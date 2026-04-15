package com.example.ms_products.infrastructure.entrypoints.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

/**
 * DTO para respuesta de subida de documento al servicio SOAP externo.
 * Contiene información del resultado y metadatos del documento procesado.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
@Schema(description = "Respuesta de la subida de documento al servicio SOAP")
public class FileUploadResponseDto {

    @Schema(description = "Indica si la subida fue exitosa", example = "true")
    private Boolean success;

    @Schema(description = "Mensaje descriptivo del resultado", example = "Documento subido exitosamente")
    private String message;

    @Schema(description = "ID del documento generado en el sistema SOAP", example = "DOC-2026-001")
    private String documentId;

    @Schema(description = "ID de la entidad asociada (producto, cliente, etc.)", example = "PROD-001")
    private String entityId;

    @Schema(description = "Nombre del archivo procesado", example = "documento-especificaciones.pdf")
    private String fileName;

    @Schema(description = "Tamaño del archivo en bytes", example = "1048576")
    private Long fileSize;

    @Schema(description = "URL de acceso al documento (si está disponible)", example = "https://storage.example.com/docs/DOC-2026-001.pdf")
    private String fileUrl;

    @Schema(description = "Estado del documento en el sistema SOAP", example = "COMPLETED")
    private String status;

    @Schema(description = "Código de respuesta del servicio SOAP", example = "200")
    private String responseCode;

    @Schema(description = "Timestamp de procesamiento", example = "2026-04-15T10:30:00Z")
    private Instant processedAt;

    @Schema(description = "Tiempo de procesamiento en milisegundos", example = "245")
    private Long processingTimeMs;

    @Schema(description = "ID de trazabilidad para seguimiento", example = "req-550e8400-e29b-41d4-a716-446655440000")
    private String requestId;

    @Schema(description = "Checksum MD5 validado", example = "d41d8cd98f00b204e9800998ecf8427e")
    private String validatedChecksum;

    @Schema(description = "Errores de validación si existen")
    private String validationErrors;
}
