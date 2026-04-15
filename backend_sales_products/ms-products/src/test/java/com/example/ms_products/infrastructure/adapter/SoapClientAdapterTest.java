package com.example.ms_products.infrastructure.adapter;

import com.example.ms_products.domain.model.SoapProductResponse;
import com.example.ms_products.infrastructure.soap.SoapEnvelopeBuilder;
import com.example.ms_products.infrastructure.soap.SoapResponseParser;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.test.StepVerifier;

import java.io.IOException;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests para SoapClientAdapter enfocados en subida de archivos al servicio SOAP.
 */
class SoapClientAdapterTest {

    private MockWebServer mockWebServer;
    private SoapClientAdapter soapClientAdapter;
    private SoapEnvelopeBuilder envelopeBuilder;
    private SoapResponseParser responseParser;

    @BeforeEach
    void setUp() throws Exception {
        mockWebServer = new MockWebServer();
        mockWebServer.start();

        WebClient webClient = WebClient.builder()
                .baseUrl(mockWebServer.url("/").toString())
                .build();

        envelopeBuilder = new SoapEnvelopeBuilder();
        responseParser = new SoapResponseParser();

        soapClientAdapter = new SoapClientAdapter(webClient, envelopeBuilder, responseParser);

        String mockUrl = mockWebServer.url("/ws/product").toString();
        ReflectionTestUtils.setField(soapClientAdapter, "soapServiceUrl", mockUrl);
        ReflectionTestUtils.setField(soapClientAdapter, "soapTimeout", 30000);
    }

    @AfterEach
    void tearDown() throws IOException {
        mockWebServer.shutdown();
    }

