# Mock SOAP Service para ms-products

Este directorio contiene un proyecto de **SoapUI** para mockear el servicio SOAP externo que consume `ms-products`.

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `ProductServiceMock-soapui-project.xml` | Proyecto SoapUI con el mock service |
| `soap-ui-mock-project.xml` | Versión alternativa con casos de prueba |

## Características del Mock

El mock service simula el servicio SOAP externo con las siguientes respuestas:

### Endpoints

- **URL**: `http://localhost:8081/ws/product`
- **SOAP Action**: `http://example.com/products/UploadDocument`

### Respuestas Disponibles

| Nombre | HTTP Status | Descripción |
|--------|-------------|-------------|
| **Success** (default) | 200 | Upload exitoso con documentId |
| **QuerySuccess** | 200 | Respuesta para operación QUERY |
| **ServerError** | 500 | Error interno del servidor |
| **ValidationError** | 400 | Error de validación de campos |
| **Timeout** | 504 | Simula timeout (>10 segundos) |

## Uso

### Opción 1: SoapUI (Recomendado)

1. **Instalar SoapUI**:
   - Descargar desde: https://www.soapui.org/downloads/soapui/

2. **Importar el proyecto**:
   ```
   File → Import Project → ProductServiceMock-soapui-project.xml
   ```

3. **Iniciar el Mock Service**:
   - Doble clic en `ProductServiceMock`
   - Click en el botón verde "Start" (▶)
   - Verificar que el puerto 8081 está disponible

4. **Verificar funcionamiento**:
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

### Opción 2: Línea de Comandos (Maven/Gradle)

Agregar al `application-test.properties`:
```properties
soap.service.url=http://localhost:8081/ws/product
```

### Opción 3: Docker (MockServer o similar)

Si prefieres no usar SoapUI, puedes usar MockServer:

```yaml
# docker-compose.yml
version: '3.8'
services:
  soap-mock:
    image: mockserver/mockserver:latest
    ports:
      - "8081:1080"
    environment:
      MOCKSERVER_INITIALIZATION_JSON_PATH: /config/expectations.json
    volumes:
      - ./mock-config:/config
```

## Configuración de ms-products

El `SoapClientAdapter` está configurado para usar:

```yaml
soap:
  service:
    url: ${SOAP_SERVICE_URL:http://localhost:8081/ws/product}
    timeout: 10000
```

## Cambiar entre Respuestas en SoapUI

Para seleccionar una respuesta diferente:

1. Abrir el proyecto en SoapUI
2. Doble clic en `ProductServiceMock`
3. Doble clic en la operación `UploadDocument`
4. Seleccionar la respuesta deseada del dropdown
5. Cambiar el dispatch method a "SEQUENCE" o "SCRIPT" para automatizar

## Troubleshooting

### Error: Puerto 8081 en uso

Cambiar el puerto en el mock service:
- Doble clic en `ProductServiceMock`
- Cambiar el puerto (ej: 8082)
- Actualizar `soap.service.url` en la configuración

### Error: Connection Refused

Verificar que:
1. El mock service está iniciado (botón verde)
2. El puerto no está bloqueado por firewall
3. La URL coincide con la configuración de `ms-products`

### Timeout en ms-products

El mock tiene una respuesta con delay de 11 segundos para probar el manejo de timeouts en el cliente.

## Estructura del Proyecto

```
mock/
├── ProductServiceMock-soapui-project.xml    # Proyecto SoapUI principal
├── soap-ui-mock-project.xml                 # Versión con test suites
├── README.md                                # Este archivo
└── .gitkeep
```

## Referencias

- [SoapUI Documentation](https://www.soapui.org/docs/)
- [Mock Service Tutorial](https://www.soapui.org/docs/soap-mocking/)
- [ms-products SoapClientAdapter](../../main/java/com/example/ms_products/infrastructure/adapter/SoapClientAdapter.java)
