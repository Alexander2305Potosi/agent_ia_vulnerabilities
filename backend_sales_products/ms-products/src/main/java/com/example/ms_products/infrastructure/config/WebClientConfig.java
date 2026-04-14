package com.example.ms_products.infrastructure.config;

import io.netty.channel.ChannelOption;
import io.netty.handler.timeout.ReadTimeoutHandler;
import io.netty.handler.timeout.WriteTimeoutHandler;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.web.reactive.function.client.ExchangeFilterFunction;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;
import reactor.netty.http.client.HttpClient;

import java.time.Duration;
import java.util.concurrent.TimeUnit;

/**
 * Configuración del WebClient para comunicación reactiva.
 * Incluye timeouts configurables, métricas y logging de requests/responses.
 */
@Slf4j
@Configuration
public class WebClientConfig {

    @Value("${soap.service.timeout:10000}")
    private int timeout;

    /**
     * Configura el WebClient con timeouts, buffer size y logging.
     */
    @Bean
    public WebClient webClient() {
        HttpClient httpClient = HttpClient.create()
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 5000) // 5s connect timeout
                .responseTimeout(Duration.ofMillis(timeout))
                .doOnConnected(conn -> conn
                        .addHandlerLast(new ReadTimeoutHandler(timeout, TimeUnit.MILLISECONDS))
                        .addHandlerLast(new WriteTimeoutHandler(timeout, TimeUnit.MILLISECONDS)));

        return WebClient.builder()
                .clientConnector(new ReactorClientHttpConnector(httpClient))
                .codecs(configurer -> configurer
                        .defaultCodecs()
                        .maxInMemorySize(2 * 1024 * 1024)) // 2MB buffer para respuestas grandes
                .filter(logRequest())
                .filter(logResponse())
                .build();
    }

    /**
     * Filtro para logging de requests.
     */
    private ExchangeFilterFunction logRequest() {
        return ExchangeFilterFunction.ofRequestProcessor(clientRequest -> {
            log.debug("[WebClient] Request: {} {}",
                    clientRequest.method(),
                    clientRequest.url());
            return Mono.just(clientRequest);
        });
    }

    /**
     * Filtro para logging de responses.
     */
    private ExchangeFilterFunction logResponse() {
        return ExchangeFilterFunction.ofResponseProcessor(clientResponse -> {
            log.debug("[WebClient] Response: {} - Status: {}",
                    clientResponse.request().getMethod(),
                    clientResponse.statusCode());
            return Mono.just(clientResponse);
        });
    }
}
