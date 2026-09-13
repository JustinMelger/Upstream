FROM node:22-alpine AS ui-build

WORKDIR /ui

COPY frontend/react/package*.json ./
RUN npm ci

COPY frontend/react/ ./
RUN npm run build

FROM nginx:1.28-alpine AS runtime

COPY frontend/react/nginx-main.conf /etc/nginx/nginx.conf
COPY frontend/react/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=ui-build /ui/dist /usr/share/nginx/html

USER nginx
EXPOSE 8080

ENTRYPOINT []
CMD ["nginx", "-g", "daemon off;"]
