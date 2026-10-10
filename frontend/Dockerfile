
# Build the React application.
FROM node:22-alpine AS build

WORKDIR /frontend

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Serve the built application using Nginx.
FROM nginx:1.28-alpine

RUN apk add --no-cache gettext

COPY nginx.conf.template /etc/nginx/templates/default.conf.template

COPY --from=build /frontend/dist /usr/share/nginx/html

EXPOSE 80

# Inject the API key into Nginx at startup, not into browser code.
CMD ["/bin/sh", "-c", "envsubst '${API_KEY}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && exec nginx -g 'daemon off;'"]
