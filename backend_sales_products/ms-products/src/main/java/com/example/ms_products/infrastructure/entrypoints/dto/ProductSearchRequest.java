package com.example.ms_products.infrastructure.entrypoints.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO para solicitud de búsqueda de producto por ID.
 * Incluye validaciones de entrada para prevenir inyecciones y datos inválidos.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "Request para buscar un producto por su ID")
public class ProductSearchRequest {

    @NotBlank(message = "El ID del producto es obligatorio")
    @Size(min = 3, max = 50, message = "El ID debe tener entre 3 y 50 caracteres")
    @Pattern(regexp = "^[a-zA-Z0-9\\-_]+$", message = "El ID solo puede contener letras, números, guiones y guiones bajos")
    @Schema(description = "Identificador único del producto", example = "PROD-001", requiredMode = Schema.RequiredMode.REQUIRED)
    private String productId;
}
