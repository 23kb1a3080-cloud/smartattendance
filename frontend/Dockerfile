# ─── Frontend Dockerfile ──────────────────────────────────────────────────────
# Covers: Docker, Nginx, Deployment
FROM nginx:alpine

# Copy frontend files
COPY . /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s \
  CMD wget -qO- http://localhost/index.html || exit 1

CMD ["nginx", "-g", "daemon off;"]
