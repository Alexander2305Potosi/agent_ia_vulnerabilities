package com.example.ms_products.infrastructure.adapter;

import com.example.ms_products.domain.gateway.SoapGateway;
import com.example.ms_products.domain.model.ProductInfo;
import com.example.ms_products.domain.model.SoapProductRequest;
import com.example.ms_products.domain.model.SoapProductResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.nio.charset.StandardCharsets;

@Slf4j
@Component
@RequiredArgsConstructor
public class SoapClientAdapter implements SoapGateway {

    private final WebClient webClient;

    @Value("${soap.service.url:http://localhost:8081/ws/product}")
    private String soapServiceUrl;

    @Override
    public Mono<SoapProductResponse> callSoapService(SoapProductRequest request) {
        log.info("Calling SOAP service for product: {}", request.getProductId());

        String soapEnvelope = buildSoapEnvelope(request);

        return webClient.post()
                .uri(soapServiceUrl)
                .header(HttpHeaders.CONTENT_TYPE, "text/xml; charset=UTF-8")
                .header(HttpHeaders.SOAPACTION, "http://example.com/products/GetProductInfo")
                .bodyValue(soapEnvelope)
                .retrieve()
                .bodyToMono(String.class)
                .flatMap(this::parseSoapResponse)
                .doOnNext(response -> log.info("SOAP response received for product: {}", request.getProductId()))
                .doOnError(error -> log.error("Error calling SOAP service: {}", error.getMessage()));
    }

    private String buildSoapEnvelope(SoapProductRequest request) {
        return String.format("""
            <?xml version="1.0" encoding="UTF-8"?>
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
                           xmlns:prod="http://example.com/products">
                <soap:Header/>
                <soap:Body>
                    <prod:GetProductInfoRequest>
                        <prod:ProductId>%s</prod:ProductId>
                    </prod:GetProductInfoRequest>
                </soap:Body>
            </soap:Envelope>
            """, escapeXml(request.getProductId()));
    }

    private Mono<SoapProductResponse> parseSoapResponse(String xmlResponse) {
        try {
            log.debug("Parsing SOAP response: {}", xmlResponse);

            ProductInfo productInfo = ProductInfo.builder()
                    .productId(extractValue(xmlResponse, "ProductId"))
                    .name(extractValue(xmlResponse, "Name"))
                    .description(extractValue(xmlResponse, "Description"))
                    .price(parseDoubleOrNull(extractValue(xmlResponse, "Price")))
                    .stockQuantity(parseIntOrNull(extractValue(xmlResponse, "StockQuantity")))
                    .category(extractValue(xmlResponse, "Category"))
                    .supplier(extractValue(xmlResponse, "Supplier"))
                    .build();

            return Mono.just(SoapProductResponse.builder()
                    .success(true)
                    .message("Product retrieved successfully")
                    .productInfo(productInfo)
                    .build());

        } catch (Exception e) {
            log.error("Error parsing SOAP response: {}", e.getMessage());
            return Mono.just(SoapProductResponse.builder()
                    .success(false)
                    .message("Error parsing response: " + e.getMessage())
                    .build());
        }
    }

    private String extractValue(String xml, String tagName) {
        String pattern = "<(?:[^>:]*:)?" + tagName + ">([^<]+)</(?:[^>:]*:)?" + tagName + ">";
        java.util.regex.Pattern r = java.util.regex.Pattern.compile(pattern);
        java.util.regex.Matcher m = r.matcher(xml);
        return m.find() ? m.group(1) : null;
    }

    private Double parseDoubleOrNull(String value) {
        try {
            return value != null ? Double.parseDouble(value) : null;
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private Integer parseIntOrNull(String value) {
        try {
            return value != null ? Integer.parseInt(value) : null;
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private String escapeXml(String input) {
        if (input == null) return "";
        return input.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\"", "&quot;")
                .replace("'", "&apos;");
    }
}
