# Mock SOAP Service para ms-products

Este directorio contiene un proyecto de **SoapUI** para mockear el servicio SOAP externo que consume `ms-products`.

## Archivo

| Archivo | Descripción |
|---------|-------------|
| `ProductServiceMock-simple.xml` | Proyecto SoapUI simplificado - **USAR ESTE** |

## Características del Mock

El mock service simula el servicio SOAP externo con las siguientes respuestas:

| Nombre | HTTP Status | Descripción |
|--------|-------------|-------------|
| **Success** (default) | 200 | Upload exitoso con documentId |
| **ServerError** | 500 | Error interno del servidor |
| **Timeout** | 504 | Simula timeout (>10 segundos) |

## Instrucciones de Uso

### 1. Instalar SoapUI
Descargar desde: https://www.soapui.org/downloads/soapui/

### 2. Importar el Proyecto
```
File → Import Project → ProductServiceMock-simple.xml
```

### 3. Iniciar el Mock Service
1. En el panel izquierdo, expandir **"ProductServiceMockSimple"**
2. Doble clic en **"ProductMockService"**
3. Click en el botón verde **Start (▶)** arriba a la izquierda
4. Verificar mensaje: **"Running on port [8081]"**

### 4. Probar el Mock
Desde terminal:
```bash
curl -X POST http://localhost:8081/ws/product \
  -H "Content-Type: text/xml; charset=UTF-8" \
  -H "SOAPAction: http://example.com/products/UploadDocument" \
  -d '<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:doc="http://example.com/products">
   <soap:Header/>
   <soap:Body>
      <doc:UploadDocumentRequest>
         <doc:entityId>PROD-TEST-001</doc:entityId>
         <doc:operation>UPLOAD_DOCUMENT</doc:operation>
         <doc:requestId>req-test-001</doc:requestId>
         <doc:timestamp>2026-04-16T10:30:00Z</doc:timestamp>
         <doc:sourceSystem>ms-products</doc:sourceSystem>
      </doc:UploadDocumentRequest>
   </soap:Body>
</soap:Envelope>'
```

### 5. Cambiar entre Respuestas
Para probar diferentes escenarios:
1. Doble clic en la operación **"UploadDocument"**
2. En el dropdown superior cambiar entre:
   - **Success** → Respuesta exitosa (default)
   - **ServerError** → Error 500
   - **Timeout** → Delay de 11 segundos (prueba timeout del cliente)

## Configuración de ms-products

En `application.properties` o variables de entorno:
```properties
soap.service.url=http://localhost:8081/ws/product
```

## Troubleshooting

### Error: Puerto 8081 en uso
Cambiar el puerto en el mock:
- Doble clic en `ProductMockService`
- Cambiar el campo **Port** (ej: 8082)
- Actualizar `soap.service.url` en ms-products

### Error: Connection Refused
Verificar que:
1. El mock service está iniciado (botón verde presionado)
2. El puerto no está bloqueado por firewall
3. La URL coincide con la configuración de ms-products

## Endpoint Mock

- **URL**: `http://localhost:8081/ws/product`
- **SOAP Action**: `http://example.com/products/UploadDocument`
- **Puerto**: `8081` (configurable)

## Respuesta Exitosa de Ejemplo

```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:doc="http://example.com/products">
   <soap:Header/>
   <soap:Body>
      <doc:UploadDocumentResponse>
         <doc:success>true</doc:success>
         <doc:message>Document uploaded successfully</doc:message>
         <doc:documentId>DOC-550e8400-e29b-41d4-a716-446655440000</doc:documentId>
         <doc:entityId>PROD-12345</doc:entityId>
         <doc:fileName>documento.pdf</doc:fileName>
         <doc:fileSize>1024</doc:fileSize>
         <doc:fileUrl>http://localhost:8081/files/DOC-550e8400-e29b-41d4-a716-446655440000</doc:fileUrl>
         <doc:status>PROCESSED</doc:status>
         <doc:responseCode>200</doc:responseCode>
         <doc:processedAt>2026-04-16T10:30:01Z</doc:processedAt>
         <doc:processingTimeMs>150</doc:processingTimeMs>
         <doc:requestId>req-12345-abcde</doc:requestId>
         <doc:sourceSystem>ms-products-mock</doc:sourceSystem>
      </doc:UploadDocumentResponse>
   </soap:Body>
</soap:Envelope>
```

## Referencias

- [SoapUI Documentation](https://www.soapui.org/docs/)
- [Mock Service Tutorial](https://www.soapui.org/docs/soap-mocking/)
- [ms-products SoapClientAdapter](../../main/java/com/example/ms_products/infrastructure/adapter/SoapClientAdapter.java)
