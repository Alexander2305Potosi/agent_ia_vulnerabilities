package com.example.ms_auth.infrastructure.entrypoints;

import com.example.ms_auth.domain.model.PersonRequest;
import com.example.ms_auth.domain.model.PersonResponse;
import com.example.ms_auth.domain.usecase.RegisterPersonUseCase;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/person")
@RequiredArgsConstructor
public class PersonController {

    private final RegisterPersonUseCase registerPersonUseCase;

    @PostMapping
    public Mono<PersonResponse> register(@RequestBody PersonRequest request) {
        return registerPersonUseCase.execute(request);
    }
}
