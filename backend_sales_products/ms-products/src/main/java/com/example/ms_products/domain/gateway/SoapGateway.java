package com.example.ms_products.domain.gateway;

import com.example.ms_products.domain.model.SoapProductRequest;
import com.example.ms_products.domain.model.SoapProductResponse;
import reactor.core.publisher.Mono;

public interface SoapGateway {
    Mono<SoapProductResponse> callSoapService(SoapProductRequest request);

    /**
     * Envía información de un documento/archivo al servicio SOAP.
     *
     * @param entityId ID de la entidad asociada (producto, cliente, etc.)
     * @param fileName nombre del archivo
     * @param fileSize tamaño del archivo en bytes
     * @param fileExtension extensión del archivo
     * @param content contenido del archivo como arreglo de bytes
     * @return Mono con la respuesta SOAP
     */
    Mono<SoapProductResponse> callSoapServiceWithFile(
            String entityId,
            String fileName,
            Long fileSize,
            String fileExtension,
            byte[] content);
}