    @Test
    void callSoapServiceWithFile_shouldReturnSuccess_whenUploadIsSuccessful() throws InterruptedException {
        // Given
        String entityId = "PROD-001";
        String fileName = "documento-prueba.pdf";
        Long fileSize = 1024L;
        String fileExtension = "pdf";
        byte[] fileContent = "Contenido de prueba".getBytes(StandardCharsets.UTF_8);

        String soapResponse = """
            <?xml version="1.0" encoding="UTF-8"?>
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Body>
                    <UploadDocumentResponse xmlns="http://example.com/products">
                        <success>true</success>
                        <message>Document uploaded successfully</message>
                        <documentId>DOC-2026-001</documentId>
                        <entityId>PROD-001</entityId>
                        <fileName>documento-prueba.pdf</fileName>
                        <fileSize>1024</fileSize>
                        <fileUrl>https://storage.example.com/docs/DOC-2026-001.pdf</fileUrl>
                        <status>UPLOADED</status>
                        <requestId>req-test-001</requestId>
                    </UploadDocumentResponse>
                </soap:Body>
            </soap:Envelope>
            """;

        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "text/xml")
                .setBody(soapResponse));

        // When & Then
        StepVerifier.create(soapClientAdapter.callSoapServiceWithFile(
                        entityId, fileName, fileSize, fileExtension, fileContent))
                .assertNext(response -> {
                    assertTrue(response.getSuccess());
                    assertEquals("Document uploaded successfully", response.getMessage());
                    assertEquals("DOC-2026-001", response.getFileId());
                    assertEquals("https://storage.example.com/docs/DOC-2026-001.pdf", response.getFileUrl());
                })
                .verifyComplete();

        // Verify request
        RecordedRequest recordedRequest = mockWebServer.takeRequest();
        assertEquals("POST", recordedRequest.getMethod());
        assertTrue(recordedRequest.getHeader("Content-Type").contains("text/xml"));
        String requestBody = recordedRequest.getBody().readUtf8();
        assertTrue(requestBody.contains("UPLOAD_DOCUMENT"));
        assertTrue(requestBody.contains(entityId));
        assertTrue(requestBody.contains(fileName));
    }

    @Test
    void callSoapServiceWithFile_shouldReturnError_whenServerReturns500() {
        // Given
        String entityId = "PROD-001";
        String fileName = "documento-prueba.pdf";
        Long fileSize = 1024L;
        String fileExtension = "pdf";
        byte[] fileContent = "Contenido de prueba".getBytes(StandardCharsets.UTF_8);

        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(500)
                .setHeader("Content-Type", "text/xml")
                .setBody("Internal Server Error"));

        // When & Then
        StepVerifier.create(soapClientAdapter.callSoapServiceWithFile(
                        entityId, fileName, fileSize, fileExtension, fileContent))
                .expectError()
                .verify();
    }

    @Test
    void callSoapServiceWithFile_shouldHandleEmptyResponse_whenSoapBodyIsEmpty() {
        // Given
        String entityId = "PROD-002";
        String fileName = "documento-vacio.pdf";
        Long fileSize = 0L;
        String fileExtension = "pdf";
        byte[] fileContent = new byte[0];

        String soapResponse = """
            <?xml version="1.0" encoding="UTF-8"?>
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Body>
                    <UploadDocumentResponse xmlns="http://example.com/products"/>
                </soap:Body>
            </soap:Envelope>
            """;

        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "text/xml")
                .setBody(soapResponse));

        // When & Then - Empty response should complete without error
        StepVerifier.create(soapClientAdapter.callSoapServiceWithFile(
                        entityId, fileName, fileSize, fileExtension, fileContent))
                .expectNextCount(1)
                .verifyComplete();
    }

    @Test
    void callSoapServiceWithFile_shouldHandleLargeFiles() throws InterruptedException {
        // Given
        String entityId = "PROD-003";
        String fileName = "archivo-grande.pdf";
        Long fileSize = 10 * 1024 * 1024L;
        String fileExtension = "pdf";
        byte[] fileContent = new byte[1024];

        String soapResponse = """
            <?xml version="1.0" encoding="UTF-8"?>
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Body>
                    <UploadDocumentResponse xmlns="http://example.com/products">
                        <success>true</success>
                        <message>Large file uploaded</message>
                        <documentId>DOC-2026-003</documentId>
                        <entityId>PROD-003</entityId>
                        <fileName>archivo-grande.pdf</fileName>
                    </UploadDocumentResponse>
                </soap:Body>
            </soap:Envelope>
            """;

        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "text/xml")
                .setBody(soapResponse));

        // When & Then
        StepVerifier.create(soapClientAdapter.callSoapServiceWithFile(
                        entityId, fileName, fileSize, fileExtension, fileContent))
                .assertNext(response -> {
                    assertTrue(response.getSuccess());
                    assertEquals("Large file uploaded", response.getMessage());
                })
                .verifyComplete();

        RecordedRequest recordedRequest = mockWebServer.takeRequest();
        String requestBody = recordedRequest.getBody().readUtf8();
        assertTrue(requestBody.contains(fileName));
        assertTrue(requestBody.contains(String.valueOf(fileSize)));
    }

    @Test
    void callSoapServiceWithFile_shouldIncludeCorrectSoapHeaders() throws InterruptedException {
        // Given
        String entityId = "PROD-004";
        String fileName = "test-document.docx";
        Long fileSize = 2048L;
        String fileExtension = "docx";
        byte[] fileContent = "Document content".getBytes(StandardCharsets.UTF_8);

        String soapResponse = """
            <?xml version="1.0" encoding="UTF-8"?>
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
                <soap:Body>
                    <UploadDocumentResponse xmlns="http://example.com/products">
                        <success>true</success>
                        <message>Success</message>
                        <documentId>DOC-004</documentId>
                    </UploadDocumentResponse>
                </soap:Body>
            </soap:Envelope>
            """;

        mockWebServer.enqueue(new MockResponse()
                .setResponseCode(200)
                .setHeader("Content-Type", "text/xml")
                .setBody(soapResponse));

        // When
        StepVerifier.create(soapClientAdapter.callSoapServiceWithFile(
                        entityId, fileName, fileSize, fileExtension, fileContent))
                .expectNextMatches(response -> response.getSuccess())
                .verifyComplete();

        // Then - Verify SOAP headers
        RecordedRequest recordedRequest = mockWebServer.takeRequest();
        assertEquals("text/xml; charset=UTF-8", recordedRequest.getHeader("Content-Type"));
        assertEquals("http://example.com/products/UploadDocument", recordedRequest.getHeader("SOAPAction"));
    }
}
