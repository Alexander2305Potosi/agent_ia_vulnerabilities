package com.example.ms_sales.domain.usecase;

import org.junit.jupiter.api.Test;
import reactor.test.StepVerifier;

class GetHelloUseCaseTest {
    private final GetHelloUseCase useCase = new GetHelloUseCase();

    @Test
    void shouldReturnHelloMessage() {
        StepVerifier.create(useCase.execute())
                .expectNext("Hola Mundo desde MS-Sales")
                .verifyComplete();
    }
}
