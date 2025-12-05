FROM node:18-alpine
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --silent
COPY frontend/ .
CMD ["npm", "start"]
