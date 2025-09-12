# Dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

# Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NODE_ENV=production
RUN npm run static

# Preview with nginx
FROM nginx:1.27-alpine AS preview
COPY --from=builder /app/out /usr/share/nginx/html
RUN <<'NGINXCONF' bash
cat >/etc/nginx/conf.d/default.conf <<'NGINX'
server {
  listen 80;
  root /usr/share/nginx/html;
  location / { try_files $uri /index.html; }
  location ~* \.(js|css|png|jpg|jpeg|gif|svg|woff2?)$ {
    add_header Cache-Control "public,max-age=31536000,immutable";
    try_files $uri =404;
  }
}
NGINX
NGINXCONF
