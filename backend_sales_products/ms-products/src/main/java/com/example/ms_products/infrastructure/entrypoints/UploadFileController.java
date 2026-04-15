package com.example.ms_products.infrastructure.entrypoints;

import com.example.ms_products.domain.usecase.UploadFileToSoapUseCase;
import com.example.ms_products.infrastructure.entrypoints.dto.ErrorResponse;
import com.example.ms_products.infrastructure.entrypoints.dto.FileUploadRequest;
import com.example.ms_products.infrastructure.entrypoints.dto.FileUploadResponseDto;
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
 * Controlador REST para gestión de documentos/archivos.
 * Expone endpoints para subir documentos al servicio SOAP externo.
 */
@RestController
@RequestMapping("/api/v1/documents")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Documentos", description = "API para gestión y subida de documentos al servicio SOAP externo")
public class UploadFileController {

    private final UploadFileToSoapUseCase uploadFileToSoapUseCase;

    /**
     * Sube información de un documento/archivo al servicio SOAP externo.
     * El archivo se envía codificado en base64 junto con sus metadatos.
     */
    @Operation(
            summary = "Subir documento al servicio SOAP",
            description = "Envía información de un documento (nombre, tamaño, extensión) y su contenido codificado en base64 " +
                    "al servicio SOAP externo para asociarlo con una entidad."
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "Documento procesado exitosamente",
                    content = @Content(schema = @Schema(implementation = FileUploadResponseDto.class))
            ),
            @ApiResponse(
                    responseCode = "400",
                    description = "Datos de documento inválidos o base64 malformado",
                    content = @Content(schema = @Schema(implementation = ErrorResponse.class))
            ),
            @ApiResponse(
                    responseCode = "429",
                    description = "Demasiadas solicitudes - Rate limit excedido",
                    content = @Content(schema = @Schema(implementation = ErrorResponse.class))
            ),
            @ApiResponse(
                    responseCode = "503",
                    description = "Servicio SOAP no disponible - Circuit breaker abierto",
                    content = @Content(schema = @Schema(implementation = ErrorResponse.class))
            ),
            @ApiResponse(
                    responseCode = "500",
                    description = "Error interno del servidor",
                    content = @Content(schema = @Schema(implementation = ErrorResponse.class))
            )
    })
    @PostMapping("/upload")
    @CircuitBreaker(name = "soapService", fallbackMethod = "uploadFileFallback")
    @RateLimiter(name = "documentApi")
    public Mono<ResponseEntity<FileUploadResponseDto>> uploadDocument(
            @Parameter(description = "Información del documento a subir", required = true)
            @RequestBody @Valid FileUploadRequest request) {

        Instant start = Instant.now();
        log.info("[API] POST /api/v1/documents/upload - Iniciando subida de documento: {} para entidad: {}",
                request.getFileName(), request.getEntityId());

        return uploadFileToSoapUseCase.execute(
                        request.getEntityId(),
                        request.getFileName(),
                        request.getFileSize(),
                        request.getFileExtension(),
                        request.getFileContentBase64()
                )
                .map(result -> FileUploadResponseDto.builder()
                        .success(result.getSuccess())
                        .message(result.getMessage())
                        .documentId(result.getDocumentId())
                        .entityId(result.getEntityId())
                        .fileName(result.getFileName())
                        .fileSize(result.getFileSize())
                        .fileUrl(result.getFileUrl())
                        .status(result.getStatus())
                        .responseCode(result.getResponseCode())
                        .processedAt(result.getProcessedAt())
                        .processingTimeMs(result.getProcessingTimeMs())
                        .requestId(result.getRequestId())
                        .validatedChecksum(result.getValidatedChecksum())
                        .validationErrors(result.getValidationErrors())
                        .build())
                .map(ResponseEntity::ok)
                .doOnSuccess(response -> {
                    Duration duration = Duration.between(start, Instant.now());
                    log.info("[API] POST /api/v1/documents/upload - Documento {} procesado en {} ms",
                            request.getFileName(), duration.toMillis());
                })
                .doOnError(error -> {
                    Duration duration = Duration.between(start, Instant.now());
                    log.error("[API] POST /api/v1/documents/upload - Error procesando documento {} después de {} ms: {}",
                            request.getFileName(), duration.toMillis(), error.getMessage());
                });
    }

    /**
     * Endpoint de verificación de salud del servicio.
     */
    @Operation(
            summary = "Health Check",
            description = "Verifica que el servicio de documentos esté operativo."
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
            description = "Retorna información básica sobre el servicio de documentos."
    )
    @GetMapping("/info")
    public Mono<ResponseEntity<Object>> getServiceInfo() {
        return Mono.just(ResponseEntity.ok(java.util.Map.of(
                "service", "ms-documents",
                "version", "2.0.0",
                "description", "Microservicio de gestión de documentos con integración SOAP"
        )));
    }

    /**
     * Fallback method para Circuit Breaker de subida de documento.
     */
    private Mono<ResponseEntity<FileUploadResponseDto>> uploadFileFallback(FileUploadRequest request, Exception ex) {
        log.warn("[CIRCUIT_BREAKER] Fallback ejecutado para subida de documento {}: {}", request.getFileName(), ex.getMessage());
        return Mono.just(ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                .body(FileUploadResponseDto.builder()
                        .success(false)
                        .message("Servicio SOAP no disponible - Circuit breaker abierto")
                        .entityId(request.getEntityId())
                        .fileName(request.getFileName())
                        .status("CIRCUIT_BREAKER_OPEN")
                        .responseCode("503")
                        .processedAt(Instant.now())
                        .build()));
    }
}
