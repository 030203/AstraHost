# Build and serve Vue frontend
ARG NODE_BUILD_IMAGE=node:18
ARG NGINX_RUNTIME_IMAGE=nginx:1.25-alpine

FROM ${NODE_BUILD_IMAGE} AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM ${NGINX_RUNTIME_IMAGE}
COPY docker/nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx","-g","daemon off;"]
