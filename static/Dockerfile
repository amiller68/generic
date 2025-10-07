FROM nginx:alpine

# Copy nginx config
COPY static/nginx.conf /etc/nginx/conf.d/default.conf

# Copy static files
COPY static/public/ /usr/share/nginx/html/
COPY branding/assets/ /usr/share/nginx/html/assets/

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]