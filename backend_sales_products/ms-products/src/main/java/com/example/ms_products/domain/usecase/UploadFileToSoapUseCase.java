package com.example.ms_products.domain.usecase;

import com.example.ms_products.domain.gateway.SoapGateway;
import com.example.ms_products.domain.model.SoapProductResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.Instant;
import java.util.Base64;

/**
 * Caso de uso para subir información de documentos al servicio SOAP externo.
 * Procesa documentos codificados en base64 y los envía al servicio SOAP.
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class UploadFileToSoapUseCase {

    private final SoapGateway soapGateway;

    /**
     * Ejecuta la subida de documento al servicio SOAP.
     *
     * @param entityId ID de la entidad asociada (producto, cliente, etc.)
     * @param fileName nombre del archivo
     * @param fileSize tamaño del archivo en bytes
     * @param fileExtension extensión del archivo
     * @param fileContentBase64 contenido del archivo codificado en base64
     * @return Mono con la respuesta del servicio SOAP
     */
    public Mono<FileUploadResult> execute(
            String entityId,
            String fileName,
            Long fileSize,
            String fileExtension,
            String fileContentBase64) {

        log.info("[USECASE] Iniciando subida de documento para entidad: {}, archivo: {}", entityId, fileName);

        Instant start = Instant.now();

        // Decodificar contenido base64
        byte[] fileContent;
        try {
            fileContent = Base64.getDecoder().decode(fileContentBase64);
            log.debug("[USECASE] Documento decodificado exitosamente: {} bytes", fileContent.length);
        } catch (IllegalArgumentException e) {
            log.error("[USECASE] Error decodificando base64: {}", e.getMessage());
            return Mono.error(new InvalidFileException("Contenido base64 inválido: " + e.getMessage()));
        }

        // Validar que el tamaño coincida
        if (fileContent.length != fileSize) {
            log.warn("[USECASE] Tamaño de documento no coincide: esperado={}, actual={}", fileSize, fileContent.length);
        }

        return soapGateway.callSoapServiceWithFile(entityId, fileName, fileSize, fileExtension, fileContent)
                .flatMap(response -> processResponse(entityId, fileName, response, start))
                .doOnSuccess(result -> {
                    long duration = java.time.Duration.between(start, Instant.now()).toMillis();
                    log.info("[USECASE] Documento {} subido exitosamente en {}ms", fileName, duration);
                })
                .doOnError(error -> {
                    long duration = java.time.Duration.between(start, Instant.now()).toMillis();
                    log.error("[USECASE] Error subiendo documento {} después de {}ms: {}", fileName, duration, error.getMessage());
                });
    }

    /**
     * Procesa la respuesta SOAP y construye el resultado.
     */
    private Mono<FileUploadResult> processResponse(
            String entityId,
            String fileName,
            SoapProductResponse response,
            Instant startTime) {

        long processingTimeMs = java.time.Duration.between(startTime, Instant.now()).toMillis();

        if (Boolean.TRUE.equals(response.getSuccess())) {
            return Mono.just(FileUploadResult.builder()
                    .success(true)
                    .message(response.getMessage() != null ? response.getMessage() : "Documento subido exitosamente")
                    .documentId(response.getFileId())
                    .entityId(entityId)
                    .fileName(fileName)
                    .fileUrl(response.getFileUrl())
                    .status("COMPLETED")
                    .responseCode("200")
                    .processedAt(Instant.now())
                    .processingTimeMs(processingTimeMs)
                    .requestId(response.getRequestId())
                    .build());
        } else {
            String errorMessage = response.getMessage() != null ? response.getMessage() : "Error desconocido del servicio SOAP";
            log.warn("[USECASE] SOAP retornó error para documento {}: {}", fileName, errorMessage);
            return Mono.just(FileUploadResult.builder()
                    .success(false)
                    .message(errorMessage)
                    .entityId(entityId)
                    .fileName(fileName)
                    .status("FAILED")
                    .responseCode(response.getErrorCode() != null ? response.getErrorCode() : "500")
                    .processedAt(Instant.now())
                    .processingTimeMs(processingTimeMs)
                    .validationErrors(errorMessage)
                    .build());
        }
    }

    /**
     * DTO interno para resultado de subida de documento.
     */
    @lombok.Data
    @lombok.Builder
    @lombok.NoArgsConstructor
    @lombok.AllArgsConstructor
    public static class FileUploadResult {
        private Boolean success;
        private String message;
        private String documentId;
        private String entityId;
        private String fileName;
        private Long fileSize;
        private String fileUrl;
        private String status;
        private String responseCode;
        private Instant processedAt;
        private Long processingTimeMs;
        private String requestId;
        private String validatedChecksum;
        private String validationErrors;
    }

    /**
     * Excepción para documentos inválidos.
     */
    public static class InvalidFileException extends RuntimeException {
        public InvalidFileException(String message) {
            super(message);
        }
    }

    /**
     * Excepción para timeout del servicio SOAP.
     */
    public static class SoapServiceTimeoutException extends RuntimeException {
        public SoapServiceTimeoutException(String message) {
            super(message);
        }
    }
}
