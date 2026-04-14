package com.example.ms_auth.domain.model;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class PersonResponse {
    private String codigo;
    private String mensaje;
    private PersonRequest datos;
}
