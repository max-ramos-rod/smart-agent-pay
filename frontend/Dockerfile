FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

ARG VITE_API_URL=https://smartagentpay.goevolux.com.br/api/v1
ARG VITE_SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
ARG VITE_USDC_MINT=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v
ARG VITE_SOLANA_NETWORK=mainnet-beta

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_SOLANA_RPC_URL=$VITE_SOLANA_RPC_URL
ENV VITE_USDC_MINT=$VITE_USDC_MINT
ENV VITE_SOLANA_NETWORK=$VITE_SOLANA_NETWORK

RUN npm run build

FROM nginx:alpine

RUN rm -f /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=build /app/dist /usr/share/nginx/smartagent