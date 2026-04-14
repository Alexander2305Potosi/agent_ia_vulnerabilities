package com.example.ms_products.domain.usecase;

import com.example.ms_products.domain.gateway.SoapGateway;
import com.example.ms_products.domain.model.ProductInfo;
import com.example.ms_products.domain.model.SoapProductRequest;
import com.example.ms_products.domain.model.SoapProductResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

@Service
@Slf4j
@RequiredArgsConstructor
public class GetProductFromSoapUseCase {

    private final SoapGateway soapGateway;

    public Mono<ProductInfo> execute(String productId) {
        log.info("Executing use case to get product from SOAP service: {}", productId);

        SoapProductRequest request = SoapProductRequest.builder()
                .productId(productId)
                .operation("GetProductInfo")
                .build();

        return soapGateway.callSoapService(request)
                .flatMap(response -> {
                    if (Boolean.TRUE.equals(response.getSuccess()) && response.getProductInfo() != null) {
                        log.info("Product retrieved successfully from SOAP: {}", productId);
                        return Mono.just(response.getProductInfo());
                    } else {
                        String message = response.getMessage() != null ? response.getMessage() : "Product not found";
                        log.warn("SOAP service returned error for product {}: {}", productId, message);
                        return Mono.error(new ProductNotFoundException(message));
                    }
                })
                .doOnError(error -> log.error("Error calling SOAP service for product {}: {}", productId, error.getMessage()));
    }

    public static class ProductNotFoundException extends RuntimeException {
        public ProductNotFoundException(String message) {
            super(message);
        }
    }
}
