package com.example.ms_products.infrastructure.adapter;

import com.example.ms_products.domain.gateway.SoapGateway;
import com.example.ms_products.domain.model.SoapProductRequest;
import com.example.ms_products.domain.model.SoapProductResponse;
import com.example.ms_products.domain.usecase.UploadFileToSoapUseCase;
import com.example.ms_products.infrastructure.soap.SoapEnvelopeBuilder;
import com.example.ms_products.infrastructure.soap.SoapResponseParser;
import com.example.ms_products.infrastructure.soap.UploadDocumentResponse;
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
        log.info("Calling SOAP service for entity: {} (timeout: {}ms)", request.getProductId(), soapTimeout);

        String soapEnvelope = envelopeBuilder.buildSoapEnvelope(request.getProductId());

        return webClient.post()
                .uri(soapServiceUrl)
                .header(HttpHeaders.CONTENT_TYPE, "text/xml; charset=UTF-8")
                .header("SOAPAction", "http://example.com/products/UploadDocument")
                .bodyValue(soapEnvelope)
                .retrieve()
                .bodyToMono(String.class)
                .timeout(Duration.ofMillis(soapTimeout),
                        Mono.error(new UploadFileToSoapUseCase.SoapServiceTimeoutException(
                                "Timeout esperando respuesta SOAP para entidad: " + request.getProductId())))
                .flatMap(xml -> responseParser.parseUploadDocumentResponse(xml)
                        .map(this::mapToSoapProductResponse))
                .doOnNext(response -> log.info("SOAP response received for entity: {}", request.getProductId()))
                .doOnError(error -> log.error("Error calling SOAP service: {}", error.getMessage()));
    }

    @Override
    public Mono<SoapProductResponse> callSoapServiceWithFile(
            String entityId,
            String fileName,
            Long fileSize,
            String fileExtension,
            byte[] content) {

        log.info("Calling SOAP service with file: {} for entity: {} ({} bytes, timeout: {}ms)",
                fileName, entityId, fileSize, soapTimeout);

        String soapEnvelope = envelopeBuilder.buildSoapEnvelopeWithFile(
                entityId, fileName, fileSize, fileExtension, content);

        return webClient.post()
                .uri(soapServiceUrl)
                .header(HttpHeaders.CONTENT_TYPE, "text/xml; charset=UTF-8")
                .header("SOAPAction", "http://example.com/products/UploadDocument")
                .bodyValue(soapEnvelope)
                .retrieve()
                .bodyToMono(String.class)
                .timeout(Duration.ofMillis(soapTimeout),
                        Mono.error(new UploadFileToSoapUseCase.SoapServiceTimeoutException(
                                "Timeout esperando respuesta SOAP para archivo: " + fileName)))
                .flatMap(xml -> responseParser.parseUploadDocumentResponse(xml)
                        .map(this::mapToSoapProductResponse))
                .doOnNext(response -> log.info("SOAP response received for file: {}", fileName))
                .doOnError(error -> log.error("Error calling SOAP service with file: {}", error.getMessage()));
    }

    /**
     * Mapea UploadDocumentResponse a SoapProductResponse para compatibilidad.
     */
    private SoapProductResponse mapToSoapProductResponse(UploadDocumentResponse uploadResponse) {
        return SoapProductResponse.builder()
                .success(uploadResponse.getSuccess())
                .message(uploadResponse.getMessage())
                .fileId(uploadResponse.getDocumentId())
                .fileUrl(uploadResponse.getFileUrl())
                .requestId(uploadResponse.getRequestId())
                .errorCode(uploadResponse.getErrorCode())
                .status(uploadResponse.getStatus())
                .processingTimeMs(uploadResponse.getProcessingTimeMs())
                .build();
    }
}
