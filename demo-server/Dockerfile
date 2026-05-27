FROM golang:1.26-alpine AS build
WORKDIR /src
COPY go.mod main.go ./
RUN go build -o server .

FROM alpine:3.21
RUN adduser -D -H appuser
USER appuser
COPY --from=build /src/server /server
ENV DATA_DIR=/data
EXPOSE 8080
ENTRYPOINT ["/server"]
