FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# VITE_API_URL resolvido em build time
ARG VITE_API_URL=https://smartagentpay.goevolux.com.br/api/v1
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/smartagent
COPY nginx.conf /etc/nginx/conf.d/smartagent.conf

EXPOSE 80