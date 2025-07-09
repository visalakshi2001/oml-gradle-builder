# Dockerfile
FROM openjdk:11-jdk-slim
WORKDIR /workspace

# Copy Gradle wrapper and build files
COPY gradlew gradlew.bat build.gradle settings.gradle ./
COPY gradle ./gradle

# Ensure the wrapper is executable
RUN chmod +x gradlew

# Default command (overridden by overrideCommand:false)
CMD [ "bash" ]