package com.example.ms_products.infrastructure.entrypoints;

import com.example.ms_products.infrastructure.entrypoints.dto.ProductResponseDto;
import com.example.ms_products.infrastructure.entrypoints.dto.ProductSearchRequest;
import com.example.ms_products.infrastructure.mapper.ProductMapper;
import com.example.ms_products.domain.usecase.GetProductFromSoapUseCase;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.github.resilience4j.ratelimiter.annotation.RateLimiter;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.time.Instant;

/**
 * Controlador REST para gestión de productos.
 * Expone endpoints para consultar productos desde el servicio SOAP externo.
 */
@RestController
@RequestMapping("/api/v1/products")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Productos", description = "API para consulta de productos desde servicio SOAP externo")
public class ProductController {

    private final GetProductFromSoapUseCase getProductFromSoapUseCase;
    private final ProductMapper productMapper;

    /**
     * Obtiene información de un producto desde el servicio SOAP externo.
     * Este endpoint está protegido con Circuit Breaker y Rate Limiter.
     */
    @Operation(
            summary = "Obtener producto por ID",
            description = "Consulta la información de un producto específico desde el servicio SOAP externo. " +
                    "El ID debe cumplir con el patrón alfanumérico con guiones permitidos."
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "Producto encontrado exitosamente",
                    content = @Content(schema = @Schema(implementation = ProductResponseDto.class))
            ),
            @ApiResponse(
                    responseCode = "400",
                    description = "ID de producto inválido",
                    content = @Content(schema = @Schema(implementation = com.example.ms_products.infrastructure.entrypoints.dto.ErrorResponse.class))
            ),
            @ApiResponse(
                    responseCode = "404",
                    description = "Producto no encontrado",
                    content = @Content(schema = @Schema(implementation = com.example.ms_products.infrastructure.entrypoints.dto.ErrorResponse.class))
            ),
            @ApiResponse(
                    responseCode = "429",
                    description = "Demasiadas solicitudes - Rate limit excedido",
                    content = @Content(schema = @Schema(implementation = com.example.ms_products.infrastructure.entrypoints.dto.ErrorResponse.class))
            ),
            @ApiResponse(
                    responseCode = "503",
                    description = "Servicio SOAP no disponible - Circuit breaker abierto",
                    content = @Content(schema = @Schema(implementation = com.example.ms_products.infrastructure.entrypoints.dto.ErrorResponse.class))
            ),
            @ApiResponse(
                    responseCode = "500",
                    description = "Error interno del servidor",
                    content = @Content(schema = @Schema(implementation = com.example.ms_products.infrastructure.entrypoints.dto.ErrorResponse.class))
            )
    })
    @GetMapping("/{productId}")
    @CircuitBreaker(name = "soapService", fallbackMethod = "getProductFallback")
    @RateLimiter(name = "productApi")
    public Mono<ResponseEntity<ProductResponseDto>> getProductById(
            @Parameter(description = "ID del producto a consultar", example = "PROD-001", required = true)
            @PathVariable @Valid String productId) {

        Instant start = Instant.now();
        log.info("[API] GET /api/v1/products/{} - Iniciando consulta", productId);

        // Crear request validado
        ProductSearchRequest request = ProductSearchRequest.builder()
                .productId(productId)
                .build();

        return getProductFromSoapUseCase.execute(request.getProductId())
                .map(productMapper::toDto)
                .map(ResponseEntity::ok)
                .doOnSuccess(response -> {
                    Duration duration = Duration.between(start, Instant.now());
                    log.info("[API] GET /api/v1/products/{} - Éxito en {} ms", productId, duration.toMillis());
                })
                .doOnError(error -> {
                    Duration duration = Duration.between(start, Instant.now());
                    log.error("[API] GET /api/v1/products/{} - Error después de {} ms: {}",
                            productId, duration.toMillis(), error.getMessage());
                });
    }

    /**
     * Endpoint de verificación de salud del servicio.
     */
    @Operation(
            summary = "Health Check",
            description = "Verifica que el servicio esté operativo y respondiendo correctamente."
    )
    @ApiResponse(
            responseCode = "200",
            description = "Servicio operativo",
            content = @Content(schema = @Schema(implementation = String.class))
    )
    @GetMapping("/health")
    public Mono<ResponseEntity<String>> health() {
        return Mono.just(ResponseEntity.ok("OK"));
    }

    /**
     * Endpoint de información del servicio.
     */
    @Operation(
            summary = "Información del servicio",
            description = "Retorna información básica sobre el servicio de productos."
    )
    @GetMapping("/info")
    public Mono<ResponseEntity<Object>> getServiceInfo() {
        return Mono.just(ResponseEntity.ok(java.util.Map.of(
                "service", "ms-products",
                "version", "1.0.0",
                "description", "Microservicio de productos con integración SOAP"
        )));
    }

    /**
     * Fallback method para Circuit Breaker.
     * Se ejecuta cuando el servicio SOAP está caído o el Circuit Breaker está abierto.
     */
    private Mono<ResponseEntity<ProductResponseDto>> getProductFallback(String productId, Exception ex) {
        log.warn("[CIRCUIT_BREAKER] Fallback ejecutado para producto {}: {}", productId, ex.getMessage());
        return Mono.just(ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).build());
    }
}
