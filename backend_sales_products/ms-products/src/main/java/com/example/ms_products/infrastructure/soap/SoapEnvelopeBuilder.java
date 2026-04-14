package com.example.ms_products.infrastructure.soap;

import jakarta.xml.bind.JAXBContext;
import jakarta.xml.bind.JAXBException;
import jakarta.xml.bind.Marshaller;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.io.StringWriter;
import java.util.Base64;

/**
 * Utilidad para construir y parsear envelopes SOAP usando JAXB.
 * Reemplaza la construcción manual de XML con String.format().
 */
@Slf4j
@Component
public class SoapEnvelopeBuilder {

    private final JAXBContext requestContext;

    public SoapEnvelopeBuilder() throws JAXBException {
        // Inicializar el contexto JAXB para las clases de request
        this.requestContext = JAXBContext.newInstance(GetProductInfoRequest.class);
    }

    /**
     * Construye el envelope SOAP a partir de un objeto Java.
     *
     * @param productId ID del producto a consultar
     * @return String con el XML del envelope SOAP
     */
    public String buildSoapEnvelope(String productId) {
        // Crear request básico con solo productId (backwards compatible)
        GetProductInfoRequest request = GetProductInfoRequest.builder()
                .productId(productId)
                .build();

        return marshalRequest(request);
    }

    /**
     * Construye el envelope SOAP con información completa de un archivo.
     *
     * @param productId ID del producto
     * @param fileName nombre del archivo
     * @param fileSize tamaño del archivo en bytes
     * @param fileExtension extensión del archivo
     * @param content contenido del archivo como arreglo de bytes
     * @return String con el XML del envelope SOAP
     */
    public String buildSoapEnvelopeWithFile(
            String productId,
            String fileName,
            Long fileSize,
            String fileExtension,
            byte[] content) {

        GetProductInfoRequest request = GetProductInfoRequest.builder()
                .productId(productId)
                .fileName(fileName)
                .fileSize(fileSize)
                .fileExtension(fileExtension)
                .content(content)
                .build();

        return marshalRequest(request);
    }

    /**
     * Serializa el objeto request a XML usando JAXB.
     */
    private String marshalRequest(GetProductInfoRequest request) {
        try {
            Marshaller marshaller = requestContext.createMarshaller();
            marshaller.setProperty(Marshaller.JAXB_FORMATTED_OUTPUT, true);
            marshaller.setProperty(Marshaller.JAXB_FRAGMENT, true);

            StringWriter writer = new StringWriter();

            // Envolver con el envelope SOAP
            writer.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
            writer.write("<soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\" ");
            writer.write("xmlns:prod=\"http://example.com/products\">\n");
            writer.write("    <soap:Header/>\n");
            writer.write("    <soap:Body>\n");
            writer.write("        ");

            marshaller.marshal(request, writer);

            writer.write("\n    </soap:Body>\n");
            writer.write("</soap:Envelope>");

            return writer.toString();

        } catch (JAXBException e) {
            log.error("Error construyendo SOAP envelope con JAXB: {}", e.getMessage());
            return buildFallbackEnvelope(request);
        }
    }

    /**
     * Método fallback que usa String.format (método anterior).
     */
    private String buildFallbackEnvelope(GetProductInfoRequest request) {
        // Codificar content a Base64 si existe
        String contentBase64 = request.getContent() != null
                ? Base64.getEncoder().encodeToString(request.getContent())
                : "";

        StringBuilder sb = new StringBuilder();
        sb.append("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
        sb.append("<soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\" ");
        sb.append("xmlns:prod=\"http://example.com/products\">\n");
        sb.append("    <soap:Header/>\n");
        sb.append("    <soap:Body>\n");
        sb.append("        <prod:GetProductInfoRequest>\n");

        if (request.getProductId() != null) {
            sb.append(String.format("            <prod:ProductId>%s</prod:ProductId>\n", escapeXml(request.getProductId())));
        }
        if (request.getFileName() != null) {
            sb.append(String.format("            <prod:FileName>%s</prod:FileName>\n", escapeXml(request.getFileName())));
        }
        if (request.getFileSize() != null) {
            sb.append(String.format("            <prod:FileSize>%d</prod:FileSize>\n", request.getFileSize()));
        }
        if (request.getFileExtension() != null) {
            sb.append(String.format("            <prod:FileExtension>%s</prod:FileExtension>\n", escapeXml(request.getFileExtension())));
        }
        if (!contentBase64.isEmpty()) {
            sb.append(String.format("            <prod:Content>%s</prod:Content>\n", contentBase64));
        }

        sb.append("        </prod:GetProductInfoRequest>\n");
        sb.append("    </soap:Body>\n");
        sb.append("</soap:Envelope>");

        return sb.toString();
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
