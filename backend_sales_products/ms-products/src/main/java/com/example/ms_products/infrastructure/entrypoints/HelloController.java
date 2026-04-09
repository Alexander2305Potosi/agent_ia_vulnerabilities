package com.example.ms_products.infrastructure.entrypoints;

import com.example.ms_products.domain.usecase.GetHelloUseCase;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/hello")
@RequiredArgsConstructor
public class HelloController {
    private final GetHelloUseCase getHelloUseCase;

    @GetMapping
    public Mono<String> hello() {
        return getHelloUseCase.execute();
    }
}
