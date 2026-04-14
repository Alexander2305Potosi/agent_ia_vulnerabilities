package com.example.ms_products.domain.gateway;

import com.example.ms_products.domain.model.SoapProductRequest;
import com.example.ms_products.domain.model.SoapProductResponse;
import reactor.core.publisher.Mono;

public interface SoapGateway {
    Mono<SoapProductResponse> callSoapService(SoapProductRequest request);
}
