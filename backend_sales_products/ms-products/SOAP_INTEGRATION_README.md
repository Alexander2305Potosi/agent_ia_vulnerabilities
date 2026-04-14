# Servicio REST-SOAP Integration (ms-products)

## Descripción

Este microservicio expone un endpoint REST que consume una API SOAP externa siguiendo los principios de **Clean Architecture**.

## Arquitectura

```
REST Controller (Entry Point)
       ↓
Use Case (Caso de Uso)
       ↓
Gateway (Puerto/Interface)
       ↓
Adapter (Implementación WebClient SOAP)
```

## Estructura de Paquetes

```
com.example.ms_products/
├── domain/
│   ├── model/
│   │   ├── ProductInfo.java           # Entidad de dominio
│   │   ├── SoapProductRequest.java    # Request SOAP
│   │   └── SoapProductResponse.java   # Response SOAP
│   ├── gateway/
│   │   └── SoapGateway.java           # Interface del puerto
│   └── usecase/
│       └── GetProductFromSoapUseCase.java  # Caso de uso
├── infrastructure/
│   ├── adapter/
│   │   └── SoapClientAdapter.java     # Implementación del adapter
│   ├── config/
│   │   └── WebClientConfig.java       # Configuración WebClient
│   ├── entrypoints/
│   │   ├── ProductController.java     # REST Controller
│   │   └── dto/
│   │       └── ProductResponseDto.java
│   └── mapper/
│       └── ProductMapper.java         # Mapper DTO-Domain
└── MainApplication.java
```

## Endpoints REST

### GET /api/v1/products/soap/{productId}

Consulta información de un producto consumiendo el servicio SOAP externo.

**Parámetros:**
- `productId` (path): ID del producto a consultar

**Respuesta Exitosa (200):**
```json
{
  "productId": "PROD-001",
  "name": "Laptop Dell XPS 15",
  "description": "Laptop de alta gama",
  "price": 1499.99,
  "stockQuantity": 50,
  "category": "ELECTRONICS",
  "supplier": "Dell Inc.",
  "source": "SOAP_EXTERNAL_API"
}
```

**Respuestas de Error:**
- `404 Not Found`: Producto no encontrado en el servicio SOAP
- `500 Internal Server Error`: Error interno del servidor

### GET /api/v1/products/health

Endpoint de health check.

**Respuesta (200):**
```
OK
```

## Configuración

### application.yml

```yaml
soap:
  service:
    url: http://localhost:8081/ws/product  # URL del servicio SOAP
    timeout: 30000                          # Timeout en milisegundos
```

## Dependencias SOAP

- `javax.xml.bind:jaxb-api` - API JAXB para binding XML
- `org.glassfish.jaxb:jaxb-runtime` - Implementación JAXB
- `jakarta.xml.soap:jakarta.xml.soap-api` - API SAAJ
- `com.sun.xml.messaging.saaj:saaj-impl` - Implementación SAAJ

## Ejemplo de Request SOAP

El servicio genera automáticamente el envelope SOAP:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:prod="http://example.com/products">
    <soap:Header/>
    <soap:Body>
        <prod:GetProductInfoRequest>
            <prod:ProductId>PROD-001</prod:ProductId>
        </prod:GetProductInfoRequest>
    </soap:Body>
</soap:Envelope>
```

## Ejecución

### Compilar
```bash
./gradlew clean build
```

### Ejecutar
```bash
./gradlew bootRun
```

### Ejecutar Tests
```bash
./gradlew test
```

## Prueba Manual con cURL

```bash
# Health Check
curl http://localhost:8082/api/v1/products/health

# Obtener producto desde SOAP
curl http://localhost:8082/api/v1/products/soap/PROD-001
```

## Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────┐
│                      Cliente REST                           │
└───────────────────────┬─────────────────────────────────────┘
                        │ GET /api/v1/products/soap/{id}
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              ProductController (Entry Point)                │
│                    @RestController                          │
└───────────────────────┬─────────────────────────────────────┘
                        │ Mono<ProductInfo>
                        ↓
┌─────────────────────────────────────────────────────────────┐
│            GetProductFromSoapUseCase (Domain)               │
│              @Service - Lógica de negocio                   │
└───────────────────────┬─────────────────────────────────────┘
                        │ Mono<SoapProductResponse>
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                   SoapGateway (Interface)                   │
│                   @Component - Puerto                       │
└───────────────────────┬─────────────────────────────────────┘
                        │ implementación
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              SoapClientAdapter (Infrastructure)             │
│       WebClient + Builder XML + Parser XML                  │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP POST + SOAP Envelope
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                   Servicio SOAP Externo                     │
│                  (Puerto 8081 - Mock/Servicio Real)        │
└─────────────────────────────────────────────────────────────┘
```

## Testing

El proyecto incluye tests unitarios:

- `GetProductFromSoapUseCaseTest` - Tests del caso de uso con Mockito
- `SoapClientAdapterTest` - Tests del adapter con MockWebServer

## Características

✅ **Clean Architecture**: Separación clara de concerns
✅ **Programación Reactiva**: Uso de WebFlux y Mono
✅ **Manejo de Errores**: Excepciones personalizadas y códigos HTTP apropiados
✅ **Logging**: Logs detallados en cada capa
✅ **Configuración Externa**: URL y timeout configurables
✅ **Testable**: Tests unitarios con mocks
