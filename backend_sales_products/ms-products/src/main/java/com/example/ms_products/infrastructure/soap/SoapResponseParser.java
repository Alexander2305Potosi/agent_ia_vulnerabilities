package com.example.ms_products.infrastructure.soap;

import com.example.ms_products.domain.model.ProductInfo;
import jakarta.xml.bind.JAXBContext;
import jakarta.xml.bind.JAXBException;
import jakarta.xml.bind.Unmarshaller;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Mono;

import java.io.StringReader;

/**
 * Utilidad para parsear respuestas SOAP usando JAXB.
 * Reemplaza el parsing manual con regex por unmarshalling automático.
 */
@Slf4j
@Component
public class SoapResponseParser {

    private final JAXBContext responseContext;

    public SoapResponseParser() throws JAXBException {
        this.responseContext = JAXBContext.newInstance(GetProductInfoResponse.class);
    }

    /**
     * Parsea el XML de respuesta SOAP a un objeto ProductInfo usando JAXB.
     *
     * @param xmlResponse XML de respuesta del servicio SOAP
     * @return Mono con el ProductInfo parseado
     */
    public Mono<ProductInfo> parseSoapResponse(String xmlResponse) {
        try {
            log.debug("Parsing SOAP response con JAXB: {}", xmlResponse);

            // Crear unmarshaller
            Unmarshaller unmarshaller = responseContext.createUnmarshaller();

            // Extraer el contenido del Body SOAP (entre <soap:Body> o <Body>)
            String bodyContent = extractSoapBody(xmlResponse);
            if (bodyContent == null) {
                log.error("No se pudo extraer el cuerpo SOAP de la respuesta");
                return Mono.empty();
            }

            // Unmarshal el XML a objeto Java
            GetProductInfoResponse response = (GetProductInfoResponse) unmarshaller.unmarshal(
                    new StringReader(bodyContent)
            );

            // Mapear a ProductInfo del dominio
            ProductInfo productInfo = ProductInfo.builder()
                    .productId(response.getProductId())
                    .name(response.getName())
                    .description(response.getDescription())
                    .price(response.getPrice())
                    .stockQuantity(response.getStockQuantity())
                    .category(response.getCategory())
                    .supplier(response.getSupplier())
                    .build();

            return Mono.just(productInfo);

        } catch (JAXBException e) {
            log.error("Error parseando SOAP response con JAXB: {}", e.getMessage());
            return Mono.empty();
        }
    }

    /**
     * Extrae el contenido dentro del Body del envelope SOAP.
     */
    private String extractSoapBody(String xml) {
        // Buscar contenido entre <soap:Body>... </soap:Body> o <Body>...</Body>
        String[] patterns = {
            "(?s)<soap:Body>(.*)</soap:Body>",
            "(?s)<Body>(.*)</Body>",
            "(?s)<SOAP-ENV:Body>(.*)</SOAP-ENV:Body>"
        };

        for (String pattern : patterns) {
            java.util.regex.Pattern r = java.util.regex.Pattern.compile(pattern);
            java.util.regex.Matcher m = r.matcher(xml);
            if (m.find()) {
                return m.group(1).trim();
            }
        }

        // Si no encuentra Body, devolver el XML completo (puede ser solo el contenido)
        return xml;
    }
}
