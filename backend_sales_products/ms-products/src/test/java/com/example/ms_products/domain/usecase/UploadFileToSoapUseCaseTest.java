package com.example.ms_products.domain.usecase;

import com.example.ms_products.domain.gateway.SoapGateway;
import com.example.ms_products.domain.model.SoapProductResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.util.Base64;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * Tests para UploadFileToSoapUseCase - Caso de uso de subida de documentos.
 */
@ExtendWith(MockitoExtension.class)
class UploadFileToSoapUseCaseTest {

    @Mock
    private SoapGateway soapGateway;

    private UploadFileToSoapUseCase useCase;

    @BeforeEach
    void setUp() {
        useCase = new UploadFileToSoapUseCase(soapGateway);
    }

    @Test
    void execute_shouldReturnSuccess_whenFileUploadIsSuccessful() {
        // Given
        String entityId = "PROD-001";
        String fileName = "documento-prueba.pdf";
        Long fileSize = 1024L;
        String fileExtension = "pdf";
        String fileContentBase64 = Base64.getEncoder().encodeToString("contenido".getBytes());

        SoapProductResponse soapResponse = SoapProductResponse.builder()
                .success(true)
                .message("Document uploaded successfully")
                .fileId("DOC-2026-001")
                .fileUrl("https://storage.example.com/docs/DOC-2026-001.pdf")
                .requestId("req-001")
                .status("UPLOADED")
                .build();

        when(soapGateway.callSoapServiceWithFile(anyString(), anyString(), anyLong(), anyString(), any()))
                .thenReturn(Mono.just(soapResponse));

        // When & Then
        StepVerifier.create(useCase.execute(entityId, fileName, fileSize, fileExtension, fileContentBase64))
                .assertNext(result -> {
                    assert result.getSuccess();
                    assert result.getDocumentId().equals("DOC-2026-001");
                    assert result.getEntityId().equals(entityId);
                    assert result.getFileName().equals(fileName);
                    assert result.getStatus().equals("COMPLETED");
                })
                .verifyComplete();

        verify(soapGateway).callSoapServiceWithFile(eq(entityId), eq(fileName), eq(fileSize), eq(fileExtension), any());
    }

    @Test
    void execute_shouldReturnError_whenSoapServiceReturnsFailure() {
        // Given
        String entityId = "PROD-002";
        String fileName = "documento-falla.pdf";
        Long fileSize = 512L;
        String fileExtension = "pdf";
        String fileContentBase64 = Base64.getEncoder().encodeToString("contenido".getBytes());

        SoapProductResponse soapResponse = SoapProductResponse.builder()
                .success(false)
                .message("Invalid file format")
                .errorCode("INVALID_FORMAT")
                .build();

        when(soapGateway.callSoapServiceWithFile(anyString(), anyString(), anyLong(), anyString(), any()))
                .thenReturn(Mono.just(soapResponse));

        // When & Then
        StepVerifier.create(useCase.execute(entityId, fileName, fileSize, fileExtension, fileContentBase64))
                .assertNext(result -> {
                    assert !result.getSuccess();
                    assert result.getStatus().equals("FAILED");
                    assert result.getResponseCode().equals("INVALID_FORMAT");
                    assert result.getValidationErrors().equals("Invalid file format");
                })
                .verifyComplete();
    }

    @Test
    void execute_shouldReturnError_whenBase64IsInvalid() {
        // Given
        String entityId = "PROD-003";
        String fileName = "invalid.pdf";
        Long fileSize = 100L;
        String fileExtension = "pdf";
        String invalidBase64 = "NOT-VALID-BASE64!!!";

        // When & Then
        StepVerifier.create(useCase.execute(entityId, fileName, fileSize, fileExtension, invalidBase64))
                .expectError(UploadFileToSoapUseCase.InvalidFileException.class)
                .verify();

        verify(soapGateway, never()).callSoapServiceWithFile(any(), any(), any(), any(), any());
    }

    @Test
    void execute_shouldReturnError_whenSoapServiceThrowsException() {
        // Given
        String entityId = "PROD-004";
        String fileName = "documento-error.pdf";
        Long fileSize = 2048L;
        String fileExtension = "pdf";
        String fileContentBase64 = Base64.getEncoder().encodeToString("contenido".getBytes());

        when(soapGateway.callSoapServiceWithFile(anyString(), anyString(), anyLong(), anyString(), any()))
                .thenReturn(Mono.error(new RuntimeException("SOAP connection error")));

        // When & Then
        StepVerifier.create(useCase.execute(entityId, fileName, fileSize, fileExtension, fileContentBase64))
                .expectError(RuntimeException.class)
                .verify();
    }

    @Test
    void execute_shouldProcessLargeFilesSuccessfully() {
        // Given
        String entityId = "PROD-005";
        String fileName = "archivo-grande.pdf";
        Long fileSize = 10485760L; // 10MB
        String fileExtension = "pdf";
        String fileContentBase64 = Base64.getEncoder().encodeToString(new byte[1024 * 1024]); // 1MB content

        SoapProductResponse soapResponse = SoapProductResponse.builder()
                .success(true)
                .message("Large file uploaded")
                .fileId("DOC-2026-005")
                .fileUrl("https://storage.example.com/docs/DOC-2026-005.pdf")
                .build();

        when(soapGateway.callSoapServiceWithFile(anyString(), anyString(), anyLong(), anyString(), any()))
                .thenReturn(Mono.just(soapResponse));

        // When & Then
        StepVerifier.create(useCase.execute(entityId, fileName, fileSize, fileExtension, fileContentBase64))
                .assertNext(result -> {
                    assert result.getSuccess();
                    assert result.getDocumentId().equals("DOC-2026-005");
                })
                .verifyComplete();
    }

    @Test
    void execute_shouldIncludeProcessingTimeInResult() {
        // Given
        String entityId = "PROD-006";
        String fileName = "test.pdf";
        Long fileSize = 1024L;
        String fileExtension = "pdf";
        String fileContentBase64 = Base64.getEncoder().encodeToString("test".getBytes());

        SoapProductResponse soapResponse = SoapProductResponse.builder()
                .success(true)
                .message("Success")
                .fileId("DOC-006")
                .build();

        when(soapGateway.callSoapServiceWithFile(anyString(), anyString(), anyLong(), anyString(), any()))
                .thenReturn(Mono.just(soapResponse));

        // When & Then
        StepVerifier.create(useCase.execute(entityId, fileName, fileSize, fileExtension, fileContentBase64))
                .assertNext(result -> {
                    assert result.getSuccess();
                    assert result.getProcessingTimeMs() != null;
                    assert result.getProcessingTimeMs() >= 0;
                    assert result.getProcessedAt() != null;
                })
                .verifyComplete();
    }
}
