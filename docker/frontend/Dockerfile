FROM nginx:alpine

# Copy frontend files
COPY frontend/static /usr/share/nginx/html/static
COPY frontend/templates /usr/share/nginx/html/templates

# Copy nginx configuration
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]