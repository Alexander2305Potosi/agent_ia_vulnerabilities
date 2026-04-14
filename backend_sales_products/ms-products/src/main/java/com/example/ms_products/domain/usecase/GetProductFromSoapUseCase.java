package com.example.ms_products.domain.usecase;

import com.example.ms_products.domain.gateway.SoapGateway;
import com.example.ms_products.domain.model.ProductInfo;
import com.example.ms_products.domain.model.SoapProductRequest;
import com.example.ms_products.domain.model.SoapProductResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

/**
 * Caso de uso para obtener información de productos desde servicio SOAP.
 * El timeout se maneja en la capa de infraestructura (Adapter) siguiendo buenas prácticas.
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class GetProductFromSoapUseCase {

    private final SoapGateway soapGateway;

    /**
     * Ejecuta la consulta de producto.
     * El timeout es responsabilidad del adapter de infraestructura.
     *
     * @param productId ID del producto a consultar
     * @return Mono con la información del producto
     */
    public Mono<ProductInfo> execute(String productId) {
        log.info("[USECASE] Iniciando consulta SOAP para producto: {}", productId);

        SoapProductRequest request = SoapProductRequest.builder()
                .productId(productId)
                .operation("GetProductInfo")
                .build();

        return soapGateway.callSoapService(request)
                .flatMap(response -> processResponse(productId, response))
                .doOnSuccess(result -> log.info("[USECASE] Producto {} obtenido exitosamente", productId))
                .doOnError(error -> log.error("[USECASE] Error consultando producto {}: {}",
                        productId, error.getMessage()));
    }

    /**
     * Procesa la respuesta SOAP y determina si fue exitosa o no.
     */
    private Mono<ProductInfo> processResponse(String productId, SoapProductResponse response) {
        if (Boolean.TRUE.equals(response.getSuccess()) && response.getProductInfo() != null) {
            return Mono.just(response.getProductInfo());
        } else {
            String message = response.getMessage() != null ? response.getMessage() : "Product not found";
            log.warn("[USECASE] SOAP retornó error para producto {}: {}", productId, message);
            return Mono.error(new ProductNotFoundException(message));
        }
    }

    /**
     * Excepción para cuando el producto no se encuentra.
     */
    public static class ProductNotFoundException extends RuntimeException {
        public ProductNotFoundException(String message) {
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
