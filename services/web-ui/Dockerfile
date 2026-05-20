FROM node:22-alpine AS builder
WORKDIR /app
COPY services/web-ui/package.json services/web-ui/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY services/web-ui/ .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY services/web-ui/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80