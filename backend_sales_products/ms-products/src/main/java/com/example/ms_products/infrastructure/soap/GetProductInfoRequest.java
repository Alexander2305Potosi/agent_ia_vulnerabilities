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
 * Clase JAXB que representa el request SOAP para enviar información de un archivo.
 * Incluye metadatos del archivo (nombre, tamaño, extensión) y su contenido binario.
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@XmlRootElement(name = "GetProductInfoRequest", namespace = "http://example.com/products")
@XmlAccessorType(XmlAccessType.FIELD)
public class GetProductInfoRequest {

    @XmlElement(name = "ProductId", namespace = "http://example.com/products")
    private String productId;

    /**
     * Nombre del archivo incluyendo la extensión (ej: "documento.pdf")
     */
    @XmlElement(name = "FileName", namespace = "http://example.com/products")
    private String fileName;

    /**
     * Tamaño del archivo en bytes
     */
    @XmlElement(name = "FileSize", namespace = "http://example.com/products")
    private Long fileSize;

    /**
     * Extensión del archivo sin el punto (ej: "pdf", "jpg", "xml")
     */
    @XmlElement(name = "FileExtension", namespace = "http://example.com/products")
    private String fileExtension;

    /**
     * Contenido del archivo como arreglo de bytes (codificado en Base64 para SOAP)
     */
    @XmlElement(name = "Content", namespace = "http://example.com/products")
    private byte[] content;
}
