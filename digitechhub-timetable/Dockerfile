# Build stage
FROM golang:1.24-alpine AS builder

# Install git and ca-certificates
RUN apk add --no-cache git ca-certificates

# Install swag for Swagger generation
RUN go install github.com/swaggo/swag/cmd/swag@latest

# Set working directory
WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Generate Swagger docs
RUN swag init -g main.go -d .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo .

# Final stage
FROM alpine:latest

# Install ca-certificates, curl and timezone data for health checks
RUN apk --no-cache add ca-certificates curl tzdata

# Set timezone
ENV TZ=Asia/Seoul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Create app directory
WORKDIR /root/

# Copy the binary from builder stage
COPY --from=builder /app/digitechhub-timetable .

# Expose port
EXPOSE 3002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:3002/health || exit 1

# Run the application
CMD ["./digitechhub-timetable"]
