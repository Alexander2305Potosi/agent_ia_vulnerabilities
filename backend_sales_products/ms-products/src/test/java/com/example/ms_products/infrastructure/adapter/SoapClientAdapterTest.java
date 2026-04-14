package com.example.ms_products.infrastructure.adapter;

import com.example.ms_products.domain.model.SoapProductRequest;
import com.example.ms_products.domain.model.SoapProductResponse;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.test.StepVerifier;

import java.io.IOException;

import static org.junit.jupiter.api.Assertions.*;

class SoapClientAdapterTest {

    private MockWebServer mockWebServer;
    private SoapClientAdapter soapClientAdapter;

    @BeforeEach
    void setUp() {
        mockWebServer = new MockWebServer();
        WebClient webClient = WebClient.builder()
                .baseUrl(mockWebServer.url("/").toString())
                .build();
        soapClientAdapter = new SoapClientAdapter(webClient);
    }

    @AfterEach
    void tearDown() throws IOException {
        mockWebServer.shutdown();
    }

    @Test
    void callSoapService_shouldReturnSuccessResponse_whenSoapResponseIsValid() {
        // Given
        String soapResponse = """
            <?xml version="1.0" encoding="UTF-8"?>
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Body>
                    <GetProductInfoResponse xmlns="http://example.com/products">
                        <ProductId>PROD-001</ProductId>
                        <Name>Test Product</Name>
                        <Description>Test Description</Description>
                        <Price>99.99</Price>
                        <StockQuantity>100</StockQuantity>
                        <Category>ELECTRONICS</Category>
                        <Supplier>Test Supplier</Supplier>
                    </GetProductInfoResponse>
                </soap:Body>
            </soap:Envelope>
            """;

        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "text/xml")
                .setBody(soapResponse));

        SoapProductRequest request = SoapProductRequest.builder()
                .productId("PROD-001")
                .operation("GetProductInfo")
                .build();

        // When & Then
        StepVerifier.create(soapClientAdapter.callSoapService(request))
                .assertNext(response -> {
                    assertTrue(response.getSuccess());
                    assertNotNull(response.getProductInfo());
                    assertEquals("PROD-001", response.getProductInfo().getProductId());
                    assertEquals("Test Product", response.getProductInfo().getName());
                    assertEquals(99.99, response.getProductInfo().getPrice());
                })
                .verifyComplete();
    }

    @Test
    void callSoapService_shouldReturnErrorResponse_whenSoapResponseIsEmpty() {
        // Given
        String soapResponse = """
            <?xml version="1.0" encoding="UTF-8"?>
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Body>
                    <GetProductInfoResponse xmlns="http://example.com/products"/>
                </soap:Body>
            </soap:Envelope>
            """;

        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "text/xml")
                .setBody(soapResponse));

        SoapProductRequest request = SoapProductRequest.builder()
                .productId("PROD-999")
                .operation("GetProductInfo")
                .build();

        // When & Then
        StepVerifier.create(soapClientAdapter.callSoapService(request))
                .assertNext(response -> {
                    assertTrue(response.getSuccess());
                    assertNull(response.getProductInfo().getName());
                })
                .verifyComplete();
    }

    @Test
    void callSoapService_shouldReturnError_whenServerReturns500() {
        // Given
        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(500)
                .setHeader("Content-Type", "text/xml")
                .setBody("Internal Server Error"));

        SoapProductRequest request = SoapProductRequest.builder()
                .productId("PROD-001")
                .operation("GetProductInfo")
                .build();

        // When & Then
        StepVerifier.create(soapClientAdapter.callSoapService(request))
                .expectError()
                .verify();
    }
}
