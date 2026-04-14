package com.example.ms_products.domain.usecase;

import com.example.ms_products.domain.gateway.SoapGateway;
import com.example.ms_products.domain.model.ProductInfo;
import com.example.ms_products.domain.model.SoapProductRequest;
import com.example.ms_products.domain.model.SoapProductResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class GetProductFromSoapUseCaseTest {

    @Mock
    private SoapGateway soapGateway;

    private GetProductFromSoapUseCase useCase;

    @BeforeEach
    void setUp() {
        useCase = new GetProductFromSoapUseCase(soapGateway);
    }

    @Test
    void execute_shouldReturnProduct_whenSoapServiceReturnsSuccess() {
        // Given
        String productId = "PROD-001";
        ProductInfo expectedProduct = ProductInfo.builder()
                .productId(productId)
                .name("Test Product")
                .description("Test Description")
                .price(99.99)
                .stockQuantity(100)
                .category("ELECTRONICS")
                .supplier("Test Supplier")
                .build();

        SoapProductResponse soapResponse = SoapProductResponse.builder()
                .success(true)
                .message("Success")
                .productInfo(expectedProduct)
                .build();

        when(soapGateway.callSoapService(any(SoapProductRequest.class)))
                .thenReturn(Mono.just(soapResponse));

        // When & Then
        StepVerifier.create(useCase.execute(productId))
                .expectNextMatches(product ->
                        product.getProductId().equals(productId) &&
                        product.getName().equals("Test Product"))
                .verifyComplete();

        verify(soapGateway).callSoapService(any(SoapProductRequest.class));
    }

    @Test
    void execute_shouldReturnError_whenSoapServiceReturnsFailure() {
        // Given
        String productId = "PROD-999";
        SoapProductResponse soapResponse = SoapProductResponse.builder()
                .success(false)
                .message("Product not found")
                .build();

        when(soapGateway.callSoapService(any(SoapProductRequest.class)))
                .thenReturn(Mono.just(soapResponse));

        // When & Then
        StepVerifier.create(useCase.execute(productId))
                .expectError(GetProductFromSoapUseCase.ProductNotFoundException.class)
                .verify();
    }

    @Test
    void execute_shouldReturnError_whenSoapServiceThrowsException() {
        // Given
        String productId = "PROD-001";

        when(soapGateway.callSoapService(any(SoapProductRequest.class)))
                .thenReturn(Mono.error(new RuntimeException("Connection error")));

        // When & Then
        StepVerifier.create(useCase.execute(productId))
                .expectError(RuntimeException.class)
                .verify();
    }
}
