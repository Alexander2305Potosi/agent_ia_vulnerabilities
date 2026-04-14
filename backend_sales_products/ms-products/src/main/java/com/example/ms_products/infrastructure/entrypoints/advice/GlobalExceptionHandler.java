package com.example.ms_products.infrastructure.entrypoints.advice;

import com.example.ms_products.domain.usecase.GetProductFromSoapUseCase;
import com.example.ms_products.infrastructure.entrypoints.dto.ErrorResponse;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.bind.support.WebExchangeBindException;
import org.springframework.web.server.ServerWebExchange;

import java.time.Instant;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Manejador global de excepciones para la API REST.
 * Proporciona respuestas de error estandarizadas y consistentes.
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final String ERROR_PRODUCT_NOT_FOUND = "PRODUCT_NOT_FOUND";
    private static final String ERROR_VALIDATION = "VALIDATION_ERROR";
    private static final String ERROR_SOAP_SERVICE = "SOAP_SERVICE_ERROR";
    private static final String ERROR_GENERIC = "INTERNAL_ERROR";

    /**
     * Maneja excepciones de producto no encontrado.
     */
    @ExceptionHandler(GetProductFromSoapUseCase.ProductNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    @ApiResponse(
            responseCode = "404",
            description = "Producto no encontrado",
            content = @Content(schema = @Schema(implementation = ErrorResponse.class))
    )
    public ResponseEntity<ErrorResponse> handleProductNotFound(
            GetProductFromSoapUseCase.ProductNotFoundException ex,
            ServerWebExchange exchange) {

        String traceId = generateTraceId();
        log.warn("[{}] Producto no encontrado: {}", traceId, ex.getMessage());

        ErrorResponse error = ErrorResponse.builder()
                .timestamp(Instant.now())
                .status(HttpStatus.NOT_FOUND.value())
                .errorCode(ERROR_PRODUCT_NOT_FOUND)
                .message(ex.getMessage())
                .path(exchange.getRequest().getPath().value())
                .traceId(traceId)
                .build();

        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
    }

    /**
     * Maneja errores de validación de entrada.
     */
    @ExceptionHandler(WebExchangeBindException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    @ApiResponse(
            responseCode = "400",
            description = "Error de validación en los datos de entrada",
            content = @Content(schema = @Schema(implementation = ErrorResponse.class))
    )
    public ResponseEntity<ErrorResponse> handleValidationErrors(
            WebExchangeBindException ex,
            ServerWebExchange exchange) {

        String traceId = generateTraceId();
        log.warn("[{}] Error de validación: {}", traceId, ex.getMessage());

        String errorMessage = ex.getBindingResult().getFieldErrors().stream()
                .map(error -> error.getField() + ": " + error.getDefaultMessage())
                .collect(Collectors.joining(", "));

        ErrorResponse error = ErrorResponse.builder()
                .timestamp(Instant.now())
                .status(HttpStatus.BAD_REQUEST.value())
                .errorCode(ERROR_VALIDATION)
                .message("Error de validación en la solicitud: " + errorMessage)
                .path(exchange.getRequest().getPath().value())
                .traceId(traceId)
                .build();

        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }

    /**
     * Maneja timeouts del servicio SOAP.
     */
    @ExceptionHandler(GetProductFromSoapUseCase.SoapServiceTimeoutException.class)
    @ResponseStatus(HttpStatus.REQUEST_TIMEOUT)
    @ApiResponse(
            responseCode = "408",
            description = "Timeout del servicio SOAP",
            content = @Content(schema = @Schema(implementation = ErrorResponse.class))
    )
    public ResponseEntity<ErrorResponse> handleSoapTimeout(
            GetProductFromSoapUseCase.SoapServiceTimeoutException ex,
            ServerWebExchange exchange) {

        String traceId = generateTraceId();
        log.warn("[{}] Timeout SOAP: {}", traceId, ex.getMessage());

        ErrorResponse error = ErrorResponse.builder()
                .timestamp(Instant.now())
                .status(HttpStatus.REQUEST_TIMEOUT.value())
                .errorCode("SOAP_TIMEOUT")
                .message("El servicio SOAP no respondió a tiempo. Por favor intente más tarde.")
                .path(exchange.getRequest().getPath().value())
                .traceId(traceId)
                .build();

        return ResponseEntity.status(HttpStatus.REQUEST_TIMEOUT).body(error);
    }

    /**
     * Maneja errores del servicio SOAP externo.
     */
    @ExceptionHandler({Exception.class, RuntimeException.class})
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    @ApiResponse(
            responseCode = "500",
            description = "Error interno del servidor",
            content = @Content(schema = @Schema(implementation = ErrorResponse.class))
    )
    public ResponseEntity<ErrorResponse> handleGenericException(
            Exception ex,
            ServerWebExchange exchange) {

        String traceId = generateTraceId();
        log.error("[{}] Error interno: {}", traceId, ex.getMessage(), ex);

        // Determinar si es un error del servicio SOAP
        String errorCode = ERROR_GENERIC;
        String message = "Error interno del servidor. Por favor intente más tarde.";

        if (ex.getMessage() != null && ex.getMessage().toLowerCase().contains("soap")) {
            errorCode = ERROR_SOAP_SERVICE;
            message = "Error comunicándose con el servicio SOAP externo. Por favor intente más tarde.";
        }

        ErrorResponse error = ErrorResponse.builder()
                .timestamp(Instant.now())
                .status(HttpStatus.INTERNAL_SERVER_ERROR.value())
                .errorCode(errorCode)
                .message(message)
                .path(exchange.getRequest().getPath().value())
                .traceId(traceId)
                .details(ex.getClass().getSimpleName() + ": " + ex.getMessage())
                .build();

        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
    }

    private String generateTraceId() {
        return UUID.randomUUID().toString().substring(0, 8);
    }
}
