package com.example.ms_products.infrastructure.soap;

import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlElement;
import jakarta.xml.bind.annotation.XmlRootElement;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Clase JAXB que representa la respuesta SOAP GetProductInfoResponse.
 * Permite deserializar automáticamente el XML de respuesta.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@XmlRootElement(name = "GetProductInfoResponse", namespace = "http://example.com/products")
@XmlAccessorType(XmlAccessType.FIELD)
public class GetProductInfoResponse {

    @XmlElement(name = "ProductId", namespace = "http://example.com/products")
    private String productId;

    @XmlElement(name = "Name", namespace = "http://example.com/products")
    private String name;

    @XmlElement(name = "Description", namespace = "http://example.com/products")
    private String description;

    @XmlElement(name = "Price", namespace = "http://example.com/products")
    private Double price;

    @XmlElement(name = "StockQuantity", namespace = "http://example.com/products")
    private Integer stockQuantity;

    @XmlElement(name = "Category", namespace = "http://example.com/products")
    private String category;

    @XmlElement(name = "Supplier", namespace = "http://example.com/products")
    private String supplier;
}
