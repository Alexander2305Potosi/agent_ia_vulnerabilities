package com.example.ms_products.infrastructure.soap;

import com.example.ms_products.domain.model.SoapProductRequest;
import jakarta.xml.bind.JAXBContext;
import jakarta.xml.bind.JAXBException;
import jakarta.xml.bind.Marshaller;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.io.StringWriter;
import java.time.Instant;
import java.util.UUID;

/**
 * Utilidad para construir envelopes SOAP usando JAXB para subida de documentos.
 */
@Slf4j
@Component
public class SoapEnvelopeBuilder {

    private final JAXBContext requestContext;

    public SoapEnvelopeBuilder() throws JAXBException {
        this.requestContext = JAXBContext.newInstance(UploadDocumentRequest.class);
    }

    /**
     * Construye el envelope SOAP para subida de documento.
     *
     * @param entityId ID de la entidad a consultar
     * @return String con el XML del envelope SOAP
     */
    public String buildSoapEnvelope(String entityId) {
        UploadDocumentRequest request = UploadDocumentRequest.builder()
                .entityId(entityId)
                .operation("QUERY")
                .requestId(UUID.randomUUID().toString())
                .timestamp(Instant.now().toString())
                .sourceSystem("ms-products")
                .build();

        return marshalRequest(request);
    }

    /**
     * Construye el envelope SOAP completo a partir de SoapProductRequest del dominio.
     *
     * @param request Request del dominio con todos los parámetros
     * @return String con el XML del envelope SOAP
     */
    public String buildSoapEnvelope(SoapProductRequest request) {
        UploadDocumentRequest jaxbRequest = UploadDocumentRequest.builder()
                .entityId(request.getProductId())
                .operation(request.getOperation())
                .requestId(request.getRequestId())
                .timestamp(request.getTimestamp())
                .sourceSystem(request.getSourceSystem())
                .userId(request.getUserId())
                .sessionId(request.getSessionId())
                .build();

        return marshalRequest(jaxbRequest);
    }

    /**
     * Construye el envelope SOAP con información de archivo adjunto.
     *
     * @param entityId ID de la entidad
     * @param fileName nombre del archivo
     * @param fileSize tamaño del archivo en bytes
     * @param fileExtension extensión del archivo
     * @param content contenido del archivo como arreglo de bytes
     * @return String con el XML del envelope SOAP
     */
    public String buildSoapEnvelopeWithFile(
            String entityId,
            String fileName,
            Long fileSize,
            String fileExtension,
            byte[] content) {

        UploadDocumentRequest request = UploadDocumentRequest.builder()
                .entityId(entityId)
                .operation("UPLOAD_DOCUMENT")
                .requestId(UUID.randomUUID().toString())
                .timestamp(Instant.now().toString())
                .fileName(fileName)
                .fileSize(fileSize)
                .fileExtension(fileExtension)
                .content(content)
                .sourceSystem("ms-products")
                .build();

        return marshalRequest(request);
    }

    /**
     * Serializa el objeto request a XML usando JAXB.
     */
    private String marshalRequest(UploadDocumentRequest request) {
        try {
            Marshaller marshaller = requestContext.createMarshaller();
            marshaller.setProperty(Marshaller.JAXB_FORMATTED_OUTPUT, true);
            marshaller.setProperty(Marshaller.JAXB_FRAGMENT, true);

            StringWriter writer = new StringWriter();

            // Envolver con el envelope SOAP
            writer.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
            writer.write("<soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\" ");
            writer.write("xmlns:doc=\"http://example.com/products\">\n");
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
     * Método fallback que usa String.format para construcción manual.
     */
    private String buildFallbackEnvelope(UploadDocumentRequest request) {
        StringBuilder sb = new StringBuilder();
        sb.append("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
        sb.append("<soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\" ");
        sb.append("xmlns:doc=\"http://example.com/products\">\n");
        sb.append("    <soap:Header/>\n");
        sb.append("    <soap:Body>\n");
        sb.append("        <doc:UploadDocumentRequest>\n");

        // Campos obligatorios
        if (request.getEntityId() != null) {
            sb.append(String.format("            <doc:entityId>%s</doc:entityId>\n", escapeXml(request.getEntityId())));
        }
        if (request.getOperation() != null) {
            sb.append(String.format("            <doc:operation>%s</doc:operation>\n", escapeXml(request.getOperation())));
        }
        if (request.getRequestId() != null) {
            sb.append(String.format("            <doc:requestId>%s</doc:requestId>\n", escapeXml(request.getRequestId())));
        }
        if (request.getTimestamp() != null) {
            sb.append(String.format("            <doc:timestamp>%s</doc:timestamp>\n", escapeXml(request.getTimestamp())));
        }

        // Campos de archivo
        if (request.getFileName() != null) {
            sb.append(String.format("            <doc:fileName>%s</doc:fileName>\n", escapeXml(request.getFileName())));
        }
        if (request.getFileSize() != null) {
            sb.append(String.format("            <doc:fileSize>%d</doc:fileSize>\n", request.getFileSize()));
        }
        if (request.getFileExtension() != null) {
            sb.append(String.format("            <doc:fileExtension>%s</doc:fileExtension>\n", escapeXml(request.getFileExtension())));
        }
        if (request.getContent() != null) {
            String contentBase64 = java.util.Base64.getEncoder().encodeToString(request.getContent());
            sb.append(String.format("            <doc:content>%s</doc:content>\n", contentBase64));
        }

        // Campos opcionales
        if (request.getMimeType() != null) {
            sb.append(String.format("            <doc:mimeType>%s</doc:mimeType>\n", escapeXml(request.getMimeType())));
        }
        if (request.getDescription() != null) {
            sb.append(String.format("            <doc:description>%s</doc:description>\n", escapeXml(request.getDescription())));
        }
        if (request.getChecksum() != null) {
            sb.append(String.format("            <doc:checksum>%s</doc:checksum>\n", escapeXml(request.getChecksum())));
        }

        // Metadatos
        if (request.getSourceSystem() != null) {
            sb.append(String.format("            <doc:sourceSystem>%s</doc:sourceSystem>\n", escapeXml(request.getSourceSystem())));
        }
        if (request.getUserId() != null) {
            sb.append(String.format("            <doc:userId>%s</doc:userId>\n", escapeXml(request.getUserId())));
        }
        if (request.getSessionId() != null) {
            sb.append(String.format("            <doc:sessionId>%s</doc:sessionId>\n", escapeXml(request.getSessionId())));
        }

        sb.append("        </doc:UploadDocumentRequest>\n");
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
