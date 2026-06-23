package com.booking.system.config;

import com.booking.system.service.PropertyCacheService;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.jsontype.impl.LaissezFaireSubTypeValidator;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.redisson.Redisson;
import org.redisson.api.RedissonClient;
import org.redisson.config.Config;
import org.redisson.config.SingleServerConfig;
import org.springframework.boot.autoconfigure.data.redis.RedisProperties;
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.cache.RedisCacheConfiguration;
import org.springframework.data.redis.cache.RedisCacheManager;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.RedisSerializationContext;
import org.springframework.util.StringUtils;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

@Configuration
@EnableCaching
public class RedisCacheConfig {

    @Bean
    @RefreshScope
    public CacheManager cacheManager(
            RedisConnectionFactory redisConnectionFactory,
            ObjectMapper objectMapper,
            RoomosCacheProperties cacheProperties
    ) {
        ObjectMapper redisObjectMapper = objectMapper.copy();
        redisObjectMapper.registerModule(new JavaTimeModule());
        redisObjectMapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        redisObjectMapper.activateDefaultTyping(
                LaissezFaireSubTypeValidator.instance,
                ObjectMapper.DefaultTyping.NON_FINAL,
                JsonTypeInfo.As.PROPERTY
        );

        GenericJackson2JsonRedisSerializer serializer = new GenericJackson2JsonRedisSerializer(redisObjectMapper);
        RedisSerializationContext.SerializationPair<Object> pair =
                RedisSerializationContext.SerializationPair.fromSerializer(serializer);

        RedisCacheConfiguration defaultConfig = RedisCacheConfiguration.defaultCacheConfig()
                .disableCachingNullValues()
                .serializeValuesWith(pair)
                .entryTtl(resolve(cacheProperties.getDefaultTtl(), Duration.ofMinutes(10)));

        Map<String, RedisCacheConfiguration> cacheConfigurations = new HashMap<>();
        cacheConfigurations.put(
                PropertyCacheService.FEATURED_CACHE,
                defaultConfig.entryTtl(resolve(cacheProperties.getFeaturedPropertyTtl(), Duration.ofMinutes(10)))
        );
        cacheConfigurations.put(
                PropertyCacheService.TOP_CACHE,
                defaultConfig.entryTtl(resolve(cacheProperties.getTopPropertyTtl(), Duration.ofMinutes(5)))
        );
        cacheConfigurations.put(
                PropertyCacheService.DETAIL_CACHE,
                defaultConfig.entryTtl(resolve(cacheProperties.getPropertyDetailTtl(), Duration.ofMinutes(15)))
        );

        return RedisCacheManager.builder(redisConnectionFactory)
                .cacheDefaults(defaultConfig)
                .withInitialCacheConfigurations(cacheConfigurations)
                .transactionAware()
                .build();
    }

    @Bean(destroyMethod = "shutdown")
    @RefreshScope
    public RedissonClient redissonClient(RedisProperties redisProperties) {
        boolean sslEnabled = redisProperties.getSsl() != null && redisProperties.getSsl().isEnabled();
        String schema = sslEnabled ? "rediss://" : "redis://";

        Config config = new Config();
        config.setLazyInitialization(true);
        SingleServerConfig singleServer = config.useSingleServer()
                .setAddress(schema + redisProperties.getHost() + ":" + redisProperties.getPort())
                .setDatabase(redisProperties.getDatabase())
                .setTimeout(toMillis(redisProperties.getTimeout(), 3000))
                .setConnectTimeout(toMillis(redisProperties.getConnectTimeout(), 3000));

        if (StringUtils.hasText(redisProperties.getUsername())) {
            singleServer.setUsername(redisProperties.getUsername());
        }
        if (StringUtils.hasText(redisProperties.getPassword())) {
            singleServer.setPassword(redisProperties.getPassword());
        }

        return Redisson.create(config);
    }

    private Duration resolve(Duration candidate, Duration fallback) {
        return candidate != null ? candidate : fallback;
    }

    private int toMillis(Duration duration, int fallback) {
        if (duration == null) {
            return fallback;
        }
        long millis = duration.toMillis();
        if (millis <= 0) {
            return fallback;
        }
        return (int) Math.min(millis, Integer.MAX_VALUE);
    }
}
