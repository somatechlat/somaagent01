
FROM eclipse-temurin:21-jdk-alpine

WORKDIR /app

COPY target/somaagent-core-0.0.1-SNAPSHOT.jar app.jar

EXPOSE 8010

ENTRYPOINT ["java", "-jar", "app.jar"]
