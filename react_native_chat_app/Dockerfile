FROM node:22-alpine AS build

WORKDIR /app

ARG EXPO_PUBLIC_API_URL
ENV EXPO_PUBLIC_API_URL=${EXPO_PUBLIC_API_URL}

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run export:web

FROM node:22-alpine

ENV NODE_ENV=production
ENV PORT=8080

WORKDIR /app

COPY --from=build /app/dist ./dist
COPY server.js ./server.js

CMD ["node", "server.js"]
