package com.example.ms_products.infrastructure.entrypoints.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO para solicitud de subida de documento al servicio SOAP externo.
 * Permite enviar información del documento y su contenido en base64.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "Request para subir documento al servicio SOAP externo")
public class FileUploadRequest {

    @NotBlank(message = "El ID de la entidad es obligatorio")
    @Size(min = 3, max = 50, message = "El ID debe tener entre 3 y 50 caracteres")
    @Pattern(regexp = "^[a-zA-Z0-9\\-_]+$", message = "El ID solo puede contener letras, números, guiones y guiones bajos")
    @Schema(description = "ID de la entidad asociada al documento (producto, cliente, etc.)", example = "PROD-001", requiredMode = Schema.RequiredMode.REQUIRED)
    private String entityId;

    @NotBlank(message = "El nombre del archivo es obligatorio")
    @Size(max = 255, message = "El nombre del archivo no puede exceder 255 caracteres")
    @Schema(description = "Nombre del archivo incluyendo extensión", example = "documento-especificaciones.pdf", requiredMode = Schema.RequiredMode.REQUIRED)
    private String fileName;

    @NotNull(message = "El tamaño del archivo es obligatorio")
    @Schema(description = "Tamaño del archivo en bytes", example = "1048576", requiredMode = Schema.RequiredMode.REQUIRED)
    private Long fileSize;

    @NotBlank(message = "La extensión del archivo es obligatoria")
    @Pattern(regexp = "^[a-zA-Z0-9]+$", message = "La extensión solo puede contener caracteres alfanuméricos")
    @Schema(description = "Extensión del archivo sin el punto", example = "pdf", requiredMode = Schema.RequiredMode.REQUIRED)
    private String fileExtension;

    @NotBlank(message = "El contenido del archivo es obligatorio")
    @Schema(description = "Contenido del archivo codificado en base64",
            example = "JVBERi0xLjQKJeLjz9MKMyAwIG9iago8PC9UeXBlL1BhZ2UvUGFyZW50IDIgMCBS...",
            requiredMode = Schema.RequiredMode.REQUIRED)
    private String fileContentBase64;

    @Schema(description = "Tipo MIME del archivo", example = "application/pdf")
    private String mimeType;

    @Schema(description = "Descripción opcional del documento", example = "Especificaciones técnicas del documento")
    private String description;

    @Schema(description = "Checksum MD5 del archivo para validación de integridad", example = "d41d8cd98f00b204e9800998ecf8427e")
    private String checksum;

    @Schema(description = "Indica si el documento es público", example = "false")
    private Boolean isPublic;

    @Schema(description = "Categoría del documento", example = "SPECIFICATION")
    private String fileCategory;
}
