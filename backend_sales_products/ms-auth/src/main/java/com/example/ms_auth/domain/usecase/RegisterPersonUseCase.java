package com.example.ms_auth.domain.usecase;

import com.example.ms_auth.domain.model.PersonRequest;
import com.example.ms_auth.domain.model.PersonResponse;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Service
public class RegisterPersonUseCase {

    public Mono<PersonResponse> execute(PersonRequest request) {
        return Mono.just(
            PersonResponse.builder()
                .codigo("200")
                .mensaje("Persona registrada exitosamente")
                .datos(request)
                .build()
        );
    }
}
