package com.example.ms_products.infrastructure.soap;

import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlElement;
import jakarta.xml.bind.annotation.XmlRootElement;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

/**
 * Clase JAXB que representa la respuesta SOAP UploadDocumentResponse.
 * Contiene el resultado de la subida de documento al servicio SOAP.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@XmlRootElement(name = "UploadDocumentResponse", namespace = "http://example.com/products")
@XmlAccessorType(XmlAccessType.FIELD)
public class UploadDocumentResponse {

    // Estado de la operación
    @XmlElement(name = "success", namespace = "http://example.com/products")
    private Boolean success;

    @XmlElement(name = "message", namespace = "http://example.com/products")
    private String message;

    // Identificadores del documento
    @XmlElement(name = "documentId", namespace = "http://example.com/products")
    private String documentId;

    @XmlElement(name = "entityId", namespace = "http://example.com/products")
    private String entityId;

    // Información del archivo
    @XmlElement(name = "fileName", namespace = "http://example.com/products")
    private String fileName;

    @XmlElement(name = "fileSize", namespace = "http://example.com/products")
    private Long fileSize;

    @XmlElement(name = "fileUrl", namespace = "http://example.com/products")
    private String fileUrl;

    // Estado del procesamiento
    @XmlElement(name = "status", namespace = "http://example.com/products")
    private String status;

    @XmlElement(name = "responseCode", namespace = "http://example.com/products")
    private String responseCode;

    @XmlElement(name = "processedAt", namespace = "http://example.com/products")
    private String processedAt;

    @XmlElement(name = "processingTimeMs", namespace = "http://example.com/products")
    private Long processingTimeMs;

    @XmlElement(name = "requestId", namespace = "http://example.com/products")
    private String requestId;

    // Validación
    @XmlElement(name = "validatedChecksum", namespace = "http://example.com/products")
    private String validatedChecksum;

    // Metadatos
    @XmlElement(name = "sourceSystem", namespace = "http://example.com/products")
    private String sourceSystem;

    // Error
    @XmlElement(name = "errorCode", namespace = "http://example.com/products")
    private String errorCode;

    @XmlElement(name = "errorMessage", namespace = "http://example.com/products")
    private String errorMessage;
}
