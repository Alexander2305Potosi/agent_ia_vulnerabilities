package com.example.ms_products.infrastructure.adapter;

import com.example.ms_products.domain.gateway.SoapGateway;
import com.example.ms_products.domain.model.SoapProductRequest;
import com.example.ms_products.domain.model.SoapProductResponse;
import com.example.ms_products.domain.usecase.GetProductFromSoapUseCase;
import com.example.ms_products.infrastructure.soap.SoapEnvelopeBuilder;
import com.example.ms_products.infrastructure.soap.SoapResponseParser;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;

@Slf4j
@Component
@RequiredArgsConstructor
public class SoapClientAdapter implements SoapGateway {

    private final WebClient webClient;
    private final SoapEnvelopeBuilder envelopeBuilder;
    private final SoapResponseParser responseParser;

    @Value("${soap.service.url:http://localhost:8081/ws/product}")
    private String soapServiceUrl;

    @Value("${soap.service.timeout:10000}")
    private int soapTimeout;

    @Override
    public Mono<SoapProductResponse> callSoapService(SoapProductRequest request) {
        log.info("Calling SOAP service for product: {} (timeout: {}ms)", request.getProductId(), soapTimeout);

        // Usar JAXB para construir el envelope SOAP (reemplaza String.format manual)
        String soapEnvelope = envelopeBuilder.buildSoapEnvelope(request.getProductId());

        return webClient.post()
                .uri(soapServiceUrl)
                .header(HttpHeaders.CONTENT_TYPE, "text/xml; charset=UTF-8")
                .header("SOAPAction", "http://example.com/products/GetProductInfo")
                .bodyValue(soapEnvelope)
                .retrieve()
                .bodyToMono(String.class)
                // Timeout a nivel de infraestructura (adapter) - buena práctica
                .timeout(Duration.ofMillis(soapTimeout),
                        Mono.error(new GetProductFromSoapUseCase.SoapServiceTimeoutException(
                                "Timeout esperando respuesta SOAP para producto: " + request.getProductId())))
                // Usar JAXB para parsear la respuesta (reemplaza regex manual)
                .flatMap(xml -> responseParser.parseSoapResponse(xml)
                        .map(productInfo -> SoapProductResponse.builder()
                                .success(true)
                                .message("Product retrieved successfully")
                                .productInfo(productInfo)
                                .build()))
                .doOnNext(response -> log.info("SOAP response received for product: {}", request.getProductId()))
                .doOnError(error -> log.error("Error calling SOAP service: {}", error.getMessage()));
    }

    @Override
    public Mono<SoapProductResponse> callSoapServiceWithFile(
            String productId,
            String fileName,
            Long fileSize,
            String fileExtension,
            byte[] content) {

        log.info("Calling SOAP service with file: {} ({} bytes, timeout: {}ms)",
                fileName, fileSize, soapTimeout);

        // Construir envelope SOAP con información del archivo
        String soapEnvelope = envelopeBuilder.buildSoapEnvelopeWithFile(
                productId, fileName, fileSize, fileExtension, content);

        return webClient.post()
                .uri(soapServiceUrl)
                .header(HttpHeaders.CONTENT_TYPE, "text/xml; charset=UTF-8")
                .header("SOAPAction", "http://example.com/products/GetProductInfo")
                .bodyValue(soapEnvelope)
                .retrieve()
                .bodyToMono(String.class)
                // Timeout a nivel de infraestructura (adapter) - buena práctica
                .timeout(Duration.ofMillis(soapTimeout),
                        Mono.error(new GetProductFromSoapUseCase.SoapServiceTimeoutException(
                                "Timeout esperando respuesta SOAP para archivo: " + fileName)))
                .flatMap(xml -> responseParser.parseSoapResponse(xml)
                        .map(productInfo -> SoapProductResponse.builder()
                                .success(true)
                                .message("File processed successfully")
                                .productInfo(productInfo)
                                .build()))
                .doOnNext(response -> log.info("SOAP response received for file: {}", fileName))
                .doOnError(error -> log.error("Error calling SOAP service with file: {}", error.getMessage()));
    }
}
