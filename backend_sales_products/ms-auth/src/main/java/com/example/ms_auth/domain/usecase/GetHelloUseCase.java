package com.example.ms_auth.domain.usecase;

import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

@Service
public class GetHelloUseCase {
    public Mono<String> execute() {
        return Mono.just("Hola Mundo desde MS-Auth");
    }
}
