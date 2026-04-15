package com.example.ms_products.infrastructure.soap;

import com.example.ms_products.domain.model.ProductInfo;
import jakarta.xml.bind.JAXBContext;
import jakarta.xml.bind.JAXBException;
import jakarta.xml.bind.Unmarshaller;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Mono;

import java.io.StringReader;
import java.time.Instant;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Utilidad para parsear respuestas SOAP usando JAXB.
 * Mapea la respuesta del servicio SOAP a ProductInfo del dominio.
 */
@Slf4j
@Component
public class SoapResponseParser {

    private final JAXBContext responseContext;

    public SoapResponseParser() throws JAXBException {
        this.responseContext = JAXBContext.newInstance(UploadDocumentResponse.class);
    }

    /**
     * Parsea el XML de respuesta SOAP usando JAXB.
     *
     * @param xmlResponse XML de respuesta del servicio SOAP
     * @return Mono con el ProductInfo parseado (para compatibilidad)
     */
    public Mono<ProductInfo> parseSoapResponse(String xmlResponse) {
        try {
            log.debug("Parsing SOAP response con JAXB");

            Unmarshaller unmarshaller = responseContext.createUnmarshaller();

            String bodyContent = extractSoapBody(xmlResponse);
            if (bodyContent == null) {
                log.error("No se pudo extraer el cuerpo SOAP de la respuesta");
                return Mono.just(ProductInfo.builder().build());
            }

            UploadDocumentResponse response = (UploadDocumentResponse) unmarshaller.unmarshal(
                    new StringReader(bodyContent)
            );

            ProductInfo productInfo = mapToProductInfo(response);

            log.info("SOAP response parseada exitosamente para documento: {}", response.getDocumentId());
            return Mono.just(productInfo);

        } catch (JAXBException e) {
            log.error("Error parseando SOAP response con JAXB: {}", e.getMessage());
            return Mono.just(ProductInfo.builder().build());
        }
    }

    /**
     * Parsea el XML de respuesta SOAP específicamente para subida de documentos.
     *
     * @param xmlResponse XML de respuesta del servicio SOAP
     * @return Mono con el UploadDocumentResponse parseado
     */
    public Mono<UploadDocumentResponse> parseUploadDocumentResponse(String xmlResponse) {
        try {
            log.debug("Parsing UploadDocument SOAP response");

            Unmarshaller unmarshaller = responseContext.createUnmarshaller();

            String bodyContent = extractSoapBody(xmlResponse);
            if (bodyContent == null) {
                log.error("No se pudo extraer el cuerpo SOAP de la respuesta");
                return Mono.empty();
            }

            UploadDocumentResponse response = (UploadDocumentResponse) unmarshaller.unmarshal(
                    new StringReader(bodyContent)
            );

            log.info("UploadDocument response parseada exitosamente: {}", response.getDocumentId());
            return Mono.just(response);

        } catch (JAXBException e) {
            log.error("Error parseando UploadDocument SOAP response: {}", e.getMessage());
            return Mono.empty();
        }
    }

    /**
     * Mapea UploadDocumentResponse a ProductInfo del dominio (para compatibilidad).
     */
    private ProductInfo mapToProductInfo(UploadDocumentResponse response) {
        return ProductInfo.builder()
                .productId(response.getEntityId())
                .name(response.getFileName())
                .description(response.getMessage())
                .status(response.getStatus())
                .sourceSystem(response.getSourceSystem())
                .build();
    }

    /**
     * Extrae el contenido dentro del Body del envelope SOAP.
     */
    private String extractSoapBody(String xml) {
        String[] patterns = {
            "(?s)<soap:Body>(.*)</soap:Body>",
            "(?s)<Body>(.*)</Body>",
            "(?s)<SOAP-ENV:Body>(.*)</SOAP-ENV:Body>"
        };

        for (String pattern : patterns) {
            Pattern r = Pattern.compile(pattern);
            Matcher m = r.matcher(xml);
            if (m.find()) {
                return m.group(1).trim();
            }
        }

        return xml;
    }
}
