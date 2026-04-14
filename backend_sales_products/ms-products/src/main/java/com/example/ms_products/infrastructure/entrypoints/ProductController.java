package com.example.ms_products.infrastructure.entrypoints;

import com.example.ms_products.domain.model.ProductInfo;
import com.example.ms_products.domain.usecase.GetProductFromSoapUseCase;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/v1/products")
@RequiredArgsConstructor
@Slf4j
public class ProductController {

    private final GetProductFromSoapUseCase getProductFromSoapUseCase;

    @GetMapping("/soap/{productId}")
    public Mono<ResponseEntity<ProductInfo>> getProductFromSoap(@PathVariable String productId) {
        log.info("REST request to get product from SOAP service: {}", productId);

        return getProductFromSoapUseCase.execute(productId)
                .map(ResponseEntity::ok)
                .onErrorResume(GetProductFromSoapUseCase.ProductNotFoundException.class,
                        error -> {
                            log.warn("Product not found: {}", error.getMessage());
                            return Mono.just(ResponseEntity.status(HttpStatus.NOT_FOUND).build());
                        })
                .onErrorResume(error -> {
                    log.error("Error processing request: {}", error.getMessage());
                    return Mono.just(ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build());
                });
    }

    @GetMapping("/health")
    public Mono<ResponseEntity<String>> health() {
        return Mono.just(ResponseEntity.ok("OK"));
    }
}
