FROM node:20-alpine AS builder

WORKDIR /app

ARG VITE_API_BASE_URL=http://localhost:8123/api
ARG VITE_DEPLOY_DOMAIN=http://localhost:8123/api/static
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_DEPLOY_DOMAIN=${VITE_DEPLOY_DOMAIN}

COPY package*.json /app/
RUN npm ci

COPY . /app
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
