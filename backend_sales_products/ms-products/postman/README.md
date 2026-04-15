# MS-Documents Postman Collection

Colección de Postman para probar la API REST de documentos y simular el servicio SOAP externo.

## 📁 Archivos

- `ms-documents-soap-mock-collection.json` - Colección completa con mocks del servicio SOAP

## 🚀 Cómo Importar

1. Abrir Postman
2. Click en **File** > **Import**
3. Seleccionar el archivo `ms-documents-soap-mock-collection.json`
4. La colección se importará con todas las requests y mocks configurados

## 📋 Endpoints Incluidos

### API REST de ms-documents

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/v1/documents/health` | GET | Health check del servicio |
| `/api/v1/documents/info` | GET | Información del servicio |
| `/api/v1/documents/upload` | POST | Subir documento al servicio SOAP |

### Mock SOAP Service

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `http://localhost:8081/ws/document` | POST | Mock del servicio SOAP externo |

## 🎯 Casos de Prueba Incluidos

### 1. Document Upload Success
Subida exitosa de documento PDF con metadatos completos:
- Entidad asociada: PROD-001
- Documento: documento-especificaciones.pdf (1MB)
- Respuesta con documentId, fileUrl, processingTimeMs

### 2. Document Upload - Invalid Base64
Error al enviar contenido base64 malformado:
- HTTP 400 Bad Request
- Mensaje descriptivo del error de decodificación

### 3. Document Upload - Circuit Breaker Open
Simula servicio SOAP no disponible:
- HTTP 503 Service Unavailable
- Estado: CIRCUIT_BREAKER_OPEN

### 4. Document Upload - Rate Limit
Simula límite de peticiones excedido:
- HTTP 429 Too Many Requests
- Header Retry-After

## 🔧 Variables de Entorno

| Variable | Valor Default | Descripción |
|----------|---------------|-------------|
| `base_url` | `http://localhost:8080` | URL base de ms-documents |
| `entity_id` | `PROD-001` | ID de la entidad asociada |
| `soap_service_url` | `http://localhost:8081/ws/document` | URL del servicio SOAP |

## 📤 Endpoint de Subida de Documentos

### POST `/api/v1/documents/upload`

Sube información de un documento al servicio SOAP externo.

#### Request Body

```json
{
  "entityId": "PROD-001",
  "fileName": "documento-especificaciones.pdf",
  "fileSize": 1048576,
  "fileExtension": "pdf",
  "fileContentBase64": "JVBERi0xLjQKJeLjz9MK...",
  "mimeType": "application/pdf",
  "description": "Especificaciones técnicas del documento",
  "checksum": "d41d8cd98f00b204e9800998ecf8427e",
  "isPublic": false,
  "fileCategory": "SPECIFICATION"
}
```

#### Campos Obligatorios

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `entityId` | String | ID de la entidad asociada (producto, cliente, etc.) |
| `fileName` | String | Nombre del archivo con extensión |
| `fileSize` | Long | Tamaño en bytes |
| `fileExtension` | String | Extensión sin punto (ej: "pdf") |
| `fileContentBase64` | String | Contenido codificado en base64 |

#### Campos Opcionales

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `mimeType` | String | Tipo MIME del archivo |
| `description` | String | Descripción del documento |
| `checksum` | String | MD5 para validación de integridad |
| `isPublic` | Boolean | Indica si es público |
| `fileCategory` | String | Categoría (SPECIFICATION, IMAGE, etc.) |

#### Response 200 OK

```json
{
  "success": true,
  "message": "Documento subido exitosamente",
  "documentId": "DOC-2026-001",
  "entityId": "PROD-001",
  "fileName": "documento-especificaciones.pdf",
  "fileSize": 1048576,
  "fileUrl": "https://storage.example.com/docs/DOC-2026-001.pdf",
  "status": "COMPLETED",
  "responseCode": "200",
  "processedAt": "2026-04-15T10:30:00Z",
  "processingTimeMs": 245,
  "requestId": "req-550e8400-e29b-41d4-a716-446655440000",
  "validatedChecksum": "d41d8cd98f00b204e9800998ecf8427e"
}
```

## 🧪 Flujo de Prueba Recomendado

1. **Health Check** - Verificar servicio activo
2. **Service Info** - Confirmar versión
3. **Upload Document (Success)** - Subir documento exitosamente
4. **Upload Document (Invalid Base64)** - Probar validación
5. **Upload Document (Rate Limit)** - Verificar rate limiting
6. **Upload Document (Circuit Breaker)** - Verificar resiliencia

## 📈 Modelo de Datos

### FileUploadRequest (API)
- Campos obligatorios: entityId, fileName, fileSize, fileExtension, fileContentBase64
- Campos opcionales: mimeType, description, checksum, isPublic, fileCategory
- Validaciones: entityId alfanumérico, fileExtension sin punto, base64 válido

### FileUploadResponseDto (API)
- Información del resultado: success, message, documentId
- Identificación: entityId, fileName, fileSize
- Ubicación: fileUrl, status, responseCode
- Metadatos: processedAt, processingTimeMs, requestId
- Validación: validatedChecksum, validationErrors

## 🔌 Integración con Servicio SOAP Real

Para probar con el servicio SOAP real:

1. Configurar en `application.yml`:
```yaml
soap:
  service:
    url: http://servicio-soap-real:8081/ws/document
    timeout: 10000
```

2. Cambiar variable `soap_service_url` en Postman

3. Desactivar el mock y usar el servicio real

## 📝 Cambios Recientes (v2.0.0)

- **Contexto cambiado**: De `/api/v1/products` a `/api/v1/documents`
- **Endpoint renombrado**: Upload ahora es específico para documentos
- **Campos renombrados**: `productId` -> `entityId`, `fileId` -> `documentId`
- **Nuevo controller**: UploadFileController (antes ProductController)
- **DTOs actualizados**: Nombres y descripciones genéricos para documentos

---

*Documentación actualizada el 2026-04-15*  
*Versión de la API: 2.0.0*
