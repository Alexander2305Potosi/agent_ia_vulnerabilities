package com.example.ms_auth.domain.model;

import lombok.Data;

@Data
public class PersonRequest {
    private String nombre;
    private String apellido;
    private String email;
    private String documento;
}
