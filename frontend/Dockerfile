# Build stage
FROM ktech4.azurecr.io/node:14 AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm config set strict-ssl false && npm install
COPY . .
RUN npm run build

# Production stage
FROM ktech4.azurecr.io/nginx:alpine
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"] 