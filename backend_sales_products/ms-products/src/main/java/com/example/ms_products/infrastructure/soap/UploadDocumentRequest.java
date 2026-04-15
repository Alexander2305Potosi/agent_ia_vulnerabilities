package com.example.ms_products.infrastructure.soap;

import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlElement;
import jakarta.xml.bind.annotation.XmlRootElement;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Clase JAXB que representa la solicitud SOAP UploadDocumentRequest.
 * Incluye todos los campos para la subida de documentos al servicio SOAP.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@XmlRootElement(name = "UploadDocumentRequest", namespace = "http://example.com/products")
@XmlAccessorType(XmlAccessType.FIELD)
public class UploadDocumentRequest {

    // Identificación de la entidad
    @XmlElement(name = "entityId", namespace = "http://example.com/products")
    private String entityId;

    // Operación a realizar
    @XmlElement(name = "operation", namespace = "http://example.com/products")
    private String operation;

    // Identificador de la solicitud (para trazabilidad)
    @XmlElement(name = "requestId", namespace = "http://example.com/products")
    private String requestId;

    // Timestamp de la solicitud
    @XmlElement(name = "timestamp", namespace = "http://example.com/products")
    private String timestamp;

    // Campos para envío de archivos
    @XmlElement(name = "fileName", namespace = "http://example.com/products")
    private String fileName;

    @XmlElement(name = "fileSize", namespace = "http://example.com/products")
    private Long fileSize;

    @XmlElement(name = "fileExtension", namespace = "http://example.com/products")
    private String fileExtension;

    @XmlElement(name = "content", namespace = "http://example.com/products")
    private byte[] content;

    // Campos opcionales adicionales
    @XmlElement(name = "mimeType", namespace = "http://example.com/products")
    private String mimeType;

    @XmlElement(name = "description", namespace = "http://example.com/products")
    private String description;

    @XmlElement(name = "checksum", namespace = "http://example.com/products")
    private String checksum;

    // Metadatos del request
    @XmlElement(name = "sourceSystem", namespace = "http://example.com/products")
    private String sourceSystem;

    @XmlElement(name = "userId", namespace = "http://example.com/products")
    private String userId;

    @XmlElement(name = "sessionId", namespace = "http://example.com/products")
    private String sessionId;
}
