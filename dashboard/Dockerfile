FROM node:20-slim AS deps
WORKDIR /srv
COPY package.json package-lock.json* ./
RUN npm install

FROM node:20-slim AS build
WORKDIR /srv
COPY --from=deps /srv/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-slim
WORKDIR /srv
ENV NODE_ENV=production
COPY --from=build /srv/.next ./.next
COPY --from=build /srv/public ./public
COPY --from=build /srv/node_modules ./node_modules
COPY --from=build /srv/package.json ./package.json
COPY --from=build /srv/next.config.mjs ./next.config.mjs
EXPOSE 3000
CMD ["npm", "start"]
