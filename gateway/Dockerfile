ARG MAVEN_BUILD_IMAGE=maven:3.9-eclipse-temurin-17
ARG JAVA_RUNTIME_IMAGE=eclipse-temurin:17-jre

FROM ${MAVEN_BUILD_IMAGE} AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn -B -DskipTests package

FROM ${JAVA_RUNTIME_IMAGE}
WORKDIR /app
COPY --from=build /app/target/*.jar /app/app.jar
EXPOSE 8088
ENTRYPOINT ["java","-jar","/app/app.jar"]
